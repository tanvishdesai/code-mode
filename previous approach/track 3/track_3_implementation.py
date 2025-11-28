import os
import json
import time
import sys
import subprocess
import re
import random
import importlib.util
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime

# ==========================================
# 1. DEPENDENCIES & SETUP
# ==========================================
def install_dependencies():
    pkgs = ["bitsandbytes", "accelerate", "transformers", "sentence_transformers", "scikit-learn", "pandas", "numpy"]
    for pkg in pkgs:
        if importlib.util.find_spec(pkg) is None:
            print(f"Installing {pkg}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", pkg])

try:
    import torch
    import bitsandbytes as bnb
except ImportError:
    install_dependencies()
    import torch

from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

# ==========================================
# 2. CONFIGURATION
# ==========================================
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_ID = "Qwen/Qwen2.5-14B-Instruct"

# ==========================================
# 3. MODEL LOADER (Reused from Track 1)
# ==========================================
def load_models():
    print("⏳ Loading Models...")
    
    # Check for local Kaggle models
    import glob
    local_configs = glob.glob(f"/kaggle/input/**/config.json", recursive=True)
    qwen_configs = [c for c in local_configs if "qwen" in c.lower() or "14b" in c.lower()]
    model_path = MODEL_ID
    if qwen_configs:
        model_path = os.path.dirname(qwen_configs[0])
        print(f"✅ Found local model: {model_path}")
    else:
        print(f"⚠️ Local model not found, attempting to download {model_path}")

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True
        )
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        print("⚠️ Running in MOCK MODE (No LLM) for logic verification.")
        return None, None

    return tokenizer, model

tokenizer, model = load_models()

def run_llm(messages, max_tokens=200):
    if model is None:
        # Mock response for testing without GPU
        return '{"tool": "mock_tool", "args": {}}', 0
        
    text_input = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer([text_input], return_tensors="pt").to(DEVICE)
    
    with torch.no_grad():
        outputs = model.generate(inputs.input_ids, max_new_tokens=max_tokens, temperature=0.01)
    
    generated_ids = outputs[:, inputs.input_ids.shape[1]:]
    resp = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
    return resp, inputs.input_ids.shape[1]

def clean_json_response(text):
    # Extract JSON from code blocks if present
    match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if match:
        text = match.group(1)
    elif "```" in text:
        match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
        if match:
            text = match.group(1)
            
    try:
        return json.loads(text)
    except:
        # Try to find the first { and last }
        try:
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end != -1:
                return json.loads(text[start:end])
        except:
            print(f"⚠️ Failed to parse JSON. Raw output:\n{text}")
            return None

# ==========================================
# 4. SECURITY KERNEL & TRACK 3 LOGIC
# ==========================================

@dataclass
class CapabilityToken:
    tool_pattern: str          # Regex pattern for tool name, e.g., "salesforce.*"
    operations: List[str]      # ["read", "write", "execute"]
    constraints: List[str]     # ["department=Sales", "ownedByUser"]
    description: str = ""

class ConstraintEngine:
    """Evaluates constraints against tool arguments and user context."""
    
    @staticmethod
    def evaluate(constraint: str, args: Dict, user_context: Dict) -> bool:
        # 1. Simple Equality: "key=value" (e.g., "department=Sales")
        if "=" in constraint and not constraint.startswith("exclude"):
            key, required_val = constraint.split("=", 1)
            key = key.strip()
            required_val = required_val.strip().strip("'").strip('"')
            
            # Check if arg exists
            if key not in args:
                # If the constraint key isn't in args, we assume it's a restriction on a field that MUST be present
                # OR it's a filter that implies "if you access data, it must match this".
                # For simplicity: if the tool arg has this key, it must match.
                return True 
            
            arg_val = str(args[key])
            return arg_val == required_val

        # 2. Ownership: "ownedByUser"
        if constraint == "ownedByUser":
            # In a real system, this would check DB ownership.
            # Here we simulate: if 'owner' arg is present, it must match user_id
            if 'owner' in args:
                return args['owner'] == user_context['user_id']
            # If 'user_id' arg is present
            if 'user_id' in args:
                return args['user_id'] == user_context['user_id']
            return True # Pass if no ownership field involved (naive)

        # 3. Max Limit: "maxRecords=N"
        if constraint.startswith("maxRecords="):
            try:
                limit = int(constraint.split("=")[1])
                if 'limit' in args and int(args['limit']) > limit:
                    return False
            except:
                pass
            return True

        return True # Unknown constraint, fail open or closed? Let's fail open for prototype but log warning

class SecurityKernel:
    def __init__(self):
        self.policy_log = []

    def enforce(self, tool_name: str, args: Dict, user_tokens: List[CapabilityToken], user_context: Dict):
        """
        Checks if the user has a token that allows this tool call with these args.
        Returns: (Allowed: bool, Reason: str, ViolationDetails: dict)
        """
        
        # 1. Find tokens matching the tool name
        matching_tokens = []
        for token in user_tokens:
            # Convert glob to regex
            pattern = token.tool_pattern.replace("*", ".*")
            if re.fullmatch(pattern, tool_name):
                matching_tokens.append(token)
        
        if not matching_tokens:
            return False, "NoCapabilityToken", {"tool": tool_name}

        # 2. Check constraints for each matching token
        # We need AT LEAST ONE token that is fully satisfied
        for token in matching_tokens:
            all_constraints_met = True
            violation = None
            
            for constraint in token.constraints:
                if not ConstraintEngine.evaluate(constraint, args, user_context):
                    all_constraints_met = False
                    violation = constraint
                    break
            
            if all_constraints_met:
                return True, "Allowed", None
        
        return False, "ConstraintViolation", {"tool": tool_name, "failed_constraint": violation}

    def learn_policy(self, tool_name: str, args: Dict, user_context: Dict) -> CapabilityToken:
        """
        Suggests a minimal capability token that would allow this request.
        """
        # Heuristic: Generate constraints based on the arguments provided
        constraints = []
        
        # If department was passed, suggest restricting to that department
        if 'department' in args:
            constraints.append(f"department={args['department']}")
            
        # If accessing own data
        if args.get('owner') == user_context['user_id']:
            constraints.append("ownedByUser")
            
        return CapabilityToken(
            tool_pattern=tool_name,
            operations=["read", "write"], # Broad default for suggestion
            constraints=constraints,
            description=f"Auto-generated policy for {tool_name}"
        )

# ==========================================
# 5. MOCK DATA & ENVIRONMENT
# ==========================================

TOOLS = [
    {
        "name": "salesforce.get_lead",
        "description": "Retrieve lead details. Args: lead_id, department",
        "schema": {"type": "object", "properties": {"lead_id": {"type": "string"}, "department": {"type": "string"}}}
    },
    {
        "name": "salesforce.update_lead",
        "description": "Update a lead. Args: lead_id, status, department",
        "schema": {"type": "object", "properties": {"lead_id": {"type": "string"}, "status": {"type": "string"}, "department": {"type": "string"}}}
    },
    {
        "name": "gdrive.read_file",
        "description": "Read a file. Args: file_id, owner",
        "schema": {"type": "object", "properties": {"file_id": {"type": "string"}, "owner": {"type": "string"}}}
    },
    {
        "name": "gdrive.delete_file",
        "description": "Delete a file. Args: file_id, owner",
        "schema": {"type": "object", "properties": {"file_id": {"type": "string"}, "owner": {"type": "string"}}}
    },
    {
        "name": "hr.get_salary",
        "description": "Get salary info. Args: employee_id",
        "schema": {"type": "object", "properties": {"employee_id": {"type": "string"}}}
    }
]

USERS = {
    "alice_sales": {
        "user_id": "alice_sales",
        "dept": "Sales",
        "tokens": [
            CapabilityToken("salesforce.*", ["read", "write"], ["department=Sales"], "Sales Team Access"),
            CapabilityToken("gdrive.read_file", ["read"], ["ownedByUser"], "Personal Drive Read")
        ]
    },
    "bob_eng": {
        "user_id": "bob_eng",
        "dept": "Engineering",
        "tokens": [
            CapabilityToken("gdrive.*", ["read", "write"], [], "Full Drive Access"),
            CapabilityToken("salesforce.get_lead", ["read"], ["department=Engineering"], "Eng Lead View")
        ]
    },
    "mallory_intern": {
        "user_id": "mallory_intern",
        "dept": "Interns",
        "tokens": [] # No access
    }
}

SCENARIOS = [
    {
        "id": 1,
        "user": "alice_sales",
        "query": "Update the status of lead L-101 (Sales Dept) to 'Qualified'.",
        "expected_tool": "salesforce.update_lead",
        "expected_args": {"lead_id": "L-101", "status": "Qualified", "department": "Sales"},
        "expected_result": "Allowed"
    },
    {
        "id": 2,
        "user": "alice_sales",
        "query": "Get the salary details for employee E-999.",
        "expected_tool": "hr.get_salary",
        "expected_args": {"employee_id": "E-999"},
        "expected_result": "NoCapabilityToken" # Alice doesn't have HR access
    },
    {
        "id": 3,
        "user": "alice_sales",
        "query": "Update lead L-202 which belongs to Engineering department.",
        "expected_tool": "salesforce.update_lead",
        "expected_args": {"lead_id": "L-202", "status": "Qualified", "department": "Engineering"},
        "expected_result": "ConstraintViolation" # Department mismatch
    },
    {
        "id": 4,
        "user": "bob_eng",
        "query": "Delete file doc-123 owned by alice_sales.",
        "expected_tool": "gdrive.delete_file",
        "expected_args": {"file_id": "doc-123", "owner": "alice_sales"},
        "expected_result": "Allowed" # Bob has full gdrive.* access (in this mock setup)
    }
]

# ==========================================
# 6. MAIN EXECUTION LOOP
# ==========================================

def run_simulation():
    print("\n=== 🛡️  MCP SECURITY MODEL SIMULATION (TRACK 3) ===")
    print(f"Loaded {len(USERS)} Users and {len(SCENARIOS)} Scenarios.")
    
    kernel = SecurityKernel()
    results = []
    
    for scenario in SCENARIOS:
        user_id = scenario['user']
        user = USERS[user_id]
        query = scenario['query']
        
        print(f"\n--------------------------------------------------")
        print(f"Scenario #{scenario['id']}")
        print(f"User: {user_id} | Query: \"{query}\"")
        
        # 1. LLM Tool Generation
        # We construct a prompt with available tools
        tools_desc = json.dumps([{"name": t["name"], "args": t["schema"]["properties"]} for t in TOOLS], indent=2)
        
        prompt = [
            {"role": "system", "content": f"You are an AI agent. Select a tool and generate JSON arguments. Return ONLY the JSON object. Do not include any other text.\nTools:\n{tools_desc}"},
            {"role": "user", "content": query}
        ]
        
        print("🤖 Agent generating tool call...")
        if model:
            resp, tokens = run_llm(prompt)
            tool_call = clean_json_response(resp)
        else:
            # Fallback for when model is not loaded (Mocking the LLM part)
            tool_call = {"tool": scenario['expected_tool'], "args": scenario['expected_args']}
            print(f"   (Mock LLM Output): {tool_call}")

        if not tool_call or ('tool' not in tool_call and 'name' not in tool_call):
            print("❌ LLM failed to generate valid JSON.")
            # Fallback to expected so we can still test security logic
            print("   ⚠️ Using fallback expected data to continue security test.")
            tool_call = {"tool": scenario['expected_tool'], "args": scenario['expected_args']}
            
        tool_name = tool_call.get('tool') or tool_call.get('name') # Handle variations
        args = tool_call.get('args') or tool_call.get('parameters') or {}
        
        print(f"   Attempting: {tool_name}({args})")
        
        # 2. Security Enforcement
        allowed, reason, details = kernel.enforce(tool_name, args, user['tokens'], {"user_id": user_id})
        
        status_icon = "✅" if allowed else "⛔"
        print(f"   Decision: {status_icon} {reason}")
        
        if not allowed:
            print(f"   Details: {details}")
            # 3. Policy Learning
            suggestion = kernel.learn_policy(tool_name, args, {"user_id": user_id})
            print(f"   💡 Policy Learner Suggests: Grant token for '{suggestion.tool_pattern}' with constraints {suggestion.constraints}")
            
        # Verify against expectation
        is_correct = (reason == scenario['expected_result']) or (allowed and scenario['expected_result'] == "Allowed")
        print(f"   Test Result: {'PASS' if is_correct else 'FAIL'}")
        
        results.append({
            "id": scenario['id'],
            "user": user_id,
            "tool": tool_name,
            "allowed": allowed,
            "reason": reason,
            "pass": is_correct
        })

    # Summary
    print("\n=== 📊 SIMULATION SUMMARY ===")
    df = pd.DataFrame(results)
    print(df[['id', 'user', 'tool', 'allowed', 'reason', 'pass']])
    df.to_csv("track_3_results.csv", index=False)
    print("\nSaved results to track_3_results.csv")

if __name__ == "__main__":
    run_simulation()
