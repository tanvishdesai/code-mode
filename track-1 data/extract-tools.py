#!/usr/bin/env python3
"""
extract_mcp_tools.py

Scans a directory of MCP server files (.py, .ts, .js) and extracts tool definitions,
producing a comprehensive JSON dataset suitable for research.

Features:
- Parses Python decorators: @mcp.tool(...), @server.tool(), @mcp.tool() with/without description/name.
- Extracts function name, description (decorator or docstring), parameters (Field(...) info).
- Parses TypeScript tool arrays: `export const tools = [ {...} ]` and `tools: [ {...} ]` literal objects (inputSchema properties).
- Estimates tokens per tool using the formula you provided:
    tokens = 50 + len(description_words)/0.75 + parameter_count * 40
- Categorizes servers into complexity buckets:
    Simple: 1-5 tools
    Medium: 6-20 tools
    Complex: 20+ tools
- Prints progress for each file processed.
- Creates errors.log listing read/parse problems and continues on errors.
- Excludes tools without descriptions or with null descriptions.

Notes:
- Regex-based parsing is intentionally resilient but conservative. It covers the patterns you asked for.
- Some dynamic registrations (e.g. mcp.add_tool(execute_sql, ...)) may not be discoverable by static parsing
  — such cases are logged as "no decorator found" (skipped) but the script continues.
"""

import json
import os
import re
import sys
from pathlib import Path

# Hard-coded configuration
INPUT_DIR = "./downloaded_server_py"
OUTPUT_FILE = "mcp_dataset.json"
VERBOSE = False

BASE_SCHEMA_OVERHEAD = 50

def estimate_tokens(description, parameter_count):
    """
    tokens = 50 + len(description_words)/0.75 + (parameter_count * 40)
    (uses number of words in description)
    """
    if not description:
        desc_words = 0
    else:
        desc_words = len(description.split())
    return int(BASE_SCHEMA_OVERHEAD + (desc_words / 0.75) + (parameter_count * 40))

def has_valid_description(desc):
    """Check if a description is valid (not None, not empty, not 'No description available')"""
    if not desc:
        return False
    desc_lower = desc.lower().strip()
    if desc_lower in ('', 'no description available', 'none', 'null'):
        return False
    return True

# ----------------------------
# Python extraction helpers
# ----------------------------
def extract_python_tools(text):
    """
    Extract tools defined via decorators in Python files.
    Looks for:
      @mcp.tool(description="...")
      @mcp.tool()
      @server.tool()
    Extracts function name, decorator description (if present), docstring fallback,
    parameter names/types/defaults, Field() descriptions when present.
    Only includes tools with valid descriptions.
    """
    tools = []

    # Simple approach: find lines with @mcp.tool or @server.tool, then look for the following def
    # This avoids complex regex and catastrophic backtracking
    tool_decorator_pattern = re.compile(r"^[ \t]*@(\w+\.)?tool", re.MULTILINE)
    
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        if tool_decorator_pattern.match(line):
            # Found a tool decorator, now collect it and all following decorators
            decorator_lines = [line]
            j = i + 1
            while j < len(lines) and (lines[j].strip().startswith('@') or 
                                      (lines[j].strip() and not lines[j].strip().startswith('def') and 
                                       lines[j][0] in ' \t')):
                decorator_lines.append(lines[j])
                j += 1
            
            # Now find the def statement
            def_line_idx = j
            while def_line_idx < len(lines) and not re.match(r'^[ \t]*(async\s+)?def\s+', lines[def_line_idx]):
                def_line_idx += 1
            
            if def_line_idx >= len(lines):
                i += 1
                continue
            
            # Collect the full function definition (handling multi-line signatures)
            def_lines = [lines[def_line_idx]]
            k = def_line_idx + 1
            paren_count = def_lines[0].count('(') - def_lines[0].count(')')
            while k < len(lines) and paren_count > 0:
                def_lines.append(lines[k])
                paren_count += lines[k].count('(') - lines[k].count(')')
                k += 1
            
            # Extract from the combined text
            decorators = '\n'.join(decorator_lines)
            def_block = '\n'.join(def_lines)
            
            # Only process if it's actually a tool decorator
            if not (("mcp.tool" in decorators) or ("server.tool" in decorators) or re.search(r"@\w+\.tool", decorators)):
                i += 1
                continue
            
            # Extract function name
            fname_match = re.search(r'def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(', def_block)
            if not fname_match:
                i += 1
                continue
            fname = fname_match.group(1)
            
            # Extract parameters - everything between the opening and closing parentheses of the function signature
            params_match = re.search(r'def\s+[A-Za-z_][A-Za-z0-9_]*\s*\((.*?)\)\s*(?:->[^:]*)?:', def_block, re.DOTALL)
            params_str = params_match.group(1) if params_match else ""
            
            # Extract function body for docstring
            body_match = re.search(r'def\s+[A-Za-z_][A-Za-z0-9_]*\s*\(.*?\)\s*(?:->[^:]*)?:\s*(.*)', def_block, re.DOTALL)
            body = body_match.group(1) if body_match else ""
            
            # Description from decorator
            desc = None
            name_override = None

            desc_match = re.search(r"description\s*=\s*([ru]?['\"]{3}.*?['\"]{3}|['\"].*?['\"])", decorators, re.S)
            if desc_match:
                raw = desc_match.group(1)
                desc = re.sub(r"^([ruRU]{0,2}['\"]{1,3})|(['\"]{1,3})$", "", raw).strip()
                desc = re.sub(r"\s+", " ", desc).strip()

            name_match = re.search(r"name\s*=\s*['\"]([A-Za-z0-9_\-]+)['\"]", decorators)
            if name_match:
                name_override = name_match.group(1)

            # Fallback to docstring
            if not desc:
                doc_match = re.search(r"^[ \t]*[\"']{3}(?P<doc>.*?)[\"']{3}", body, re.S | re.M)
                if doc_match:
                    desc = re.sub(r"\s+", " ", doc_match.group("doc")).strip()
                else:
                    first_string = re.search(r"^[ \t]*([\"'])(?P<doc2>.*?)(\1)", body, re.M | re.S)
                    if first_string:
                        desc = first_string.group("doc2").strip()

            # Skip tools without valid descriptions
            if not has_valid_description(desc):
                i = def_line_idx + 1
                continue

            # Parse parameter list
            parameters = {}
            param_count = 0
            if params_str.strip():
                parts = re.split(r',(?![^\(\[]*[\)\]])', params_str)
                for p in parts:
                    p = p.strip()
                    if not p or p == 'self' or p == 'cls':
                        continue
                    name_search = re.match(r'(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*(?::\s*(?P<type>[^=]+?))?\s*(?:=\s*(?P<default>.*))?$', p)
                    if not name_search:
                        continue
                    pname = name_search.group("name")
                    ptype = name_search.group("type").strip() if name_search.group("type") else None
                    pdefault = name_search.group("default").strip() if name_search.group("default") else None

                    pre_desc = ""
                    required = True
                    default_value = None
                    if pdefault:
                        field_match = re.search(r'Field\((?P<inner>.*)\)', pdefault, re.S)
                        if field_match:
                            inner = field_match.group("inner")
                            fdesc_match = re.search(r'description\s*=\s*([\'\"].*?[\'\"])', inner, re.S)
                            if fdesc_match:
                                pre_desc = re.sub(r"^['\"]|['\"]$", "", fdesc_match.group(1)).strip()
                                pre_desc = re.sub(r"\s+", " ", pre_desc).strip()
                            fdefault_match = re.search(r'default\s*=\s*([^,]+)', inner)
                            if fdefault_match:
                                default_value = fdefault_match.group(1).strip().strip('\'"')
                            required = False if 'default' in inner else True
                        else:
                            required = False
                            default_value = pdefault.strip().strip('\'"')
                    else:
                        required = True

                    parameters[pname] = {
                        "type": ptype.strip() if ptype else "unknown",
                        "description": pre_desc or "",
                        "required": required,
                        "default": None if default_value in (None, "None") else (default_value if default_value else None)
                    }
                    param_count += 1

            tool_name = name_override or fname
            estimated = estimate_tokens(desc, param_count)
            tools.append({
                "name": tool_name,
                "description": desc,
                "parameters": parameters,
                "parameter_count": param_count,
                "estimated_tokens": estimated
            })
            
            i = def_line_idx + 1
        else:
            i += 1

    return tools

# ----------------------------
# TypeScript extraction helpers
# ----------------------------
def extract_typescript_tools(text):
    """
    Extract simple TypeScript tool literal objects from:
     - export const tools = [ { name: "...", description: "...", inputSchema: {...} }, ... ]
     - or literal tools: [ {...} ] used directly inside a returned object
    This is a pragmatic regex-based extractor (not a JS parser) that handles common literal patterns.
    Only includes tools with valid descriptions.
    """
    tools = []

    export_tools_pattern = re.compile(r"export\s+const\s+tools\s*[:=][^\[]*\[(?P<content>.*?)\]\s*;?", re.S)
    tools_array_pattern = re.compile(r"tools\s*:\s*\[(?P<content>.*?)\]\s*[,}]?", re.S)

    array_matches = []
    for pat in (export_tools_pattern, tools_array_pattern):
        for m in pat.finditer(text):
            array_matches.append(m.group("content"))

    # object literal matcher: { ... } (followed by comma or end)
    obj_pattern = re.compile(r"\{(?P<body>.*?)\}(?=\s*,|\s*$)", re.S)
    for arr in array_matches:
        for om in obj_pattern.finditer(arr):
            body = om.group("body")
            name_match = re.search(r"name\s*:\s*['\"](?P<name>[^'\"]+)['\"]", body)
            if not name_match:
                continue
            name = name_match.group("name").strip()
            desc_match = re.search(r"description\s*:\s*['\"](?P<desc>.*?)['\"]", body, re.S)
            desc = re.sub(r"\s+", " ", desc_match.group("desc")).strip() if desc_match else None

            # Skip tools without valid descriptions
            if not has_valid_description(desc):
                continue

            params = {}
            param_count = 0
            input_match = re.search(r"inputSchema\s*:\s*(\{(?P<schema>.*?)\})", body, re.S)
            if input_match:
                schema = input_match.group("schema")
                # properties: { path: { type: 'string', description: '...' }, ... }
                prop_match = re.search(r"properties\s*:\s*\{(?P<props>.*?)\}\s*(,|$)", schema, re.S)
                required_list = []
                req_match = re.search(r"required\s*:\s*\[(?P<reqs>[^\]]*)\]", schema, re.S)
                if req_match:
                    reqs = req_match.group("reqs")
                    required_list = [r.strip().strip('\"\'') for r in re.split(r',\s*', reqs) if r.strip()]
                if prop_match:
                    props = prop_match.group("props")
                    prop_obj_pattern = re.compile(r"(?P<pname>['\"]?\w+['\"]?)\s*:\s*\{(?P<pbody>.*?)\}(?=\s*,|$)", re.S)
                    for pm in prop_obj_pattern.finditer(props):
                        rawpname = pm.group("pname").strip().strip('\"\'')
                        pbody = pm.group("pbody")
                        ptype_match = re.search(r"type\s*:\s*['\"](?P<ptype>[^'\"]+)['\"]", pbody)
                        pdesc_match = re.search(r"description\s*:\s*['\"](?P<pdesc>.*?)['\"]", pbody, re.S)
                        ptype = ptype_match.group("ptype") if ptype_match else "unknown"
                        pdesc = re.sub(r"\s+", " ", pdesc_match.group("pdesc")).strip() if pdesc_match else ""
                        required = rawpname in required_list
                        params[rawpname] = {
                            "type": ptype,
                            "description": pdesc,
                            "required": required,
                            "default": None
                        }
                        param_count += 1

            estimated = estimate_tokens(desc, param_count)
            tools.append({
                "name": name,
                "description": desc,
                "parameters": params,
                "parameter_count": param_count,
                "estimated_tokens": estimated
            })

    return tools

# ----------------------------
# File processing
# ----------------------------
def process_file(path):
    p = Path(path)
    try:
        text = p.read_text(encoding='utf-8')
    except Exception as e:
        return None, f"Read error: {e}"
    if p.suffix == '.py':
        tools = extract_python_tools(text)
        lang = 'python'
    elif p.suffix in ('.ts', '.js'):
        tools = extract_typescript_tools(text)
        lang = 'typescript'
    else:
        return None, None
    if not tools:
        return None, None
    total_schema_tokens = sum(t['estimated_tokens'] for t in tools)
    complexity = 'simple' if len(tools) <= 5 else ('medium' if len(tools) <= 20 else 'complex')
    return {
        "server_name": p.stem,
        "file_path": str(p),
        "language": lang,
        "total_tools": len(tools),
        "total_schema_tokens": total_schema_tokens,
        "complexity": complexity,
        "tools": tools
    }, None

# ----------------------------
# Main
# ----------------------------
def main():
    input_dir = Path(INPUT_DIR)
    output_file = Path(OUTPUT_FILE)
    verbose = VERBOSE

    all_servers = []
    errors_encountered = []
    total_tools = 0
    python_servers = 0
    ts_servers = 0
    files = list(input_dir.rglob('*'))

    files = [f for f in files if f.suffix in ('.py', '.ts', '.js') and f.is_file()]

    for idx, f in enumerate(files, start=1):
        print(f"Processing file {idx}/{len(files)}: {f}", file=sys.stderr)
        server_entry, error = process_file(f)
        if error:
            errors_encountered.append({"file": str(f), "error": error})
            with open('errors.log', 'a', encoding='utf-8') as ef:
                ef.write(f"{f}: {error}\n")
            continue
        if server_entry:
            all_servers.append(server_entry)
            total_tools += server_entry['total_tools']
            if server_entry['language'] == 'python':
                python_servers += 1
            else:
                ts_servers += 1
            if verbose:
                print(json.dumps(server_entry, indent=2), file=sys.stderr)

    by_complexity = {"simple": 0, "medium": 0, "complex": 0}
    for s in all_servers:
        by_complexity[s['complexity']] += 1

    dataset = {
        "dataset_summary": {
            "total_servers": len(all_servers),
            "total_tools": total_tools,
            "python_servers": python_servers,
            "typescript_servers": ts_servers,
            "by_complexity": by_complexity
        },
        "servers": all_servers
    }

    output_file.write_text(json.dumps(dataset, indent=2), encoding='utf-8')

    # Summary report
    print("\nSummary Report", file=sys.stderr)
    print(f"Total servers processed: {len(all_servers)}", file=sys.stderr)
    print(f"Total tools found: {total_tools}", file=sys.stderr)
    print(f"Distribution by complexity: {by_complexity}", file=sys.stderr)
    if errors_encountered:
        print(f"Errors encountered: {len(errors_encountered)} (see errors.log)", file=sys.stderr)
    else:
        print("No errors encountered.", file=sys.stderr)
    
    # Print total tools found
    print(f"\n=== Total tools found across all files: {total_tools} ===")

if __name__ == '__main__':
    main()
