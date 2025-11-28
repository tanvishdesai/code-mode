import json
import random
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np
from track_3_implementation import SecurityKernel, CapabilityToken, ConstraintEngine, USERS, SCENARIOS, TOOLS as MOCK_TOOLS

# ==========================================
# CONFIGURATION
# ==========================================
DATASET_PATH = "/kaggle/input/mcp-tools-v1/mcp_dataset_enhanced.json"
# Fallback for local testing
if not os.path.exists(DATASET_PATH):
    DATASET_PATH = "track-1 data/mcp_dataset_enhanced.json"

NUM_REQUESTS = 100
RANDOM_SEED = 42

# ==========================================
# PART 1: QUALITATIVE CASE STUDY (Alice & Bob)
# ==========================================
def run_qualitative_study():
    print("\n" + "="*50)
    print("PART 1: QUALITATIVE CASE STUDY (Alice & Bob)")
    print("Demonstrating fine-grained access control on specific scenarios.")
    print("="*50)
    
    kernel = SecurityKernel()
    results = []
    
    # Use the pre-defined scenarios from implementation file
    for scenario in SCENARIOS:
        user_id = scenario['user']
        user = USERS[user_id]
        query = scenario['query']
        tool_name = scenario['expected_tool']
        args = scenario['expected_args']
        
        print(f"\nScenario #{scenario['id']}: {query}")
        print(f"   User: {user_id} | Tool: {tool_name}")
        
        allowed, reason, details = kernel.enforce(tool_name, args, user['tokens'], {"user_id": user_id})
        
        status_icon = "✅" if allowed else "⛔"
        print(f"   Decision: {status_icon} {reason}")
        if not allowed:
            print(f"   Details: {details}")
            
        results.append({
            "Scenario ID": scenario['id'],
            "User": user_id,
            "Decision": "Allowed" if allowed else "Blocked",
            "Reason": reason
        })
        
    df = pd.DataFrame(results)
    print("\nSummary of Case Study:")
    print(df)
    return df

# ==========================================
# PART 2: QUANTITATIVE STRESS TEST
# ==========================================
def load_tools(path):
    print(f"\nLoading tools from {path}...")
    tools = []
    try:
        with open(path, 'r') as f:
            data = json.load(f)
            for server in data.get('servers', []):
                server_name = server.get('server_name', 'unknown')
                for tool in server.get('tools', []):
                    tool['full_name'] = f"{server_name}.{tool['name']}"
                    tools.append(tool)
    except FileNotFoundError:
        print("⚠️ Dataset not found. Using mock tools.")
        tools = MOCK_TOOLS
        for t in tools: t['full_name'] = t['name']
            
    return tools

def generate_users(tools, count=10):
    """Generate mock users with random access tokens."""
    departments = ["Sales", "Engineering", "HR", "Legal"]
    users = []
    
    for i in range(count):
        dept = random.choice(departments)
        user_id = f"user_{i}_{dept}"
        
        # Grant access to 3-5 random tools
        tokens = []
        # Pick 5 random tools this user is "allowed" to use
        allowed_tools = random.sample(tools, k=min(len(tools), 5))
        
        for tool in allowed_tools:
            # 50% chance of exact match, 50% wildcard
            if random.random() > 0.5:
                pattern = tool['full_name']
            else:
                pattern = tool['full_name'].split('.')[0] + ".*"
            
            # Add constraints
            constraints = []
            if random.random() > 0.5:
                constraints.append(f"department={dept}")
                
            tokens.append(CapabilityToken(pattern, ["read", "write"], constraints))
            
        users.append({
            "id": user_id,
            "dept": dept,
            "tokens": tokens,
            "known_tools": allowed_tools # Helper to generate valid traffic
        })
    return users

def generate_traffic(users, all_tools, count=100):
    """
    Generate a mix of traffic:
    - 60% Valid Requests (Authorized tool + Correct args)
    - 20% Unauthorized Tool (Tool user doesn't have)
    - 20% Constraint Violation (Authorized tool + Wrong args)
    """
    traffic = []
    
    for _ in range(count):
        user = random.choice(users)
        rand = random.random()
        
        if rand < 0.6:
            # === VALID REQUEST ===
            if not user['known_tools']: continue
            tool = random.choice(user['known_tools'])
            args = {"department": user['dept'], "owner": user['id']}
            expected = "Allowed"
            
        elif rand < 0.8:
            # === UNAUTHORIZED TOOL ===
            # Pick a tool NOT in their known list
            unknown_tools = [t for t in all_tools if t not in user['known_tools']]
            if not unknown_tools: continue
            tool = random.choice(unknown_tools)
            args = {"department": user['dept']}
            expected = "NoCapabilityToken"
            
        else:
            # === CONSTRAINT VIOLATION ===
            if not user['known_tools']: continue
            tool = random.choice(user['known_tools'])
            # Intentionally wrong department
            wrong_depts = [d for d in ["Sales", "Engineering", "HR"] if d != user['dept']]
            args = {"department": random.choice(wrong_depts), "owner": user['id']}
            expected = "ConstraintViolation" # Likely, unless token has no constraints
            
        traffic.append({
            "user": user,
            "tool": tool,
            "args": args,
            "expected_type": expected
        })
    return traffic

def run_quantitative_study():
    print("\n" + "="*50)
    print("PART 2: QUANTITATIVE STRESS TEST")
    print(f"Simulating {NUM_REQUESTS} requests across large toolset.")
    print("="*50)
    
    random.seed(RANDOM_SEED)
    tools = load_tools(DATASET_PATH)
    users = generate_users(tools, count=10)
    traffic = generate_traffic(users, tools, NUM_REQUESTS)
    
    kernel = SecurityKernel()
    results = []
    
    print(f"Processing {len(traffic)} requests...")
    
    for i, req in enumerate(traffic):
        user = req['user']
        tool = req['tool']
        args = req['args']
        
        allowed, reason, _ = kernel.enforce(
            tool['full_name'], 
            args, 
            user['tokens'], 
            {"user_id": user['id']}
        )
        
        results.append({
            "Request ID": i,
            "User Dept": user['dept'],
            "Tool": tool['full_name'],
            "Input Type": req['expected_type'],
            "Outcome": reason,
            "Allowed": allowed
        })
        
    df = pd.DataFrame(results)
    
    # === METRICS ===
    print("\n=== 📊 EXPERIMENT METRICS ===")
    
    # 1. Confusion Matrix-like stats
    # True Positive = Allowed Valid Request
    # True Negative = Blocked Invalid Request
    # False Positive = Blocked Valid Request (Over-restrictive)
    # False Negative = Allowed Invalid Request (Security Hole)
    
    # Note: In this simulation, 'Input Type' is our ground truth intent.
    # However, 'ConstraintViolation' input might be allowed if the random token didn't actually have a constraint.
    # So we look at distribution.
    
    outcome_counts = df['Outcome'].value_counts()
    print("\nOutcome Distribution:")
    print(outcome_counts)
    
    # 2. Violation Prevention Rate
    # How many "Unauthorized" or "Constraint" inputs were actually blocked?
    bad_inputs = df[df['Input Type'].isin(['NoCapabilityToken', 'ConstraintViolation'])]
    blocked_bad = bad_inputs[bad_inputs['Allowed'] == False]
    prevention_rate = len(blocked_bad) / len(bad_inputs) * 100 if len(bad_inputs) > 0 else 0
    print(f"\nViolation Prevention Rate: {prevention_rate:.1f}%")
    
    # 3. False Positive Rate (Valid inputs that were blocked)
    # This shouldn't happen in our logic unless we messed up generation
    valid_inputs = df[df['Input Type'] == 'Allowed']
    blocked_valid = valid_inputs[valid_inputs['Allowed'] == False]
    fp_rate = len(blocked_valid) / len(valid_inputs) * 100 if len(valid_inputs) > 0 else 0
    print(f"False Positive Rate: {fp_rate:.1f}%")

    # === PLOTS ===
    sns.set_theme(style="whitegrid")
    
    # Plot 1: Outcomes by Intended Input Type
    plt.figure(figsize=(10, 6))
    sns.countplot(data=df, x='Input Type', hue='Outcome', palette='viridis')
    plt.title("Security Enforcement Decisions by Input Type")
    plt.xlabel("Intended Request Type")
    plt.ylabel("Count")
    plt.legend(title="Enforcement Outcome")
    plt.tight_layout()
    plt.savefig("experiment_outcomes.png")
    print("✅ Saved plot: experiment_outcomes.png")
    
    # Plot 2: Overall Security Posture
    plt.figure(figsize=(6, 6))
    df['Outcome'].value_counts().plot(kind='pie', autopct='%1.1f%%', colors=['#2ecc71', '#e74c3c', '#f1c40f'])
    plt.title("Overall Traffic Disposition")
    plt.ylabel("")
    plt.tight_layout()
    plt.savefig("experiment_distribution.png")
    print("✅ Saved plot: experiment_distribution.png")

    df.to_csv("track_3_full_results.csv", index=False)
    print("📝 Saved full results to track_3_full_results.csv")

if __name__ == "__main__":
    run_qualitative_study()
    run_quantitative_study()
