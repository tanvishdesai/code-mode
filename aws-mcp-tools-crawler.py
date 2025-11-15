import argparse
import ast
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# --- Constants ---
# Token estimation formula: 50 (base) + (word_count / 0.75) + (param_count * 40)
TOKEN_BASE_COST = 50
TOKEN_PER_PARAM_COST = 40
TOKEN_WORD_DIVISOR = 0.75

# --- Helper Functions ---

def estimate_tokens(description: str, param_count: int) -> int:
    """Estimates the token count for a tool's schema."""
    if not description:
        description = ""
    word_count = len(description.strip().split())
    
    description_cost = word_count / TOKEN_WORD_DIVISOR
    param_cost = param_count * TOKEN_PER_PARAM_COST
    
    return int(TOKEN_BASE_COST + description_cost + param_cost)

def get_complexity(tool_count: int) -> str:
    """Categorizes server complexity based on the number of tools."""
    if tool_count <= 5:
        return "simple"
    elif 6 <= tool_count <= 20:
        return "medium"
    else:
        return "complex"

# --- Python File Parser ---

def _parse_py_decorator(decorator: ast.Call) -> bool:
    """Check if a decorator node is an @mcp.tool or @server.tool call."""
    if isinstance(decorator.func, ast.Attribute):
        attr = decorator.func
        # Check for @mcp.tool or @server.tool
        if isinstance(attr.value, ast.Name) and attr.value.id in ('mcp', 'server'):
            if attr.attr == 'tool':
                return True
    return False

def _extract_py_tool_description(node: ast.FunctionDef, decorator: ast.Call) -> str:
    """Extract description from decorator args or function docstring."""
    # Prioritize description from decorator argument
    for keyword in decorator.keywords:
        if keyword.arg == 'description' and isinstance(keyword.value, ast.Constant):
            return keyword.value.s.strip()
            
    # Fallback to docstring
    docstring = ast.get_docstring(node)
    if docstring:
        return docstring.strip().split('\n')[0] # Get the first line
        
    return "No description available"

def _extract_py_parameters(node: ast.FunctionDef) -> Dict[str, Dict[str, Any]]:
    """Extract parameters from a Python function definition."""
    params = {}
    args = node.args.args
    
    # Match defaults to arguments from right to left
    defaults = node.args.defaults
    num_defaults = len(defaults)
    
    for i, arg in enumerate(args):
        if arg.arg in ('self', 'cls'):
            continue
        
        param_info: Dict[str, Any] = {"required": True}
        
        # Check for default value
        default_index = i - (len(args) - num_defaults)
        if default_index >= 0:
            param_info["required"] = False
            default_node = defaults[default_index]
            if isinstance(default_node, ast.Constant):
                param_info["default"] = default_node.value
            else:
                # Represent complex defaults as string
                param_info["default"] = ast.dump(default_node)

        # Extract type and description from Field annotation if present
        if isinstance(arg.annotation, ast.Call) and \
           isinstance(arg.annotation.func, ast.Name) and \
           arg.annotation.func.id == 'Field':
            
            for kw in arg.annotation.keywords:
                if kw.arg == 'description' and isinstance(kw.value, ast.Constant):
                    param_info['description'] = kw.value.s
                if kw.arg == 'default' and 'default' not in param_info:
                    param_info['required'] = False
                    if isinstance(kw.value, ast.Constant):
                        param_info['default'] = kw.value.value
        
        # Infer type from simple type hint
        if isinstance(arg.annotation, ast.Name):
             param_info['type'] = arg.annotation.id
        elif isinstance(arg.annotation, ast.Subscript) and isinstance(arg.annotation.value, ast.Name):
            # Handles list[str], dict[str, Any] etc.
            param_info['type'] = f"{arg.annotation.value.id}[...]"


        params[arg.arg] = param_info

    return params

def parse_python_file(file_path: Path) -> Optional[List[Dict[str, Any]]]:
    """Parses a Python file and extracts all MCP tool definitions using AST."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            tree = ast.parse(content, filename=str(file_path))
    except (SyntaxError, UnicodeDecodeError):
        return None # Let the main loop handle the error logging

    tools = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and _parse_py_decorator(decorator):
                    
                    name = node.name
                    description = _extract_py_tool_description(node, decorator)
                    parameters = _extract_py_parameters(node)
                    param_count = len(parameters)
                    
                    tool_data = {
                        "name": name,
                        "description": description,
                        "parameters": parameters,
                        "parameter_count": param_count,
                        "estimated_tokens": estimate_tokens(description, param_count)
                    }
                    tools.append(tool_data)
                    # A function can only be one tool, so break after finding the decorator
                    break 
    return tools if tools else None

# --- TypeScript File Parser ---

def _find_ts_tool_objects(content: str) -> List[str]:
    """Isolates tool object strings from a 'tools: [...]' array using brace counting."""
    tool_objects = []
    # Find the start of the tools array
    match = re.search(r'tools:\s*\[', content)
    if not match:
        return []
    
    content_from_array = content[match.end():]
    
    open_braces = 0
    in_object = False
    current_obj = ""
    
    for char in content_from_array:
        if char == '{':
            if not in_object:
                in_object = True
            open_braces += 1
            current_obj += char
        elif char == '}':
            open_braces -= 1
            current_obj += char
            if in_object and open_braces == 0:
                tool_objects.append(current_obj)
                current_obj = ""
                in_object = False
        elif open_braces > 0:
            current_obj += char
        elif char == ']' and not in_object:
            # End of the tools array
            break
            
    return tool_objects

def _parse_ts_input_schema(schema_str: str) -> Tuple[Dict[str, Dict[str, Any]], int]:
    """Parses the inputSchema block for parameters."""
    parameters = {}
    
    props_match = re.search(r'properties:\s*\{(.*?)\}', schema_str, re.DOTALL)
    if not props_match:
        return {}, 0

    props_str = props_match.group(1)
    
    req_match = re.search(r'required:\s*\[(.*?)\]', schema_str, re.DOTALL)
    required_list = []
    if req_match:
        required_list = [
            item.strip().strip('"\'') for item in req_match.group(1).split(',')
        ]
    
    # Find individual properties: name: { ... }
    prop_definitions = re.finditer(r'(\w+)\s*:\s*\{([^}]+)\}', props_str)
    for prop in prop_definitions:
        name = prop.group(1)
        details = prop.group(2)
        param_info: Dict[str, Any] = { "required": name in required_list }

        type_match = re.search(r'type:\s*["\'](\w+)["\']', details)
        if type_match:
            param_info['type'] = type_match.group(1)

        desc_match = re.search(r'description:\s*["\']([^"\']+)["\']', details)
        if desc_match:
            param_info['description'] = desc_match.group(1)
        
        parameters[name] = param_info

    return parameters, len(parameters)


def parse_typescript_file(file_path: Path) -> Optional[List[Dict[str, Any]]]:
    """Parses a TypeScript file to extract MCP tool definitions using regex."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Remove comments to simplify parsing
            content = re.sub(r'//.*', '', f.read())
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    except UnicodeDecodeError:
        return None

    tool_objects = _find_ts_tool_objects(content)
    if not tool_objects:
        return None

    tools = []
    for obj_str in tool_objects:
        name_match = re.search(r'name:\s*["\'`]([^"\'`]+)["\'`]', obj_str)
        desc_match = re.search(r'description:\s*["\'`]([^"\'`]+)["\'`]', obj_str, re.DOTALL)
        schema_match = re.search(r'inputSchema:\s*(\{.*?\})', obj_str, re.DOTALL)

        if name_match:
            name = name_match.group(1).strip()
            description = desc_match.group(1).strip() if desc_match else "No description available"
            
            parameters, param_count = {}, 0
            if schema_match:
                parameters, param_count = _parse_ts_input_schema(schema_match.group(1))

            tool_data = {
                "name": name,
                "description": description,
                "parameters": parameters,
                "parameter_count": param_count,
                "estimated_tokens": estimate_tokens(description, param_count)
            }
            tools.append(tool_data)
    
    return tools if tools else None


# --- Main Execution ---

def main():
    parser = argparse.ArgumentParser(
        description="Extract MCP tool definitions from Python and TypeScript server files."
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        required=True,
        help="Directory containing MCP server files."
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to the output JSON dataset file."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable detailed logging during processing."
    )
    args = parser.parse_args()

    input_path = Path(args.input_dir)
    if not input_path.is_dir():
        print(f"Error: Input directory not found at '{input_path}'")
        return

    files_to_process = list(input_path.rglob('*.py')) + \
                       list(input_path.rglob('*.ts')) + \
                       list(input_path.rglob('*.js'))
    
    if not files_to_process:
        print(f"Error: No .py, .ts, or .js files found in '{input_path}'")
        return

    all_servers_data = []
    errors = []
    total_files = len(files_to_process)

    print(f"Found {total_files} files to process...")

    for i, file_path in enumerate(files_to_process):
        print(f"Processing file {i+1}/{total_files}: {file_path.relative_to(input_path)}", end='\r')
        
        tools = None
        language = ""
        try:
            if file_path.suffix == '.py':
                language = 'python'
                tools = parse_python_file(file_path)
            elif file_path.suffix in ('.ts', '.js'):
                language = 'typescript'
                tools = parse_typescript_file(file_path)

            if tools:
                total_tools = len(tools)
                total_tokens = sum(t['estimated_tokens'] for t in tools)
                
                server_data = {
                    "server_name": file_path.stem.replace('server', '').replace('index', '').strip('-_'),
                    "file_path": str(file_path),
                    "language": language,
                    "total_tools": total_tools,
                    "total_schema_tokens": total_tokens,
                    "complexity": get_complexity(total_tools),
                    "tools": tools
                }
                all_servers_data.append(server_data)

                if args.verbose:
                    print(f"\n[SUCCESS] Extracted {total_tools} tools from {file_path.name}")

        except Exception as e:
            error_msg = f"Failed to process {file_path}: {e}"
            errors.append(error_msg)
            if args.verbose:
                print(f"\n[ERROR] {error_msg}")

    print("\n\nProcessing complete.")

    # --- Generate Summary and Output ---
    total_servers = len(all_servers_data)
    total_tools_found = sum(s['total_tools'] for s in all_servers_data)
    py_servers = sum(1 for s in all_servers_data if s['language'] == 'python')
    ts_servers = sum(1 for s in all_servers_data if s['language'] == 'typescript')

    complexity_counts = {
        "simple": sum(1 for s in all_servers_data if s['complexity'] == 'simple'),
        "medium": sum(1 for s in all_servers_data if s['complexity'] == 'medium'),
        "complex": sum(1 for s in all_servers_data if s['complexity'] == 'complex'),
    }

    dataset_summary = {
        "total_servers": total_servers,
        "total_tools": total_tools_found,
        "python_servers": py_servers,
        "typescript_servers": ts_servers,
        "by_complexity": complexity_counts
    }

    final_dataset = {
        "dataset_summary": dataset_summary,
        "servers": sorted(all_servers_data, key=lambda x: x['server_name'])
    }
    
    # Write JSON output
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(final_dataset, f, indent=2, ensure_ascii=False)
    
    print(f"\nSuccessfully generated JSON dataset at: {args.output}")

    # Write errors log
    if errors:
        error_log_path = "errors.log"
        with open(error_log_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(errors))
        print(f"Encountered {len(errors)} errors. See '{error_log_path}' for details.")

    # Print final report
    print("\n--- Summary Report ---")
    print(f"Total Servers with Tools: {total_servers}")
    print(f"  - Python Servers:     {py_servers}")
    print(f"  - TypeScript Servers:   {ts_servers}")
    print(f"Total Tools Found:        {total_tools_found}")
    print("Complexity Distribution:")
    print(f"  - Simple (1-5 tools):   {complexity_counts['simple']}")
    print(f"  - Medium (6-20 tools):  {complexity_counts['medium']}")
    print(f"  - Complex (20+ tools):  {complexity_counts['complex']}")
    print("------------------------\n")


if __name__ == "__main__":
    main()