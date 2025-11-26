import json
import os

def generate_drive_server():
    tools = []
    
    # Common parameter definitions
    params_id = {"type": "string", "description": "Unique identifier of the file or folder", "required": True}
    params_limit = {"type": "integer", "description": "Maximum number of results to return", "default": 50}
    
    # 1. File Operations (10 tools)
    tools.extend([
        {
            "name": "upload_file",
            "description": "Uploads a new file.",
            "parameters": {
                "name": {"type": "string", "required": True},
                "parent_id": {"type": "string", "description": "ID of the parent folder"},
                "content_base64": {"type": "string", "required": True},
                "mime_type": {"type": "string"}
            }
        },
        {
            "name": "get_file_metadata",
            "description": "Retrieves metadata for a file.",
            "parameters": {"file_id": params_id}
        },
        {
            "name": "download_file",
            "description": "Downloads the content of a file.",
            "parameters": {
                "file_id": params_id,
                "format": {"type": "string", "description": "Optional export format (e.g., pdf for docs)"}
            }
        },
        {
            "name": "update_file_metadata",
            "description": "Updates a file's name or description.",
            "parameters": {
                "file_id": params_id,
                "name": {"type": "string"},
                "description": {"type": "string"},
                "starred": {"type": "boolean"}
            }
        },
        {
            "name": "delete_file",
            "description": "Moves a file to the trash.",
            "parameters": {"file_id": params_id}
        },
        {
            "name": "copy_file",
            "description": "Creates a copy of a file.",
            "parameters": {
                "file_id": params_id,
                "name": {"type": "string", "description": "Name of the copy"},
                "parent_id": {"type": "string", "description": "Destination folder"}
            }
        },
        {
            "name": "move_file",
            "description": "Moves a file to a different folder.",
            "parameters": {
                "file_id": params_id,
                "new_parent_id": {"type": "string", "required": True}
            }
        },
        {
            "name": "list_files",
            "description": "Lists files in a folder or matching a query.",
            "parameters": {
                "query": {"type": "string", "description": "Search query"},
                "parent_id": {"type": "string"},
                "limit": params_limit,
                "order_by": {"type": "string", "default": "modifiedTime desc"}
            }
        },
        {
            "name": "restore_file",
            "description": "Restores a file from the trash.",
            "parameters": {"file_id": params_id}
        },
        {
            "name": "empty_trash",
            "description": "Permanently deletes all files in the trash.",
            "parameters": {}
        }
    ])

    # 2. Folder Operations (5 tools)
    tools.extend([
        {
            "name": "create_folder",
            "description": "Creates a new folder.",
            "parameters": {
                "name": {"type": "string", "required": True},
                "parent_id": {"type": "string"}
            }
        },
        {
            "name": "get_folder_metadata",
            "description": "Retrieves metadata for a folder.",
            "parameters": {"folder_id": params_id}
        },
        {
            "name": "list_folders",
            "description": "Lists subfolders within a folder.",
            "parameters": {
                "parent_id": {"type": "string", "required": True},
                "limit": params_limit
            }
        },
        {
            "name": "move_folder",
            "description": "Moves a folder to a different location.",
            "parameters": {
                "folder_id": params_id,
                "new_parent_id": {"type": "string", "required": True}
            }
        },
        {
            "name": "delete_folder",
            "description": "Moves a folder to the trash.",
            "parameters": {"folder_id": params_id}
        }
    ])

    # 3. Permissions & Sharing (8 tools)
    tools.extend([
        {
            "name": "share_file",
            "description": "Shares a file with a user or group.",
            "parameters": {
                "file_id": params_id,
                "email": {"type": "string", "required": True},
                "role": {"type": "string", "enum": ["reader", "commenter", "writer"], "required": True},
                "notify": {"type": "boolean", "default": True}
            }
        },
        {
            "name": "unshare_file",
            "description": "Removes a user's access to a file.",
            "parameters": {
                "file_id": params_id,
                "permission_id": {"type": "string", "required": True}
            }
        },
        {
            "name": "list_permissions",
            "description": "Lists all permissions on a file.",
            "parameters": {"file_id": params_id}
        },
        {
            "name": "update_permission",
            "description": "Updates a user's role on a file.",
            "parameters": {
                "file_id": params_id,
                "permission_id": {"type": "string", "required": True},
                "role": {"type": "string", "enum": ["reader", "commenter", "writer"], "required": True}
            }
        },
        {
            "name": "create_shared_drive",
            "description": "Creates a new shared drive (team drive).",
            "parameters": {
                "name": {"type": "string", "required": True}
            }
        },
        {
            "name": "add_shared_drive_member",
            "description": "Adds a member to a shared drive.",
            "parameters": {
                "drive_id": {"type": "string", "required": True},
                "email": {"type": "string", "required": True},
                "role": {"type": "string", "enum": ["organizer", "fileOrganizer", "writer", "commenter", "reader"], "required": True}
            }
        },
        {
            "name": "list_shared_drives",
            "description": "Lists shared drives the user has access to.",
            "parameters": {"limit": params_limit}
        },
        {
            "name": "get_share_link",
            "description": "Generates a shareable link for a file.",
            "parameters": {
                "file_id": params_id,
                "access_level": {"type": "string", "enum": ["anyone", "domain", "restricted"], "default": "restricted"}
            }
        }
    ])

    # 4. Comments & Revisions (7 tools)
    tools.extend([
        {
            "name": "create_comment",
            "description": "Adds a comment to a file.",
            "parameters": {
                "file_id": params_id,
                "content": {"type": "string", "required": True},
                "anchor": {"type": "string", "description": "JSON string specifying location in file"}
            }
        },
        {
            "name": "list_comments",
            "description": "Lists comments on a file.",
            "parameters": {"file_id": params_id}
        },
        {
            "name": "resolve_comment",
            "description": "Marks a comment as resolved.",
            "parameters": {
                "file_id": params_id,
                "comment_id": {"type": "string", "required": True}
            }
        },
        {
            "name": "list_revisions",
            "description": "Lists version history of a file.",
            "parameters": {"file_id": params_id}
        },
        {
            "name": "get_revision",
            "description": "Retrieves metadata for a specific revision.",
            "parameters": {
                "file_id": params_id,
                "revision_id": {"type": "string", "required": True}
            }
        },
        {
            "name": "update_revision",
            "description": "Updates revision properties (e.g., keep forever).",
            "parameters": {
                "file_id": params_id,
                "revision_id": {"type": "string", "required": True},
                "keep_forever": {"type": "boolean", "required": True}
            }
        },
        {
            "name": "delete_revision",
            "description": "Deletes a specific revision.",
            "parameters": {
                "file_id": params_id,
                "revision_id": {"type": "string", "required": True}
            }
        }
    ])

    # Post-processing
    final_tools = []
    for t in tools:
        text = t['name'] + t['description'] + json.dumps(t['parameters'])
        est_tokens = len(text) // 4
        
        final_tools.append({
            "name": t['name'],
            "description": t['description'],
            "parameters": t['parameters'],
            "parameter_count": len(t['parameters']),
            "estimated_tokens": est_tokens
        })

    return {
        "server_name": "file-storage-mcp-server",
        "file_path": "synthetic/drive_server.py",
        "language": "python",
        "total_tools": len(final_tools),
        "total_schema_tokens": sum(t['estimated_tokens'] for t in final_tools),
        "complexity": "medium",
        "tools": final_tools
    }

if __name__ == "__main__":
    server_data = generate_drive_server()
    output_path = "synthetic_data/drive_server.json"
    
    with open(output_path, "w") as f:
        json.dump(server_data, f, indent=2)
        
    print(f"Generated {len(server_data['tools'])} tools in {output_path}")
