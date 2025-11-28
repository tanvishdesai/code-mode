import json
import os

def generate_pm_server():
    tools = []
    
    # Common parameter definitions
    params_id = {"type": "string", "description": "Unique identifier of the record", "required": True}
    params_limit = {"type": "integer", "description": "Maximum number of results to return", "default": 50}
    params_key = {"type": "string", "description": "Project key or issue key (e.g., PROJ-123)", "required": True}
    
    # 1. Issue Tracking (15 tools)
    tools.extend([
        {
            "name": "create_issue",
            "description": "Creates a new issue or ticket.",
            "parameters": {
                "project_key": {"type": "string", "required": True},
                "summary": {"type": "string", "required": True},
                "issue_type": {"type": "string", "enum": ["Story", "Bug", "Task", "Epic"], "required": True},
                "description": {"type": "string"},
                "priority": {"type": "string", "default": "Medium"},
                "assignee_id": {"type": "string"}
            }
        },
        {
            "name": "get_issue",
            "description": "Retrieves details of a specific issue.",
            "parameters": {"issue_key": params_key}
        },
        {
            "name": "update_issue",
            "description": "Updates fields of an existing issue.",
            "parameters": {
                "issue_key": params_key,
                "summary": {"type": "string"},
                "description": {"type": "string"},
                "priority": {"type": "string"},
                "labels": {"type": "array", "items": {"type": "string"}}
            }
        },
        {
            "name": "transition_issue",
            "description": "Changes the status of an issue (e.g., To Do -> In Progress).",
            "parameters": {
                "issue_key": params_key,
                "transition_id": {"type": "string", "required": True},
                "comment": {"type": "string"}
            }
        },
        {
            "name": "assign_issue",
            "description": "Assigns an issue to a user.",
            "parameters": {
                "issue_key": params_key,
                "assignee_id": {"type": "string", "required": True}
            }
        },
        {
            "name": "search_issues",
            "description": "Searches for issues using JQL (Jira Query Language).",
            "parameters": {
                "jql": {"type": "string", "required": True},
                "start_at": {"type": "integer", "default": 0},
                "max_results": params_limit
            }
        },
        {
            "name": "delete_issue",
            "description": "Permanently deletes an issue.",
            "parameters": {"issue_key": params_key}
        },
        {
            "name": "link_issues",
            "description": "Creates a link between two issues (e.g., Blocks, Relates to).",
            "parameters": {
                "inward_issue_key": params_key,
                "outward_issue_key": {"type": "string", "required": True},
                "link_type": {"type": "string", "required": True}
            }
        },
        {
            "name": "add_attachment",
            "description": "Uploads a file attachment to an issue.",
            "parameters": {
                "issue_key": params_key,
                "filename": {"type": "string", "required": True},
                "content_base64": {"type": "string", "required": True}
            }
        },
        {
            "name": "get_issue_watchers",
            "description": "Lists users watching an issue.",
            "parameters": {"issue_key": params_key}
        },
        {
            "name": "add_watcher",
            "description": "Adds a user as a watcher to an issue.",
            "parameters": {
                "issue_key": params_key,
                "user_id": {"type": "string", "required": True}
            }
        },
        {
            "name": "log_work",
            "description": "Logs time spent working on an issue.",
            "parameters": {
                "issue_key": params_key,
                "time_spent_seconds": {"type": "integer", "required": True},
                "started": {"type": "string", "format": "datetime"},
                "comment": {"type": "string"}
            }
        },
        {
            "name": "get_worklogs",
            "description": "Retrieves worklogs for an issue.",
            "parameters": {"issue_key": params_key}
        },
        {
            "name": "vote_for_issue",
            "description": "Adds a vote to an issue.",
            "parameters": {"issue_key": params_key}
        },
        {
            "name": "get_issue_transitions",
            "description": "Returns a list of possible transitions for an issue.",
            "parameters": {"issue_key": params_key}
        }
    ])

    # 2. Agile & Scrum (10 tools)
    tools.extend([
        {
            "name": "create_sprint",
            "description": "Creates a new sprint for a board.",
            "parameters": {
                "board_id": {"type": "integer", "required": True},
                "name": {"type": "string", "required": True},
                "start_date": {"type": "string", "format": "datetime"},
                "end_date": {"type": "string", "format": "datetime"},
                "goal": {"type": "string"}
            }
        },
        {
            "name": "add_issues_to_sprint",
            "description": "Moves issues into a sprint.",
            "parameters": {
                "sprint_id": {"type": "integer", "required": True},
                "issue_keys": {"type": "array", "items": {"type": "string"}, "required": True}
            }
        },
        {
            "name": "start_sprint",
            "description": "Starts a planned sprint.",
            "parameters": {"sprint_id": {"type": "integer", "required": True}}
        },
        {
            "name": "complete_sprint",
            "description": "Completes an active sprint.",
            "parameters": {"sprint_id": {"type": "integer", "required": True}}
        },
        {
            "name": "get_sprint_issues",
            "description": "Lists issues in a specific sprint.",
            "parameters": {"sprint_id": {"type": "integer", "required": True}}
        },
        {
            "name": "get_backlog_issues",
            "description": "Lists issues in the backlog for a board.",
            "parameters": {"board_id": {"type": "integer", "required": True}}
        },
        {
            "name": "create_epic",
            "description": "Creates a new epic.",
            "parameters": {
                "project_key": {"type": "string", "required": True},
                "name": {"type": "string", "required": True},
                "summary": {"type": "string", "required": True}
            }
        },
        {
            "name": "add_issue_to_epic",
            "description": "Links an issue to an epic.",
            "parameters": {
                "issue_key": params_key,
                "epic_key": {"type": "string", "required": True}
            }
        },
        {
            "name": "get_epic_issues",
            "description": "Lists all issues belonging to an epic.",
            "parameters": {"epic_key": params_key}
        },
        {
            "name": "get_board_configuration",
            "description": "Retrieves the configuration of a board (columns, filters).",
            "parameters": {"board_id": {"type": "integer", "required": True}}
        }
    ])

    # 3. Comments & Collaboration (5 tools)
    tools.extend([
        {
            "name": "add_comment",
            "description": "Adds a comment to an issue.",
            "parameters": {
                "issue_key": params_key,
                "body": {"type": "string", "required": True},
                "visibility": {"type": "string", "description": "Group or Role to restrict visibility"}
            }
        },
        {
            "name": "get_comments",
            "description": "Retrieves comments for an issue.",
            "parameters": {"issue_key": params_key}
        },
        {
            "name": "update_comment",
            "description": "Edits an existing comment.",
            "parameters": {
                "issue_key": params_key,
                "comment_id": {"type": "string", "required": True},
                "body": {"type": "string", "required": True}
            }
        },
        {
            "name": "delete_comment",
            "description": "Deletes a comment.",
            "parameters": {
                "issue_key": params_key,
                "comment_id": {"type": "string", "required": True}
            }
        },
        {
            "name": "mention_user",
            "description": "Notifies a user in a comment.",
            "parameters": {
                "issue_key": params_key,
                "user_id": {"type": "string", "required": True},
                "message": {"type": "string"}
            }
        }
    ])

    # 4. Projects & Components (10 tools)
    tools.extend([
        {
            "name": "create_project",
            "description": "Creates a new project.",
            "parameters": {
                "key": {"type": "string", "required": True},
                "name": {"type": "string", "required": True},
                "lead_id": {"type": "string", "required": True},
                "template": {"type": "string", "default": "Scrum"}
            }
        },
        {
            "name": "get_project",
            "description": "Retrieves project details.",
            "parameters": {"project_key": params_key}
        },
        {
            "name": "create_component",
            "description": "Creates a new component within a project.",
            "parameters": {
                "project_key": params_key,
                "name": {"type": "string", "required": True},
                "description": {"type": "string"},
                "lead_id": {"type": "string"}
            }
        },
        {
            "name": "get_project_components",
            "description": "Lists components in a project.",
            "parameters": {"project_key": params_key}
        },
        {
            "name": "create_version",
            "description": "Creates a new release version.",
            "parameters": {
                "project_key": params_key,
                "name": {"type": "string", "required": True},
                "release_date": {"type": "string", "format": "date"}
            }
        },
        {
            "name": "get_project_versions",
            "description": "Lists versions/releases in a project.",
            "parameters": {"project_key": params_key}
        },
        {
            "name": "release_version",
            "description": "Marks a version as released.",
            "parameters": {
                "version_id": {"type": "string", "required": True},
                "release_date": {"type": "string", "format": "date", "required": True}
            }
        },
        {
            "name": "get_project_roles",
            "description": "Lists roles defined in a project.",
            "parameters": {"project_key": params_key}
        },
        {
            "name": "add_actor_to_role",
            "description": "Adds a user or group to a project role.",
            "parameters": {
                "project_key": params_key,
                "role_id": {"type": "string", "required": True},
                "user_id": {"type": "string"}
            }
        },
        {
            "name": "get_project_statuses",
            "description": "Lists valid statuses for issues in a project.",
            "parameters": {"project_key": params_key}
        }
    ])

    # 5. Dashboards & Filters (5 tools)
    tools.extend([
        {
            "name": "create_dashboard",
            "description": "Creates a new dashboard.",
            "parameters": {
                "name": {"type": "string", "required": True},
                "description": {"type": "string"},
                "share_permissions": {"type": "array", "items": {"type": "object"}}
            }
        },
        {
            "name": "get_dashboard",
            "description": "Retrieves a dashboard.",
            "parameters": {"dashboard_id": params_id}
        },
        {
            "name": "create_filter",
            "description": "Creates a saved JQL filter.",
            "parameters": {
                "name": {"type": "string", "required": True},
                "jql": {"type": "string", "required": True},
                "description": {"type": "string"}
            }
        },
        {
            "name": "get_filter",
            "description": "Retrieves a saved filter.",
            "parameters": {"filter_id": params_id}
        },
        {
            "name": "get_favourite_filters",
            "description": "Lists the current user's favourite filters.",
            "parameters": {}
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
        "server_name": "project-management-mcp-server",
        "file_path": "synthetic/pm_server.py",
        "language": "python",
        "total_tools": len(final_tools),
        "total_schema_tokens": sum(t['estimated_tokens'] for t in final_tools),
        "complexity": "medium",
        "tools": final_tools
    }

if __name__ == "__main__":
    server_data = generate_pm_server()
    output_path = "synthetic_data/pm_server.json"
    
    with open(output_path, "w") as f:
        json.dump(server_data, f, indent=2)
        
    print(f"Generated {len(server_data['tools'])} tools in {output_path}")
