import json
import os

def generate_comm_server():
    tools = []
    
    # Common parameter definitions
    params_id = {"type": "string", "description": "Unique identifier of the record", "required": True}
    params_limit = {"type": "integer", "description": "Maximum number of results to return", "default": 50}
    params_ts = {"type": "string", "description": "Timestamp of the message", "required": True}
    
    # 1. Messaging (12 tools)
    tools.extend([
        {
            "name": "send_message",
            "description": "Sends a message to a channel or user.",
            "parameters": {
                "channel_id": {"type": "string", "required": True},
                "text": {"type": "string", "required": True},
                "attachments": {"type": "array", "items": {"type": "object"}},
                "thread_ts": {"type": "string", "description": "Provide to reply to a thread"}
            }
        },
        {
            "name": "edit_message",
            "description": "Updates an existing message.",
            "parameters": {
                "channel_id": {"type": "string", "required": True},
                "ts": params_ts,
                "text": {"type": "string", "required": True}
            }
        },
        {
            "name": "delete_message",
            "description": "Deletes a message.",
            "parameters": {
                "channel_id": {"type": "string", "required": True},
                "ts": params_ts
            }
        },
        {
            "name": "get_conversation_history",
            "description": "Fetches a page of messages from a channel.",
            "parameters": {
                "channel_id": {"type": "string", "required": True},
                "limit": params_limit,
                "latest": {"type": "string", "description": "End of time range"},
                "oldest": {"type": "string", "description": "Start of time range"}
            }
        },
        {
            "name": "add_reaction",
            "description": "Adds an emoji reaction to a message.",
            "parameters": {
                "channel_id": {"type": "string", "required": True},
                "ts": params_ts,
                "name": {"type": "string", "required": True, "description": "Emoji name (e.g., thumbsup)"}
            }
        },
        {
            "name": "remove_reaction",
            "description": "Removes an emoji reaction from a message.",
            "parameters": {
                "channel_id": {"type": "string", "required": True},
                "ts": params_ts,
                "name": {"type": "string", "required": True}
            }
        },
        {
            "name": "get_reactions",
            "description": "Lists reactions on a message.",
            "parameters": {
                "channel_id": {"type": "string", "required": True},
                "ts": params_ts
            }
        },
        {
            "name": "pin_message",
            "description": "Pins a message to the channel.",
            "parameters": {
                "channel_id": {"type": "string", "required": True},
                "ts": params_ts
            }
        },
        {
            "name": "unpin_message",
            "description": "Unpins a message from the channel.",
            "parameters": {
                "channel_id": {"type": "string", "required": True},
                "ts": params_ts
            }
        },
        {
            "name": "list_pinned_messages",
            "description": "Lists all pinned messages in a channel.",
            "parameters": {"channel_id": {"type": "string", "required": True}}
        },
        {
            "name": "schedule_message",
            "description": "Schedules a message to be sent at a later time.",
            "parameters": {
                "channel_id": {"type": "string", "required": True},
                "text": {"type": "string", "required": True},
                "post_at": {"type": "integer", "required": True, "description": "Unix timestamp"}
            }
        },
        {
            "name": "list_scheduled_messages",
            "description": "Lists pending scheduled messages.",
            "parameters": {
                "channel_id": {"type": "string"},
                "limit": params_limit
            }
        }
    ])

    # 2. Channels & Groups (10 tools)
    tools.extend([
        {
            "name": "create_channel",
            "description": "Creates a new public or private channel.",
            "parameters": {
                "name": {"type": "string", "required": True},
                "is_private": {"type": "boolean", "default": False},
                "description": {"type": "string"}
            }
        },
        {
            "name": "archive_channel",
            "description": "Archives a channel.",
            "parameters": {"channel_id": {"type": "string", "required": True}}
        },
        {
            "name": "invite_to_channel",
            "description": "Invites users to a channel.",
            "parameters": {
                "channel_id": {"type": "string", "required": True},
                "user_ids": {"type": "array", "items": {"type": "string"}, "required": True}
            }
        },
        {
            "name": "kick_from_channel",
            "description": "Removes a user from a channel.",
            "parameters": {
                "channel_id": {"type": "string", "required": True},
                "user_id": {"type": "string", "required": True}
            }
        },
        {
            "name": "join_channel",
            "description": "Joins an existing channel.",
            "parameters": {"channel_id": {"type": "string", "required": True}}
        },
        {
            "name": "leave_channel",
            "description": "Leaves a channel.",
            "parameters": {"channel_id": {"type": "string", "required": True}}
        },
        {
            "name": "list_channels",
            "description": "Lists all channels in the workspace.",
            "parameters": {
                "types": {"type": "string", "default": "public_channel,private_channel"},
                "limit": params_limit
            }
        },
        {
            "name": "get_channel_info",
            "description": "Retrieves information about a channel.",
            "parameters": {"channel_id": {"type": "string", "required": True}}
        },
        {
            "name": "set_channel_topic",
            "description": "Sets the topic or purpose of a channel.",
            "parameters": {
                "channel_id": {"type": "string", "required": True},
                "topic": {"type": "string", "required": True}
            }
        },
        {
            "name": "list_channel_members",
            "description": "Lists users in a channel.",
            "parameters": {
                "channel_id": {"type": "string", "required": True},
                "limit": params_limit
            }
        }
    ])

    # 3. Users & Status (8 tools)
    tools.extend([
        {
            "name": "get_user_profile",
            "description": "Retrieves a user's profile information.",
            "parameters": {"user_id": {"type": "string", "required": True}}
        },
        {
            "name": "set_user_status",
            "description": "Sets the user's status emoji and text.",
            "parameters": {
                "status_text": {"type": "string"},
                "status_emoji": {"type": "string"},
                "status_expiration": {"type": "integer"}
            }
        },
        {
            "name": "set_presence",
            "description": "Manually sets the user's presence (auto or away).",
            "parameters": {"presence": {"type": "string", "enum": ["auto", "away"], "required": True}}
        },
        {
            "name": "list_users",
            "description": "Lists all users in the workspace.",
            "parameters": {"limit": params_limit}
        },
        {
            "name": "lookup_user_by_email",
            "description": "Finds a user by their email address.",
            "parameters": {"email": {"type": "string", "required": True}}
        },
        {
            "name": "get_user_presence",
            "description": "Gets the online status of a user.",
            "parameters": {"user_id": {"type": "string", "required": True}}
        },
        {
            "name": "create_user_group",
            "description": "Creates a new user group.",
            "parameters": {
                "name": {"type": "string", "required": True},
                "handle": {"type": "string", "required": True}
            }
        },
        {
            "name": "update_user_group",
            "description": "Updates an existing user group.",
            "parameters": {
                "user_group_id": {"type": "string", "required": True},
                "name": {"type": "string"},
                "handle": {"type": "string"}
            }
        }
    ])

    # 4. Search & Files (5 tools)
    tools.extend([
        {
            "name": "search_messages",
            "description": "Searches for messages matching a query.",
            "parameters": {
                "query": {"type": "string", "required": True},
                "sort": {"type": "string", "default": "score"},
                "count": params_limit
            }
        },
        {
            "name": "search_files",
            "description": "Searches for files matching a query.",
            "parameters": {
                "query": {"type": "string", "required": True},
                "sort": {"type": "string", "default": "score"},
                "count": params_limit
            }
        },
        {
            "name": "upload_file",
            "description": "Uploads or creates a file.",
            "parameters": {
                "channels": {"type": "string", "description": "Comma-separated list of channel IDs"},
                "content": {"type": "string"},
                "filename": {"type": "string"},
                "filetype": {"type": "string"}
            }
        },
        {
            "name": "delete_file",
            "description": "Deletes a file.",
            "parameters": {"file_id": {"type": "string", "required": True}}
        },
        {
            "name": "get_file_info",
            "description": "Retrieves information about a file.",
            "parameters": {"file_id": {"type": "string", "required": True}}
        }
    ])

    # 5. Admin & Apps (5 tools)
    tools.extend([
        {
            "name": "auth_test",
            "description": "Checks authentication and returns identity.",
            "parameters": {}
        },
        {
            "name": "list_apps",
            "description": "Lists installed apps in the workspace.",
            "parameters": {}
        },
        {
            "name": "uninstall_app",
            "description": "Uninstalls an app.",
            "parameters": {
                "app_id": {"type": "string", "required": True},
                "client_id": {"type": "string"}
            }
        },
        {
            "name": "get_team_info",
            "description": "Retrieves information about the current workspace.",
            "parameters": {}
        },
        {
            "name": "get_billable_info",
            "description": "Retrieves billable usage information for users.",
            "parameters": {"user_id": {"type": "string"}}
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
        "server_name": "communication-mcp-server",
        "file_path": "synthetic/comm_server.py",
        "language": "python",
        "total_tools": len(final_tools),
        "total_schema_tokens": sum(t['estimated_tokens'] for t in final_tools),
        "complexity": "medium",
        "tools": final_tools
    }

if __name__ == "__main__":
    server_data = generate_comm_server()
    output_path = "synthetic_data/comm_server.json"
    
    with open(output_path, "w") as f:
        json.dump(server_data, f, indent=2)
        
    print(f"Generated {len(server_data['tools'])} tools in {output_path}")
