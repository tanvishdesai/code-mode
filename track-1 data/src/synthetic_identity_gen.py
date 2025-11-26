import json
import os

def generate_identity_server():
    tools = []
    
    # Common parameter definitions
    params_id = {"type": "string", "description": "Unique identifier of the resource", "required": True}
    params_limit = {"type": "integer", "description": "Maximum number of results to return", "default": 50}
    
    # 1. User Management (10 tools)
    tools.extend([
        {
            "name": "create_user",
            "description": "Creates a new user identity.",
            "parameters": {
                "email": {"type": "string", "required": True},
                "first_name": {"type": "string", "required": True},
                "last_name": {"type": "string", "required": True},
                "password": {"type": "string", "description": "Initial password (optional)"}
            }
        },
        {
            "name": "get_user",
            "description": "Retrieves user profile details.",
            "parameters": {"user_id": params_id}
        },
        {
            "name": "update_user",
            "description": "Updates user profile attributes.",
            "parameters": {
                "user_id": params_id,
                "first_name": {"type": "string"},
                "last_name": {"type": "string"},
                "email": {"type": "string"}
            }
        },
        {
            "name": "delete_user",
            "description": "Deletes a user identity.",
            "parameters": {"user_id": params_id}
        },
        {
            "name": "list_users",
            "description": "Lists users with optional filtering.",
            "parameters": {
                "query": {"type": "string", "description": "Search query"},
                "status": {"type": "string", "enum": ["active", "suspended", "deprovisioned"]},
                "limit": params_limit
            }
        },
        {
            "name": "suspend_user",
            "description": "Suspends a user account.",
            "parameters": {"user_id": params_id}
        },
        {
            "name": "unsuspend_user",
            "description": "Reactivates a suspended user account.",
            "parameters": {"user_id": params_id}
        },
        {
            "name": "reset_password",
            "description": "Triggers a password reset email for a user.",
            "parameters": {"user_id": params_id}
        },
        {
            "name": "expire_password",
            "description": "Forces a user to change their password on next login.",
            "parameters": {"user_id": params_id}
        },
        {
            "name": "unlock_user",
            "description": "Unlocks a user account locked due to failed login attempts.",
            "parameters": {"user_id": params_id}
        }
    ])

    # 2. Groups & Roles (8 tools)
    tools.extend([
        {
            "name": "create_group",
            "description": "Creates a new user group.",
            "parameters": {
                "name": {"type": "string", "required": True},
                "description": {"type": "string"}
            }
        },
        {
            "name": "delete_group",
            "description": "Deletes a group.",
            "parameters": {"group_id": params_id}
        },
        {
            "name": "add_user_to_group",
            "description": "Adds a user to a group.",
            "parameters": {
                "user_id": {"type": "string", "required": True},
                "group_id": {"type": "string", "required": True}
            }
        },
        {
            "name": "remove_user_from_group",
            "description": "Removes a user from a group.",
            "parameters": {
                "user_id": {"type": "string", "required": True},
                "group_id": {"type": "string", "required": True}
            }
        },
        {
            "name": "list_groups",
            "description": "Lists available groups.",
            "parameters": {
                "query": {"type": "string"},
                "limit": params_limit
            }
        },
        {
            "name": "list_group_members",
            "description": "Lists members of a group.",
            "parameters": {"group_id": params_id}
        },
        {
            "name": "assign_role",
            "description": "Assigns a role to a user.",
            "parameters": {
                "user_id": {"type": "string", "required": True},
                "role_id": {"type": "string", "required": True}
            }
        },
        {
            "name": "revoke_role",
            "description": "Revokes a role from a user.",
            "parameters": {
                "user_id": {"type": "string", "required": True},
                "role_id": {"type": "string", "required": True}
            }
        }
    ])

    # 3. Authentication & Sessions (7 tools)
    tools.extend([
        {
            "name": "create_api_token",
            "description": "Generates a new API token for a user.",
            "parameters": {
                "user_id": {"type": "string", "required": True},
                "name": {"type": "string", "required": True},
                "expires_in_days": {"type": "integer", "default": 30}
            }
        },
        {
            "name": "revoke_api_token",
            "description": "Revokes an API token.",
            "parameters": {"token_id": params_id}
        },
        {
            "name": "list_api_tokens",
            "description": "Lists active API tokens for a user.",
            "parameters": {"user_id": params_id}
        },
        {
            "name": "get_user_sessions",
            "description": "Lists active sessions for a user.",
            "parameters": {"user_id": params_id}
        },
        {
            "name": "revoke_user_sessions",
            "description": "Revokes all active sessions for a user.",
            "parameters": {"user_id": params_id}
        },
        {
            "name": "enable_mfa",
            "description": "Enables Multi-Factor Authentication for a user.",
            "parameters": {
                "user_id": {"type": "string", "required": True},
                "factor_type": {"type": "string", "enum": ["sms", "totp", "push"], "default": "totp"}
            }
        },
        {
            "name": "disable_mfa",
            "description": "Disables MFA for a user (requires admin privilege).",
            "parameters": {"user_id": params_id}
        }
    ])

    # 4. Policies & Audit (10 tools)
    tools.extend([
        {
            "name": "create_policy",
            "description": "Creates a new access policy.",
            "parameters": {
                "name": {"type": "string", "required": True},
                "statements": {"type": "array", "items": {"type": "object"}, "required": True}
            }
        },
        {
            "name": "get_policy",
            "description": "Retrieves a policy definition.",
            "parameters": {"policy_id": params_id}
        },
        {
            "name": "update_policy",
            "description": "Updates a policy definition.",
            "parameters": {
                "policy_id": params_id,
                "statements": {"type": "array", "items": {"type": "object"}}
            }
        },
        {
            "name": "delete_policy",
            "description": "Deletes a policy.",
            "parameters": {"policy_id": params_id}
        },
        {
            "name": "attach_policy_to_group",
            "description": "Attaches a policy to a group.",
            "parameters": {
                "policy_id": {"type": "string", "required": True},
                "group_id": {"type": "string", "required": True}
            }
        },
        {
            "name": "detach_policy_from_group",
            "description": "Detaches a policy from a group.",
            "parameters": {
                "policy_id": {"type": "string", "required": True},
                "group_id": {"type": "string", "required": True}
            }
        },
        {
            "name": "check_permission",
            "description": "Checks if a user has a specific permission.",
            "parameters": {
                "user_id": {"type": "string", "required": True},
                "permission": {"type": "string", "required": True},
                "resource": {"type": "string"}
            }
        },
        {
            "name": "get_audit_logs",
            "description": "Retrieves system audit logs.",
            "parameters": {
                "start_time": {"type": "string", "format": "datetime"},
                "end_time": {"type": "string", "format": "datetime"},
                "actor_id": {"type": "string"},
                "limit": params_limit
            }
        },
        {
            "name": "get_user_activity",
            "description": "Retrieves activity logs for a specific user.",
            "parameters": {
                "user_id": {"type": "string", "required": True},
                "limit": params_limit
            }
        },
        {
            "name": "create_application",
            "description": "Registers a new application (OIDC client).",
            "parameters": {
                "name": {"type": "string", "required": True},
                "redirect_uris": {"type": "array", "items": {"type": "string"}, "required": True},
                "grant_types": {"type": "array", "items": {"type": "string"}}
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
        "server_name": "identity-mcp-server",
        "file_path": "synthetic/identity_server.py",
        "language": "python",
        "total_tools": len(final_tools),
        "total_schema_tokens": sum(t['estimated_tokens'] for t in final_tools),
        "complexity": "high",
        "tools": final_tools
    }

if __name__ == "__main__":
    server_data = generate_identity_server()
    output_path = "synthetic_data/identity_server.json"
    
    with open(output_path, "w") as f:
        json.dump(server_data, f, indent=2)
        
    print(f"Generated {len(server_data['tools'])} tools in {output_path}")
