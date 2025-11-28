import json
import sys
sys.path.append("../aid_framework")
from inference import InterfaceDistiller

# Mock "Subtle Bugs" Dataset
# Cases where type checking passes but logic fails
TEST_CASES = [
    {
        "query": "Set age to -5",
        "schema": {"paths": {"/update_user": {"post": {"parameters": [{"name": "age", "type": "integer"}]}}}},
        "expected_constraint": "age >= 0"
    },
    {
        "query": "Set end date to 2020-01-01 and start date to 2021-01-01",
        "schema": {"paths": {"/schedule": {"post": {"parameters": [{"name": "start", "type": "string"}, {"name": "end", "type": "string"}]}}}},
        "expected_constraint": "end > start"
    }
]

def run_benchmark():
    print("🚀 Running Safety Benchmark...")
    distiller = InterfaceDistiller()
    
    passed = 0
    
    for case in TEST_CASES:
        print(f"\nQuery: {case['query']}")
        
        # Distill
        _, constraints = distiller.distill(case['query'], case['schema'])
        
        print(f"Extracted Constraints: {constraints}")
        
        # Check if expected constraint (or similar) is present
        # Simple keyword match for prototype
        expected_keywords = case['expected_constraint'].split()
        found = False
        for c in constraints:
            if all(k in c for k in expected_keywords):
                found = True
                break
                
        if found:
            print("✅ Constraint Caught")
            passed += 1
        else:
            print("❌ Constraint Missed")
            
    print(f"\nSafety Score: {passed}/{len(TEST_CASES)}")

if __name__ == "__main__":
    run_benchmark()
