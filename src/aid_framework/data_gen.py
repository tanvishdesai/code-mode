import json
import random
import os
import pandas as pd
from tqdm import tqdm
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# Configuration
INPUT_FILE = "../../data/track1_dataset.jsonl"
OUTPUT_FILE = "../../data/aid_training_data.jsonl"
MODEL_ID = "Qwen/Qwen2.5-14B-Instruct" 

def load_model():
    print("⏳ Loading local model for data generation...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID, 
            device_map="auto", 
            torch_dtype=torch.float16,
            trust_remote_code=True
        )
        return tokenizer, model
    except Exception as e:
        print(f"⚠️ Failed to load model: {e}")
        return None, None

def generate_synthetic_data(tokenizer, model, summary, full_spec):
    """
    Uses the Teacher Model to generate:
    1. A natural language query.
    2. A list of safety constraints (logic).
    """
    if not model:
        return "Interact with endpoint", ["constraint1"]
        
    # 1. Generate Query
    prompt_q = [
        {"role": "system", "content": "Generate a natural language query for this API endpoint. Return ONLY the query."},
        {"role": "user", "content": f"Endpoint: {summary}"}
    ]
    text_q = tokenizer.apply_chat_template(prompt_q, tokenize=False, add_generation_prompt=True)
    inputs_q = tokenizer([text_q], return_tensors="pt").to(model.device)
    with torch.no_grad():
        out_q = model.generate(inputs_q.input_ids, max_new_tokens=50)
    query = tokenizer.batch_decode(out_q[:, inputs_q.input_ids.shape[1]:], skip_special_tokens=True)[0].strip('"')

    # 2. Extract Constraints (Neuro-Symbolic)
    # We ask the model to identify logical constraints from the spec/summary
    prompt_c = [
        {"role": "system", "content": "Extract logical safety constraints from this API description. Return a JSON list of strings. Example: [\"age >= 18\", \"end_date > start_date\"]"},
        {"role": "user", "content": f"Description: {summary}\nSpec Fragment: {json.dumps(full_spec)[:1000]}"}
    ]
    text_c = tokenizer.apply_chat_template(prompt_c, tokenize=False, add_generation_prompt=True)
    inputs_c = tokenizer([text_c], return_tensors="pt").to(model.device)
    with torch.no_grad():
        out_c = model.generate(inputs_c.input_ids, max_new_tokens=100)
    constraints_str = tokenizer.batch_decode(out_c[:, inputs_c.input_ids.shape[1]:], skip_special_tokens=True)[0]
    
    try:
        constraints = json.loads(constraints_str)
        if not isinstance(constraints, list): constraints = []
    except:
        constraints = []
        
    return query, constraints

def extract_minimal_schema(full_spec, target_path, target_method):
    # (Same as before: prune everything except target)
    minimal = {
        "openapi": full_spec.get("openapi", "3.0.0"),
        "paths": {target_path: {target_method: full_spec["paths"][target_path][target_method]}},
        "components": full_spec.get("components", {}) # simplified
    }
    return minimal

def process_data():
    if not os.path.exists(INPUT_FILE):
        print("❌ Dataset index not found. Run dataset_prep.py first (from Track 1, now reused).")
        return

    df = pd.read_json(INPUT_FILE, lines=True)
    tokenizer, model = load_model()
    
    training_data = []
    
    print(f"⏳ Generating AID training pairs...")
    for _, row in tqdm(df.iterrows(), total=len(df)):
        spec_path = row['spec_path']
        try:
            with open(spec_path, 'r', encoding='utf-8') as f:
                spec = json.load(f)
        except:
            continue
            
        paths = spec.get('paths', {})
        if not paths: continue
        
        targets = random.sample(list(paths.keys()), min(2, len(paths)))
        
        for path in targets:
            methods = paths[path]
            for method in methods:
                if method not in ['get', 'post', 'put', 'delete']: continue
                
                summary = methods[method].get('summary', methods[method].get('description', f"{method.upper()} {path}"))
                
                # Generate Query & Constraints
                query, constraints = generate_synthetic_data(tokenizer, model, summary, methods[method])
                
                # Minimal Schema
                minimal_schema = extract_minimal_schema(spec, path, method)
                
                # Unified Output Format
                # We train the model to output: <MINIMAL_JSON> <CONSTRAINTS_JSON>
                target_output = json.dumps(minimal_schema) + "\nCONSTRAINTS:\n" + json.dumps(constraints)
                
                training_data.append({
                    "query": query,
                    "full_schema": json.dumps(spec),
                    "target_output": target_output
                })
                
    pd.DataFrame(training_data).to_json(OUTPUT_FILE, orient='records', lines=True)
    print(f"✅ Saved {len(training_data)} AID training examples to {OUTPUT_FILE}")

if __name__ == "__main__":
    process_data()
