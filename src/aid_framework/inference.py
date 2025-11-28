import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel, PeftConfig
import json

# Configuration
BASE_MODEL_ID = "Qwen/Qwen2.5-14B-Instruct"
ADAPTER_PATH = "../../models/aid_distiller"

class InterfaceDistiller:
    def __init__(self):
        print("⏳ Loading Distiller Model...")
        self.tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID, trust_remote_code=True)
        
        # Load Base Model
        self.base_model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL_ID,
            device_map="auto",
            torch_dtype=torch.float16,
            trust_remote_code=True
        )
        
        # Load Adapter
        if os.path.exists(ADAPTER_PATH):
            self.model = PeftModel.from_pretrained(self.base_model, ADAPTER_PATH)
            print("✅ Loaded LoRA Adapter.")
        else:
            print("⚠️ Adapter not found. Using base model (Zero-shot).")
            self.model = self.base_model

    def distill(self, query, full_schema):
        """
        Returns: (Minimal Schema JSON, Constraints List)
        """
        prompt = f"Instruction: Distill this interface for query: \"{query}\"\nFull Schema: {json.dumps(full_schema)}\n\nDistilled Interface: "
        
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        
        with torch.no_grad():
            outputs = self.model.generate(inputs.input_ids, max_new_tokens=512, temperature=0.1)
            
        response = self.tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
        
        # Parse Output
        # Expected format: <JSON> \nCONSTRAINTS:\n <JSON_LIST>
        try:
            parts = response.split("CONSTRAINTS:")
            minimal_schema = json.loads(parts[0].strip())
            constraints = []
            if len(parts) > 1:
                constraints = json.loads(parts[1].strip())
        except:
            print(f"⚠️ Failed to parse output:\n{response}")
            return full_schema, [] # Fallback
            
        return minimal_schema, constraints

if __name__ == "__main__":
    # Test
    distiller = InterfaceDistiller()
    q = "Get price of AAPL"
    schema = {"paths": {"/price": {"get": {"description": "Get stock price"}}, "/history": {"get": {"description": "Get history"}}}}
    
    mini, const = distiller.distill(q, schema)
    print("Minimal:", json.dumps(mini, indent=2))
    print("Constraints:", const)
