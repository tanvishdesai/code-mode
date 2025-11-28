import json
import os
import random

def generate_crm_server():
    tools = []
    
    # Common parameter definitions to reuse
    params_id = {"type": "string", "description": "Unique identifier of the record", "required": True}
    params_limit = {"type": "integer", "description": "Maximum number of results to return", "default": 50}
    params_offset = {"type": "integer", "description": "Offset for pagination", "default": 0}
    
    # 1. Lead Management (10 tools)
    tools.extend([
        {
            "name": "create_lead",
            "description": "Creates a new lead in the CRM system with basic contact information.",
            "parameters": {
                "first_name": {"type": "string", "required": True},
                "last_name": {"type": "string", "required": True},
                "email": {"type": "string", "required": True},
                "company": {"type": "string", "required": True},
                "source": {"type": "string", "description": "Lead source (e.g., Web, Referral)", "default": "Web"}
            }
        },
        {
            "name": "get_lead",
            "description": "Retrieves detailed information about a specific lead by ID.",
            "parameters": {"lead_id": params_id}
        },
        {
            "name": "update_lead_status",
            "description": "Updates the status of a lead (e.g., New, Contacted, Qualified, Lost).",
            "parameters": {
                "lead_id": params_id,
                "status": {"type": "string", "enum": ["New", "Contacted", "Qualified", "Unqualified"], "required": True}
            }
        },
        {
            "name": "convert_lead",
            "description": "Converts a qualified lead into a contact, account, and opportunity.",
            "parameters": {
                "lead_id": params_id,
                "opportunity_name": {"type": "string", "required": True},
                "owner_id": {"type": "string", "description": "ID of the user who will own the new records"}
            }
        },
        {
            "name": "search_leads",
            "description": "Searches for leads based on criteria like name, company, or email.",
            "parameters": {
                "query": {"type": "string", "required": True},
                "limit": params_limit
            }
        },
        {
            "name": "delete_lead",
            "description": "Permanently removes a lead record.",
            "parameters": {"lead_id": params_id}
        },
        {
            "name": "assign_lead",
            "description": "Assigns a lead to a specific sales representative.",
            "parameters": {
                "lead_id": params_id,
                "user_id": {"type": "string", "required": True, "description": "ID of the sales rep"}
            }
        },
        {
            "name": "get_lead_history",
            "description": "Retrieves the activity history and changes for a lead.",
            "parameters": {"lead_id": params_id}
        },
        {
            "name": "merge_leads",
            "description": "Merges duplicate leads into a single record.",
            "parameters": {
                "master_lead_id": params_id,
                "duplicate_lead_id": {"type": "string", "required": True}
            }
        },
        {
            "name": "export_leads",
            "description": "Exports a list of leads to a CSV file based on a filter.",
            "parameters": {
                "filter_id": {"type": "string", "description": "ID of the saved filter view"},
                "format": {"type": "string", "default": "csv"}
            }
        }
    ])

    # 2. Opportunity Management (10 tools)
    tools.extend([
        {
            "name": "create_opportunity",
            "description": "Creates a new sales opportunity.",
            "parameters": {
                "name": {"type": "string", "required": True},
                "account_id": {"type": "string", "required": True},
                "close_date": {"type": "string", "format": "date", "required": True},
                "stage": {"type": "string", "required": True},
                "amount": {"type": "number"}
            }
        },
        {
            "name": "update_opportunity_stage",
            "description": "Moves an opportunity to a different stage in the sales pipeline.",
            "parameters": {
                "opportunity_id": params_id,
                "stage_name": {"type": "string", "required": True},
                "probability": {"type": "integer", "description": "Win probability percentage"}
            }
        },
        {
            "name": "add_opportunity_product",
            "description": "Adds a product line item to an opportunity.",
            "parameters": {
                "opportunity_id": params_id,
                "product_id": {"type": "string", "required": True},
                "quantity": {"type": "integer", "required": True},
                "price": {"type": "number", "required": True}
            }
        },
        {
            "name": "get_opportunity_products",
            "description": "Lists all products associated with an opportunity.",
            "parameters": {"opportunity_id": params_id}
        },
        {
            "name": "list_opportunities",
            "description": "Lists opportunities, optionally filtered by account or owner.",
            "parameters": {
                "account_id": {"type": "string"},
                "owner_id": {"type": "string"},
                "limit": params_limit
            }
        },
        {
            "name": "get_opportunity_forecast",
            "description": "Calculates the revenue forecast based on opportunity stages and probabilities.",
            "parameters": {
                "quarter": {"type": "string", "description": "e.g., 2024-Q1"},
                "user_id": {"type": "string"}
            }
        },
        {
            "name": "close_opportunity",
            "description": "Marks an opportunity as Closed Won or Closed Lost.",
            "parameters": {
                "opportunity_id": params_id,
                "is_won": {"type": "boolean", "required": True},
                "reason": {"type": "string", "description": "Reason for win/loss"}
            }
        },
        {
            "name": "share_opportunity",
            "description": "Grants access to an opportunity to another user or team.",
            "parameters": {
                "opportunity_id": params_id,
                "user_or_group_id": {"type": "string", "required": True},
                "access_level": {"type": "string", "enum": ["Read", "Edit"], "default": "Read"}
            }
        },
        {
            "name": "clone_opportunity",
            "description": "Creates a copy of an existing opportunity.",
            "parameters": {
                "opportunity_id": params_id,
                "include_products": {"type": "boolean", "default": True}
            }
        },
        {
            "name": "get_opportunity_timeline",
            "description": "Retrieves the timeline of stage changes and activities for an opportunity.",
            "parameters": {"opportunity_id": params_id}
        }
    ])

    # 3. Account & Contact Management (10 tools)
    tools.extend([
        {
            "name": "create_account",
            "description": "Registers a new business account.",
            "parameters": {
                "name": {"type": "string", "required": True},
                "industry": {"type": "string"},
                "website": {"type": "string"},
                "phone": {"type": "string"}
            }
        },
        {
            "name": "get_account_hierarchy",
            "description": "Retrieves the parent-child relationship hierarchy for an account.",
            "parameters": {"account_id": params_id}
        },
        {
            "name": "update_account_address",
            "description": "Updates the billing or shipping address of an account.",
            "parameters": {
                "account_id": params_id,
                "street": {"type": "string"},
                "city": {"type": "string"},
                "state": {"type": "string"},
                "postal_code": {"type": "string"},
                "country": {"type": "string"},
                "type": {"type": "string", "enum": ["Billing", "Shipping"], "default": "Billing"}
            }
        },
        {
            "name": "create_contact",
            "description": "Adds a new contact person to an account.",
            "parameters": {
                "account_id": {"type": "string", "required": True},
                "first_name": {"type": "string", "required": True},
                "last_name": {"type": "string", "required": True},
                "email": {"type": "string"},
                "title": {"type": "string"}
            }
        },
        {
            "name": "search_contacts",
            "description": "Finds contacts across all accounts.",
            "parameters": {
                "query": {"type": "string", "required": True},
                "email_domain": {"type": "string"}
            }
        },
        {
            "name": "link_contact_to_opportunity",
            "description": "Associates a contact with an opportunity as a contact role (e.g., Decision Maker).",
            "parameters": {
                "opportunity_id": {"type": "string", "required": True},
                "contact_id": {"type": "string", "required": True},
                "role": {"type": "string", "default": "Influencer"}
            }
        },
        {
            "name": "get_account_team",
            "description": "Lists the internal team members working on an account.",
            "parameters": {"account_id": params_id}
        },
        {
            "name": "add_account_team_member",
            "description": "Adds a user to the account team.",
            "parameters": {
                "account_id": params_id,
                "user_id": {"type": "string", "required": True},
                "role": {"type": "string"}
            }
        },
        {
            "name": "merge_accounts",
            "description": "Merges two account records.",
            "parameters": {
                "master_account_id": params_id,
                "duplicate_account_id": {"type": "string", "required": True}
            }
        },
        {
            "name": "get_nearby_accounts",
            "description": "Finds accounts located within a specific radius of a location.",
            "parameters": {
                "latitude": {"type": "number", "required": True},
                "longitude": {"type": "number", "required": True},
                "radius_km": {"type": "number", "default": 10}
            }
        }
    ])

    # 4. Activity & Task Management (10 tools)
    tools.extend([
        {
            "name": "log_call",
            "description": "Logs a phone call activity against a record.",
            "parameters": {
                "related_to_id": {"type": "string", "description": "ID of lead, contact, or opportunity", "required": True},
                "subject": {"type": "string", "default": "Call"},
                "notes": {"type": "string"},
                "duration_seconds": {"type": "integer"}
            }
        },
        {
            "name": "create_task",
            "description": "Creates a task or to-do item.",
            "parameters": {
                "subject": {"type": "string", "required": True},
                "due_date": {"type": "string", "format": "date"},
                "priority": {"type": "string", "enum": ["High", "Normal", "Low"], "default": "Normal"},
                "assigned_to": {"type": "string"}
            }
        },
        {
            "name": "complete_task",
            "description": "Marks a task as completed.",
            "parameters": {"task_id": params_id}
        },
        {
            "name": "schedule_meeting",
            "description": "Schedules a meeting and sends invites.",
            "parameters": {
                "subject": {"type": "string", "required": True},
                "start_time": {"type": "string", "format": "datetime", "required": True},
                "end_time": {"type": "string", "format": "datetime", "required": True},
                "attendees": {"type": "array", "items": {"type": "string"}, "description": "List of email addresses"}
            }
        },
        {
            "name": "list_my_tasks",
            "description": "Lists open tasks assigned to the current user.",
            "parameters": {
                "status": {"type": "string", "default": "Open"},
                "overdue_only": {"type": "boolean", "default": False}
            }
        },
        {
            "name": "log_email",
            "description": "Logs an email sent outside the system.",
            "parameters": {
                "related_to_id": {"type": "string", "required": True},
                "subject": {"type": "string", "required": True},
                "body": {"type": "string"},
                "sent_at": {"type": "string", "format": "datetime"}
            }
        },
        {
            "name": "get_activity_timeline",
            "description": "Gets a consolidated timeline of all calls, emails, and meetings for a record.",
            "parameters": {"record_id": params_id}
        },
        {
            "name": "create_recurring_task",
            "description": "Creates a series of recurring tasks.",
            "parameters": {
                "subject": {"type": "string", "required": True},
                "frequency": {"type": "string", "enum": ["Daily", "Weekly", "Monthly"], "required": True},
                "end_date": {"type": "string", "format": "date"}
            }
        },
        {
            "name": "assign_task_queue",
            "description": "Assigns a task to a queue instead of a specific user.",
            "parameters": {
                "task_id": params_id,
                "queue_id": {"type": "string", "required": True}
            }
        },
        {
            "name": "get_overdue_tasks",
            "description": "Retrieves all overdue tasks for a team.",
            "parameters": {"team_id": {"type": "string", "required": True}}
        }
    ])

    # 5. Reports & Dashboards (5 tools)
    tools.extend([
        {
            "name": "run_report",
            "description": "Executes a pre-defined report and returns the data.",
            "parameters": {
                "report_id": params_id,
                "filters": {"type": "object", "description": "Dynamic filters to apply"}
            }
        },
        {
            "name": "list_dashboards",
            "description": "Lists available dashboards.",
            "parameters": {"folder_id": {"type": "string"}}
        },
        {
            "name": "get_dashboard_components",
            "description": "Retrieves the metadata for components on a dashboard.",
            "parameters": {"dashboard_id": params_id}
        },
        {
            "name": "export_report",
            "description": "Exports report data to Excel or CSV.",
            "parameters": {
                "report_id": params_id,
                "format": {"type": "string", "enum": ["csv", "xlsx"], "default": "csv"}
            }
        },
        {
            "name": "subscribe_to_report",
            "description": "Subscribes a user to receive report updates via email.",
            "parameters": {
                "report_id": params_id,
                "frequency": {"type": "string", "default": "Weekly"}
            }
        }
    ])

    # 6. Admin & Setup (5 tools)
    tools.extend([
        {
            "name": "get_users",
            "description": "Lists active users in the CRM.",
            "parameters": {"role_id": {"type": "string"}}
        },
        {
            "name": "create_custom_field",
            "description": "Adds a custom field to a standard object.",
            "parameters": {
                "object_name": {"type": "string", "required": True},
                "field_name": {"type": "string", "required": True},
                "field_type": {"type": "string", "enum": ["Text", "Number", "Date", "Picklist"], "required": True}
            }
        },
        {
            "name": "get_system_info",
            "description": "Retrieves system usage and limit information.",
            "parameters": {}
        },
        {
            "name": "manage_permission_set",
            "description": "Assigns or removes a permission set for a user.",
            "parameters": {
                "user_id": {"type": "string", "required": True},
                "permission_set_id": {"type": "string", "required": True},
                "action": {"type": "string", "enum": ["assign", "remove"], "required": True}
            }
        },
        {
            "name": "audit_login_history",
            "description": "Retrieves login history for security auditing.",
            "parameters": {
                "user_id": {"type": "string"},
                "start_date": {"type": "string", "format": "date"}
            }
        }
    ])

    # Post-processing to match schema
    final_tools = []
    for t in tools:
        # Calculate estimated tokens (rough heuristic)
        # Name + Desc + Params
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
        "server_name": "enterprise-crm-mcp-server",
        "file_path": "synthetic/crm_server.py",
        "language": "python",
        "total_tools": len(final_tools),
        "total_schema_tokens": sum(t['estimated_tokens'] for t in final_tools),
        "complexity": "medium",
        "tools": final_tools
    }

if __name__ == "__main__":
    server_data = generate_crm_server()
    output_path = "synthetic_data/crm_server.json"
    
    with open(output_path, "w") as f:
        json.dump(server_data, f, indent=2)
        
    print(f"Generated {len(server_data['tools'])} tools in {output_path}")
