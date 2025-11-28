import json
import os
import glob

def verify_dataset():
    base_dir = "synthetic_data"
    json_files = glob.glob(os.path.join(base_dir, "*_server.json"))
    
    total_synthetic_tools = 0
    synthetic_servers = []
    
    print(f"Found {len(json_files)} synthetic server files.")
    
    for file_path in json_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            server_name = data.get('server_name', 'unknown')
            tools = data.get('tools', [])
            count = len(tools)
            
            total_synthetic_tools += count
            synthetic_servers.append(data)
            
            # Basic validation
            for tool in tools:
                if not all(k in tool for k in ['name', 'description', 'parameters']):
                    print(f"WARNING: Invalid tool structure in {server_name}: {tool.get('name', 'UNKNOWN')}")
                    
            print(f"Verified {server_name}: {count} tools")
            
        except Exception as e:
            print(f"ERROR reading {file_path}: {e}")

    print("-" * 30)
    print(f"Total Synthetic Tools: {total_synthetic_tools}")
    
    # Load existing dataset
    existing_path = "mcp_dataset.json"
    final_data = {"dataset_summary": {}, "servers": []}
    
    if os.path.exists(existing_path):
        with open(existing_path, 'r') as f:
            existing_data = json.load(f)
            final_data = existing_data
            
            existing_servers = existing_data.get('servers', [])
            existing_tool_count = sum(len(s.get('tools', [])) for s in existing_servers)
            
            print(f"Existing Real Tools: {existing_tool_count}")
            
            # Merge synthetic servers into the list
            final_data['servers'].extend(synthetic_servers)
            
            # Update summary
            final_data['dataset_summary']['total_servers'] = len(final_data['servers'])
            final_data['dataset_summary']['total_tools'] = existing_tool_count + total_synthetic_tools
            
            print(f"GRAND TOTAL: {final_data['dataset_summary']['total_tools']}")

    # Create consolidated file
    consolidated_path = "mcp_dataset_enhanced.json"
    with open(consolidated_path, 'w') as f:
        json.dump(final_data, f, indent=2)
    print(f"Created consolidated dataset at {consolidated_path}")

if __name__ == "__main__":
    verify_dataset()
