import ast
import re
import json
import sys
import subprocess
import traceback
import importlib.util
import os
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass

# ==========================================
# 1. DEPENDENCIES & MODEL SETUP
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

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_ID = "Qwen/Qwen2.5-14B-Instruct"

def load_models():
    print("⏳ Loading Models for Track 2...")
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
        return tokenizer, model
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        print("⚠️ Running in MOCK MODE (No LLM).")
        return None, None

# Global Model Instances
tokenizer, model = load_models()

def run_llm(messages, max_tokens=200):
    if model is None:
        return None
        
    text_input = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer([text_input], return_tensors="pt").to(DEVICE)
    
    with torch.no_grad():
        outputs = model.generate(inputs.input_ids, max_new_tokens=max_tokens, temperature=0.01)
    
    generated_ids = outputs[:, inputs.input_ids.shape[1]:]
    resp = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
    return resp

# ==========================================
# 2. CONSTRAINT SYSTEM
# ==========================================
@dataclass
class ValidationResult:
    valid: bool
    error: Optional[str] = None
    fix_suggestion: Optional[str] = None

class SchemaTranslator:
    """Translates JSON Schema to executable Python constraints."""
    
    @staticmethod
    def validate_type(value: Any, expected_type: str) -> bool:
        if expected_type == "string": return isinstance(value, str)
        if expected_type == "integer": return isinstance(value, int)
        if expected_type == "number": return isinstance(value, (int, float))
        if expected_type == "boolean": return isinstance(value, bool)
        if expected_type == "array": return isinstance(value, list)
        if expected_type == "object": return isinstance(value, dict)
        return True # Unknown type, pass

    @staticmethod
    def validate_args(tool_name: str, args: Dict[str, Any], schema: Dict[str, Any]) -> ValidationResult:
        parameters = schema.get("parameters", {})
        props = parameters.get("properties", {})
        required = parameters.get("required", [])
        
        # 1. Check Required Fields
        for field in required:
            if field not in args:
                return ValidationResult(False, f"Missing required argument: '{field}'", f"Add '{field}' to arguments")
        
        # 2. Check Field Constraints
        for key, value in args.items():
            if key not in props: continue
                
            field_schema = props[key]
            
            # Type Check
            if "type" in field_schema:
                type_def = field_schema["type"]
                if "int" in type_def.lower(): py_type = "integer"
                elif "str" in type_def.lower(): py_type = "string"
                elif "bool" in type_def.lower(): py_type = "boolean"
                elif "list" in type_def.lower(): py_type = "array"
                elif "dict" in type_def.lower(): py_type = "object"
                else: py_type = "unknown"
                
                if py_type != "unknown" and not SchemaTranslator.validate_type(value, py_type):
                    return ValidationResult(False, f"Type mismatch for '{key}': expected {py_type}, got {type(value).__name__}", f"Cast '{key}' to {py_type}")

            # Pattern Check (Regex)
            if "pattern" in field_schema and isinstance(value, str):
                if not re.match(field_schema["pattern"], value):
                    return ValidationResult(False, f"Value for '{key}' does not match pattern {field_schema['pattern']}", f"Format '{key}' correctly")
                    
        return ValidationResult(True)

# ==========================================
# 3. STATIC ANALYZER
# ==========================================
class StaticAnalyzer(ast.NodeVisitor):
    def __init__(self, available_tools: Dict[str, Any]):
        self.available_tools = available_tools
        self.errors = []
        
    def visit_Call(self, node):
        tool_name = None
        if isinstance(node.func, ast.Name):
            tool_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            tool_name = node.func.attr
            
        if tool_name:
            matched_tool = None
            for t_name in self.available_tools:
                if t_name.endswith(tool_name) or t_name == tool_name:
                    matched_tool = t_name
                    break
            
            if not matched_tool and tool_name not in dir(__builtins__):
                self.errors.append(f"Hallucination: Tool '{tool_name}' does not exist.")
        
        self.generic_visit(node)

    def analyze(self, code: str) -> List[str]:
        try:
            tree = ast.parse(code)
            self.visit(tree)
        except SyntaxError as e:
            return [f"Syntax Error: {e}"]
        return self.errors

# ==========================================
# 4. RUNTIME GUARD & REPAIR
# ==========================================
class RuntimeGuard:
    def __init__(self, tools_db: Dict[str, Any]):
        self.tools_db = tools_db
        
    def execute_safe(self, tool_name: str, args: Dict[str, Any]) -> Tuple[bool, Any]:
        if tool_name not in self.tools_db:
            return False, f"Hallucination: Tool '{tool_name}' not found."
            
        schema = self.tools_db[tool_name]
        validation = SchemaTranslator.validate_args(tool_name, args, schema)
        if not validation.valid:
            return False, f"SchemaViolation: {validation.error}"
            
        return True, f"Executed {tool_name} successfully."

class SelfRepairAgent:
    """
    Uses the LLM to fix code based on error messages.
    """
    @staticmethod
    def repair(code_repr: str, error_msg: str) -> str:
        # If no model, fall back to heuristic (Mock Mode)
        if model is None:
            if "Missing required argument: 'department'" in error_msg:
                return code_repr.replace("}", ", 'department': 'Sales'}")
            if "Type mismatch for 'age'" in error_msg:
                return code_repr.replace("'30'", "30")
            if "Hallucination: Tool 'get_users'" in error_msg:
                return code_repr.replace("get_users", "list_users")
            return code_repr

        # Real LLM Repair
        prompt = [
            {"role": "system", "content": "You are an expert coding assistant. Fix the code based on the error message. Return ONLY the corrected code string. Do not include markdown formatting or explanations."},
            {"role": "user", "content": f"Code:\n{code_repr}\n\nError:\n{error_msg}\n\nCorrected Code:"}
        ]
        
        try:
            response = run_llm(prompt, max_tokens=100)
            # Clean response
            cleaned = response.strip().replace("```python", "").replace("```", "").strip()
            return cleaned
        except Exception as e:
            print(f"LLM Repair failed: {e}")
            return code_repr

# ==========================================
# 5. MAIN PIPELINE
# ==========================================
class VerificationPipeline:
    def __init__(self, tools_list: List[Dict]):
        self.tools_map = {t['name']: t for t in tools_list}
        self.static_analyzer = StaticAnalyzer(self.tools_map)
        self.runtime_guard = RuntimeGuard(self.tools_map)
        
    def verify_code(self, code: str) -> List[str]:
        return self.static_analyzer.analyze(code)
        
    def execute_with_guard(self, tool_name: str, args: Dict) -> Dict:
        success, result = self.runtime_guard.execute_safe(tool_name, args)
        return {"success": success, "message": result}

if __name__ == "__main__":
    # Simple test
    tools = [{"name": "test_tool", "parameters": {"required": ["x"], "properties": {"x": {"type": "int"}}}}]
    pipeline = VerificationPipeline(tools)
    print(pipeline.execute_with_guard("test_tool", {"x": "wrong"}))
