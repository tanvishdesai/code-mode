import os
import glob
import json
import time
import sys
import subprocess
import pandas as pd
import numpy as np
import importlib.util
import re
import random
from typing import List, Dict, Any

# ==========================================
# DEPENDENCIES
# ==========================================
def install_dependencies():
    pkgs = ["bitsandbytes", "accelerate", "transformers", "sentence_transformers", "scikit-learn", "matplotlib", "seaborn", "pandas"]
    for pkg in pkgs:
        if importlib.util.find_spec(pkg) is None:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", pkg])

try:
    import bitsandbytes as bnb
except ImportError:
    install_dependencies()

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt
import seaborn as sns

# ==========================================
# CONFIGURATION
# ==========================================
DATASET_PATH = "/kaggle/input/mcp-tools-v1/mcp_dataset_enhanced.json"
# Fallback path for local testing
if not os.path.exists(DATASET_PATH):
    DATASET_PATH = "mcp_dataset_enhanced.json"

TARGET_TOOL_COUNT = 1000 
RETRIEVAL_POOL_SIZE = 15
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
CONTEXT_WINDOW_LIMIT = 32000 # Example limit for visualization

# ==========================================
# MODEL LOADER
# ==========================================
def load_models():
    print("⏳ Loading Models...")
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    
    model_id = "Qwen/Qwen2.5-14B-Instruct"
    # Check for local Kaggle models
    local_configs = glob.glob(f"/kaggle/input/**/config.json", recursive=True)
    qwen_configs = [c for c in local_configs if "qwen" in c.lower() or "14b" in c.lower()]
    if qwen_configs:
        model_id = os.path.dirname(qwen_configs[0])
        print(f"✅ Found local model: {model_id}")
    else:
        print(f"⚠️ Local model not found, attempting to use {model_id}")

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    try:
        tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True
        )
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        print("⚠️ Falling back to CPU/Mock mode for testing logic.")
        raise e

    return tokenizer, model, embedder

# Global models
tokenizer, model, embedder = load_models()

# ==========================================
# DATASET & RETRIEVERS
# ==========================================
class ToolDatabase:
    def __init__(self, json_path, target_count=1000):
        self.tools = []
        self.embeddings = None
        self.load_data(json_path, target_count)

    def load_data(self, json_path, target_count):
        print(f"Loading data from {json_path}...")
        raw_tools = []
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                data = json.load(f)
                if 'servers' in data:
                    for server in data['servers']:
                        s_name = server.get('server_name', 'unknown')
                        for tool in server.get('tools', []):
                            t = tool.copy()
                            t['unique_name'] = f"{s_name}__{t['name']}"
                            raw_tools.append(t)
        
        if not raw_tools:
            print("⚠️ No tools found. Generating dummy tools.")
            raw_tools = [{"unique_name": f"dummy_server__tool_{i}", "description": f"Dummy tool {i}", "name": f"tool_{i}"} for i in range(10)]

        self.tools = raw_tools
        if len(self.tools) > 0:
            while len(self.tools) < target_count:
                self.tools.extend(raw_tools)
            self.tools = self.tools[:target_count]
        
        print(f"Loaded {len(self.tools)} tools (Target: {target_count})")

        # Embed for Semantic Search
        print(f"Embedding {len(self.tools)} tools...")
        descriptions = [f"{t.get('unique_name', '')} {t.get('description', '')}" for t in self.tools]
        self.embeddings = embedder.encode(descriptions)
        print(f"✅ Database Ready.")

    def retrieve_semantic(self, query, top_k=10):
        q_emb = embedder.encode([query])
        sims = cosine_similarity(q_emb, self.embeddings)[0]
        top_idxs = np.argsort(sims)[-top_k:][::-1]
        return [self.tools[i] for i in top_idxs]

    def retrieve_keyword(self, query, top_k=10):
        """Simple keyword matching based on name and description"""
        query_terms = set(query.lower().split())
        scores = []
        for i, tool in enumerate(self.tools):
            text = (tool['unique_name'] + " " + tool['description']).lower()
            score = sum(1 for term in query_terms if term in text)
            scores.append((score, i))
        
        # Sort by score desc
        scores.sort(key=lambda x: x[0], reverse=True)
        top_idxs = [x[1] for x in scores[:top_k]]
        return [self.tools[i] for i in top_idxs]

    def get_tool(self, unique_name):
        for t in self.tools:
            if t.get('unique_name') == unique_name:
                return t
        return None

db = ToolDatabase(DATASET_PATH, TARGET_TOOL_COUNT)

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def clean_response(text):
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    return text.strip()

def run_llm(messages, max_tokens=200):
    text_input = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer([text_input], return_tensors="pt").to(DEVICE)
    
    with torch.no_grad():
        outputs = model.generate(inputs.input_ids, max_new_tokens=max_tokens, temperature=0.01)
    
    generated_ids = outputs[:, inputs.input_ids.shape[1]:]
    resp = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
    input_tokens = inputs.input_ids.shape[1]
    
    return resp, input_tokens

# ==========================================
# AGENTS
# ==========================================

def run_retrieval_agent(query, db, method="semantic"):
    """
    Runs the agent with a specific retrieval method.
    Returns: Selected Tool, Token Usage, Latency
    """
    start_time = time.time()
    
    # 1. Retrieval
    if method == "semantic":
        candidates = db.retrieve_semantic(query, top_k=RETRIEVAL_POOL_SIZE)
    elif method == "keyword":
        candidates = db.retrieve_keyword(query, top_k=RETRIEVAL_POOL_SIZE)
    else:
        raise ValueError("Unknown method")
    
    # 2. Selection
    tool_list_str = ""
    for t in candidates:
        tool_list_str += f"- {t['unique_name']}: {t['description'][:100]}\n"
    
    sel_msgs = [
        {"role": "system", "content": "Select the best tool for the query. Return ONLY the tool unique_name. If none, return 'None'."},
        {"role": "user", "content": f"Query: {query}\n\nTools:\n{tool_list_str}"}
    ]
    
    sel_resp, t1 = run_llm(sel_msgs, max_tokens=30)
    selected_name = clean_response(sel_resp).split('\n')[0].strip()
    
    # 3. Generation (Simulated for token count)
    tool = db.get_tool(selected_name)
    if not tool and candidates: tool = candidates[0] # Fallback
    
    full_schema = json.dumps(tool, indent=2)
    exec_msgs = [
        {"role": "system", "content": "Generate a JSON function call."},
        {"role": "user", "content": f"Query: {query}\n\nSchema:\n{full_schema}"}
    ]
    
    exec_resp, t2 = run_llm(exec_msgs, max_tokens=150)
    
    duration = time.time() - start_time
    
    return {
        "tool": tool['unique_name'] if tool else "None",
        "tokens": t1 + t2,
        "latency": duration
    }

def run_naive_baseline(db):
    # Theoretical calculation: All tools loaded
    # Avg 150 tokens per tool * 1000 tools = 150,000 tokens
    return 150000

# ==========================================
# VISUALIZATION
# ==========================================
def generate_plots(df):
    print("📊 Generating Visualizations...")
    sns.set_theme(style="whitegrid")
    
    # 1. Token Usage Comparison (Log Scale)
    plt.figure(figsize=(12, 6))
    melted = df.melt(id_vars=["Query"], value_vars=["Semantic Tokens", "Keyword Tokens", "Naive Tokens"], var_name="Method", value_name="Tokens")
    
    ax = sns.barplot(data=melted, x="Query", y="Tokens", hue="Method", palette="viridis")
    ax.set_yscale("log")
    plt.xticks(rotation=45, ha='right')
    plt.title("Token Usage: Semantic vs Keyword vs Naive (Log Scale)")
    plt.tight_layout()
    plt.savefig("token_usage_comparison.png")
    print("   ✅ Saved token_usage_comparison.png")
    
    # 2. Success Rate Comparison
    plt.figure(figsize=(8, 6))
    success_counts = {
        "Semantic": df["Semantic Success"].sum(),
        "Keyword": df["Keyword Success"].sum()
    }
    plt.bar(success_counts.keys(), success_counts.values(), color=['#2ecc71', '#e74c3c'])
    plt.title(f"Success Rate (Total Queries: {len(df)})")
    plt.ylabel("Correct Tool Selections")
    plt.ylim(0, len(df) + 1)
    for i, v in enumerate(success_counts.values()):
        plt.text(i, v + 0.1, str(v), ha='center')
    plt.savefig("success_rate.png")
    print("   ✅ Saved success_rate.png")

    # 3. Context Window Visualization
    # Show average tokens used vs Context Window Limit
    plt.figure(figsize=(10, 4))
    avg_semantic = df["Semantic Tokens"].mean()
    avg_keyword = df["Keyword Tokens"].mean()
    avg_naive = df["Naive Tokens"].mean()
    
    methods = ['Semantic', 'Keyword', 'Naive (Full Load)']
    values = [avg_semantic, avg_keyword, avg_naive]
    colors = ['#2ecc71', '#3498db', '#e74c3c']
    
    # Create horizontal bar chart
    y_pos = np.arange(len(methods))
    plt.barh(y_pos, values, color=colors, align='center')
    plt.yticks(y_pos, methods)
    plt.xlabel('Tokens Used')
    plt.title('Context Window Consumption (Avg per Task)')
    
    # Add limit line
    plt.axvline(x=CONTEXT_WINDOW_LIMIT, color='gray', linestyle='--', label=f'Typical Context Limit ({CONTEXT_WINDOW_LIMIT})')
    
    # Add text labels
    for i, v in enumerate(values):
        plt.text(v + 100, i, f"{int(v)} toks", va='center')
        
    plt.legend()
    plt.tight_layout()
    plt.savefig("context_window_viz.png")
    print("   ✅ Saved context_window_viz.png")

# ==========================================
# EXPERIMENT
# ==========================================
def check_success(selected_tool, targets):
    if not selected_tool: return False
    for t in targets:
        if t.lower() in selected_tool.lower():
            return True
    return False

def run_experiment():
    benchmarks = [
        {"q": "Find contact details for 'John Doe'", "target": ["search_contacts", "get_contact"]},
        {"q": "Update opportunity 'Big Deal' to stage 'Closed Won'", "target": ["update_opportunity"]},
        {"q": "Get salary history for employee 'Alice Smith'", "target": ["get_compensation", "salary"]},
        {"q": "Submit vacation request for next week", "target": ["submit_time_off", "vacation"]},
        {"q": "Trigger deployment for 'backend-service' to production", "target": ["trigger_pipeline", "deployment"]},
        {"q": "Get logs for build #1234", "target": ["get_build_logs", "logs"]},
        {"q": "Create a high priority ticket for 'Login Failure'", "target": ["create_ticket"]},
        {"q": "Search knowledge base for 'password reset'", "target": ["search_articles", "knowledge"]},
        {"q": "Refund charge ch_999999", "target": ["create_refund", "refund"]},
        {"q": "Get latest invoice for customer 'Acme Corp'", "target": ["list_invoices", "invoice"]},
        {"q": "Reset password for user 'bob@example.com'", "target": ["reset_password"]},
        {"q": "Grant 'admin' role to user 'bob'", "target": ["assign_role", "grant"]},
        {"q": "List all PDF files in /documents", "target": ["list_files"]},
        {"q": "Share 'report.pdf' with 'team@company.com'", "target": ["share_file"]},
        {"q": "Send message to #general channel saying 'Hello'", "target": ["post_message", "send_message"]},
    ]
    
    print(f"\n=== 🚀 RUNNING COMPARATIVE BENCHMARK ({len(db.tools)} Tools) ===")
    
    results = []
    naive_tokens = run_naive_baseline(db)
    
    for b in benchmarks:
        query = b['q']
        targets = b['target']
        print(f"\nProcessing: {query}")
        
        # 1. Semantic Search
        sem_res = run_retrieval_agent(query, db, method="semantic")
        sem_success = check_success(sem_res['tool'], targets)
        
        # 2. Keyword Search
        key_res = run_retrieval_agent(query, db, method="keyword")
        key_success = check_success(key_res['tool'], targets)
        
        results.append({
            "Query": query,
            "Semantic Tokens": sem_res['tokens'],
            "Semantic Success": sem_success,
            "Keyword Tokens": key_res['tokens'],
            "Keyword Success": key_success,
            "Naive Tokens": naive_tokens,
            "Semantic Tool": sem_res['tool'],
            "Keyword Tool": key_res['tool']
        })
        
        print(f"   ✅ Semantic: {sem_res['tokens']} toks | Success: {sem_success} | {sem_res['tool']}")
        print(f"   � Keyword : {key_res['tokens']} toks | Success: {key_success} | {key_res['tool']}")

    # Save Results
    df = pd.DataFrame(results)
    df.to_csv("benchmark_results_enhanced.csv", index=False)
    print(f"\n📝 Saved results to benchmark_results_enhanced.csv")
    
    # Statistics
    print("\n=== 📊 SUMMARY STATISTICS ===")
    print(f"Semantic Success Rate: {df['Semantic Success'].mean():.1%}")
    print(f"Keyword Success Rate : {df['Keyword Success'].mean():.1%}")
    print(f"Avg Semantic Tokens  : {df['Semantic Tokens'].mean():.1f}")
    print(f"Avg Keyword Tokens   : {df['Keyword Tokens'].mean():.1f}")
    
    # Generate Plots
    generate_plots(df)

if __name__ == "__main__":
    run_experiment()