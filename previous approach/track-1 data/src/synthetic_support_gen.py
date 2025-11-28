import json
import os

def generate_support_server():
    tools = []
    
    # Common parameter definitions
    params_id = {"type": "string", "description": "Unique identifier of the record", "required": True}
    params_limit = {"type": "integer", "description": "Maximum number of results to return", "default": 50}
    
    # 1. Ticket Management (15 tools)
    tools.extend([
        {
            "name": "create_ticket",
            "description": "Creates a new support ticket.",
            "parameters": {
                "subject": {"type": "string", "required": True},
                "description": {"type": "string", "required": True},
                "requester_email": {"type": "string", "required": True},
                "priority": {"type": "string", "enum": ["low", "normal", "high", "urgent"], "default": "normal"},
                "tags": {"type": "array", "items": {"type": "string"}}
            }
        },
        {
            "name": "get_ticket",
            "description": "Retrieves details of a ticket.",
            "parameters": {"ticket_id": params_id}
        },
        {
            "name": "update_ticket",
            "description": "Updates ticket properties.",
            "parameters": {
                "ticket_id": params_id,
                "status": {"type": "string", "enum": ["open", "pending", "solved", "closed"]},
                "priority": {"type": "string"},
                "assignee_id": {"type": "string"}
            }
        },
        {
            "name": "add_ticket_comment",
            "description": "Adds a comment to a ticket.",
            "parameters": {
                "ticket_id": params_id,
                "body": {"type": "string", "required": True},
                "public": {"type": "boolean", "default": True, "description": "True for public reply, False for internal note"}
            }
        },
        {
            "name": "list_ticket_comments",
            "description": "Lists comments on a ticket.",
            "parameters": {"ticket_id": params_id}
        },
        {
            "name": "search_tickets",
            "description": "Searches for tickets using a query string.",
            "parameters": {
                "query": {"type": "string", "required": True},
                "status": {"type": "string"},
                "limit": params_limit
            }
        },
        {
            "name": "delete_ticket",
            "description": "Permanently deletes a ticket.",
            "parameters": {"ticket_id": params_id}
        },
        {
            "name": "merge_tickets",
            "description": "Merges one ticket into another.",
            "parameters": {
                "source_ticket_id": {"type": "string", "required": True},
                "target_ticket_id": {"type": "string", "required": True}
            }
        },
        {
            "name": "get_ticket_metrics",
            "description": "Retrieves metrics for a ticket (e.g., reply time).",
            "parameters": {"ticket_id": params_id}
        },
        {
            "name": "list_tickets_by_user",
            "description": "Lists tickets requested by a specific user.",
            "parameters": {
                "user_id": {"type": "string", "required": True},
                "status": {"type": "string"}
            }
        },
        {
            "name": "assign_ticket",
            "description": "Assigns a ticket to an agent or group.",
            "parameters": {
                "ticket_id": params_id,
                "assignee_id": {"type": "string"},
                "group_id": {"type": "string"}
            }
        },
        {
            "name": "escalate_ticket",
            "description": "Escalates a ticket to a higher tier.",
            "parameters": {
                "ticket_id": params_id,
                "reason": {"type": "string", "required": True},
                "tier": {"type": "string", "required": True}
            }
        },
        {
            "name": "mark_as_spam",
            "description": "Marks a ticket as spam.",
            "parameters": {"ticket_id": params_id}
        },
        {
            "name": "restore_ticket",
            "description": "Restores a deleted ticket.",
            "parameters": {"ticket_id": params_id}
        },
        {
            "name": "get_ticket_audit_logs",
            "description": "Retrieves the audit log for a ticket.",
            "parameters": {"ticket_id": params_id}
        }
    ])

    # 2. Customer/User Management (8 tools)
    tools.extend([
        {
            "name": "create_user",
            "description": "Creates a new end-user or agent.",
            "parameters": {
                "name": {"type": "string", "required": True},
                "email": {"type": "string", "required": True},
                "role": {"type": "string", "enum": ["end-user", "agent", "admin"], "default": "end-user"}
            }
        },
        {
            "name": "get_user",
            "description": "Retrieves user details.",
            "parameters": {"user_id": params_id}
        },
        {
            "name": "update_user",
            "description": "Updates user information.",
            "parameters": {
                "user_id": params_id,
                "name": {"type": "string"},
                "phone": {"type": "string"},
                "notes": {"type": "string"}
            }
        },
        {
            "name": "search_users",
            "description": "Searches for users by name or email.",
            "parameters": {
                "query": {"type": "string", "required": True},
                "role": {"type": "string"}
            }
        },
        {
            "name": "delete_user",
            "description": "Deletes a user.",
            "parameters": {"user_id": params_id}
        },
        {
            "name": "merge_users",
            "description": "Merges a duplicate user into a primary user.",
            "parameters": {
                "source_user_id": {"type": "string", "required": True},
                "target_user_id": {"type": "string", "required": True}
            }
        },
        {
            "name": "get_user_identities",
            "description": "Lists identities (email, phone, etc.) for a user.",
            "parameters": {"user_id": params_id}
        },
        {
            "name": "suspend_user",
            "description": "Suspends a user's access.",
            "parameters": {
                "user_id": params_id,
                "reason": {"type": "string"}
            }
        }
    ])

    # 3. Knowledge Base (Help Center) (10 tools)
    tools.extend([
        {
            "name": "create_article",
            "description": "Creates a new knowledge base article.",
            "parameters": {
                "title": {"type": "string", "required": True},
                "body": {"type": "string", "required": True},
                "section_id": {"type": "string", "required": True},
                "locale": {"type": "string", "default": "en-us"}
            }
        },
        {
            "name": "get_article",
            "description": "Retrieves an article.",
            "parameters": {"article_id": params_id}
        },
        {
            "name": "update_article",
            "description": "Updates an existing article.",
            "parameters": {
                "article_id": params_id,
                "title": {"type": "string"},
                "body": {"type": "string"},
                "draft": {"type": "boolean"}
            }
        },
        {
            "name": "search_articles",
            "description": "Searches the knowledge base.",
            "parameters": {
                "query": {"type": "string", "required": True},
                "category_id": {"type": "string"},
                "locale": {"type": "string"}
            }
        },
        {
            "name": "delete_article",
            "description": "Deletes an article.",
            "parameters": {"article_id": params_id}
        },
        {
            "name": "list_sections",
            "description": "Lists sections within a category.",
            "parameters": {"category_id": {"type": "string", "required": True}}
        },
        {
            "name": "list_categories",
            "description": "Lists help center categories.",
            "parameters": {"locale": {"type": "string", "default": "en-us"}}
        },
        {
            "name": "create_translation",
            "description": "Creates a translation for an article.",
            "parameters": {
                "article_id": params_id,
                "locale": {"type": "string", "required": True},
                "title": {"type": "string", "required": True},
                "body": {"type": "string", "required": True}
            }
        },
        {
            "name": "vote_article",
            "description": "Adds a helpful/not helpful vote to an article.",
            "parameters": {
                "article_id": params_id,
                "vote": {"type": "string", "enum": ["up", "down"], "required": True}
            }
        },
        {
            "name": "list_article_comments",
            "description": "Lists comments on an article.",
            "parameters": {"article_id": params_id}
        }
    ])

    # 4. Chat & Messaging (7 tools)
    tools.extend([
        {
            "name": "start_chat_session",
            "description": "Initiates a new chat session.",
            "parameters": {
                "visitor_email": {"type": "string", "required": True},
                "department": {"type": "string"}
            }
        },
        {
            "name": "send_chat_message",
            "description": "Sends a message in a chat session.",
            "parameters": {
                "session_id": {"type": "string", "required": True},
                "message": {"type": "string", "required": True},
                "sender_type": {"type": "string", "enum": ["agent", "visitor"], "required": True}
            }
        },
        {
            "name": "end_chat_session",
            "description": "Ends an active chat session.",
            "parameters": {"session_id": {"type": "string", "required": True}}
        },
        {
            "name": "get_chat_history",
            "description": "Retrieves the transcript of a chat session.",
            "parameters": {"session_id": {"type": "string", "required": True}}
        },
        {
            "name": "list_active_chats",
            "description": "Lists currently active chat sessions.",
            "parameters": {"department": {"type": "string"}}
        },
        {
            "name": "ban_visitor",
            "description": "Bans a visitor from chat.",
            "parameters": {
                "visitor_id": {"type": "string", "required": True},
                "reason": {"type": "string"}
            }
        },
        {
            "name": "send_offline_message",
            "description": "Sends a message to support when no agents are online.",
            "parameters": {
                "email": {"type": "string", "required": True},
                "message": {"type": "string", "required": True}
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
        "server_name": "customer-support-mcp-server",
        "file_path": "synthetic/support_server.py",
        "language": "python",
        "total_tools": len(final_tools),
        "total_schema_tokens": sum(t['estimated_tokens'] for t in final_tools),
        "complexity": "medium",
        "tools": final_tools
    }

if __name__ == "__main__":
    server_data = generate_support_server()
    output_path = "synthetic_data/support_server.json"
    
    with open(output_path, "w") as f:
        json.dump(server_data, f, indent=2)
        
    print(f"Generated {len(server_data['tools'])} tools in {output_path}")
