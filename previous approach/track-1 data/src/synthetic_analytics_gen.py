import json
import os

def generate_analytics_server():
    tools = []
    
    # Common parameter definitions
    params_id = {"type": "string", "description": "Unique identifier of the resource", "required": True}
    params_limit = {"type": "integer", "description": "Maximum number of results to return", "default": 50}
    
    # 1. Data Querying (10 tools)
    tools.extend([
        {
            "name": "run_sql_query",
            "description": "Executes a raw SQL query against the data warehouse.",
            "parameters": {
                "sql": {"type": "string", "required": True},
                "limit": {"type": "integer", "default": 100},
                "timeout_seconds": {"type": "integer", "default": 60}
            }
        },
        {
            "name": "get_dataset_preview",
            "description": "Retrieves a preview of data from a dataset.",
            "parameters": {
                "dataset_id": params_id,
                "rows": {"type": "integer", "default": 10}
            }
        },
        {
            "name": "list_datasets",
            "description": "Lists available datasets/tables.",
            "parameters": {
                "schema": {"type": "string"},
                "limit": params_limit
            }
        },
        {
            "name": "get_dataset_schema",
            "description": "Retrieves the schema (columns, types) of a dataset.",
            "parameters": {"dataset_id": params_id}
        },
        {
            "name": "search_data",
            "description": "Searches for data across datasets using keywords.",
            "parameters": {
                "query": {"type": "string", "required": True},
                "limit": params_limit
            }
        },
        {
            "name": "explain_query",
            "description": "Returns the execution plan for a query.",
            "parameters": {"sql": {"type": "string", "required": True}}
        },
        {
            "name": "cancel_query",
            "description": "Cancels a running query.",
            "parameters": {"query_id": params_id}
        },
        {
            "name": "get_query_history",
            "description": "Retrieves a history of executed queries.",
            "parameters": {
                "user_id": {"type": "string"},
                "limit": params_limit
            }
        },
        {
            "name": "create_saved_query",
            "description": "Saves a query for future use.",
            "parameters": {
                "name": {"type": "string", "required": True},
                "sql": {"type": "string", "required": True},
                "description": {"type": "string"}
            }
        },
        {
            "name": "get_saved_query",
            "description": "Retrieves a saved query definition.",
            "parameters": {"query_id": params_id}
        }
    ])

    # 2. Dashboards & Visualizations (10 tools)
    tools.extend([
        {
            "name": "create_dashboard",
            "description": "Creates a new empty dashboard.",
            "parameters": {
                "name": {"type": "string", "required": True},
                "description": {"type": "string"},
                "folder_id": {"type": "string"}
            }
        },
        {
            "name": "get_dashboard",
            "description": "Retrieves dashboard metadata and layout.",
            "parameters": {"dashboard_id": params_id}
        },
        {
            "name": "add_tile_to_dashboard",
            "description": "Adds a visualization tile to a dashboard.",
            "parameters": {
                "dashboard_id": {"type": "string", "required": True},
                "visualization_type": {"type": "string", "required": True},
                "query_id": {"type": "string", "required": True},
                "layout": {"type": "object"}
            }
        },
        {
            "name": "update_dashboard_filter",
            "description": "Updates global filters on a dashboard.",
            "parameters": {
                "dashboard_id": {"type": "string", "required": True},
                "filters": {"type": "array", "items": {"type": "object"}}
            }
        },
        {
            "name": "list_dashboards",
            "description": "Lists available dashboards.",
            "parameters": {
                "folder_id": {"type": "string"},
                "limit": params_limit
            }
        },
        {
            "name": "delete_dashboard",
            "description": "Deletes a dashboard.",
            "parameters": {"dashboard_id": params_id}
        },
        {
            "name": "refresh_dashboard",
            "description": "Triggers a data refresh for a dashboard.",
            "parameters": {"dashboard_id": params_id}
        },
        {
            "name": "get_dashboard_screenshot",
            "description": "Generates a screenshot of a dashboard.",
            "parameters": {"dashboard_id": params_id}
        },
        {
            "name": "duplicate_dashboard",
            "description": "Creates a copy of a dashboard.",
            "parameters": {
                "dashboard_id": params_id,
                "new_name": {"type": "string", "required": True}
            }
        },
        {
            "name": "pin_dashboard",
            "description": "Pins a dashboard to the user's home screen.",
            "parameters": {"dashboard_id": params_id}
        }
    ])

    # 3. Reports & Exports (8 tools)
    tools.extend([
        {
            "name": "create_report_schedule",
            "description": "Schedules a report to be sent via email.",
            "parameters": {
                "dashboard_id": {"type": "string", "required": True},
                "cron_expression": {"type": "string", "required": True},
                "recipients": {"type": "array", "items": {"type": "string"}, "required": True},
                "format": {"type": "string", "enum": ["pdf", "csv", "png"], "default": "pdf"}
            }
        },
        {
            "name": "list_schedules",
            "description": "Lists active report schedules.",
            "parameters": {"limit": params_limit}
        },
        {
            "name": "delete_schedule",
            "description": "Deletes a report schedule.",
            "parameters": {"schedule_id": params_id}
        },
        {
            "name": "export_data",
            "description": "Exports query results to a file.",
            "parameters": {
                "query_id": {"type": "string", "required": True},
                "format": {"type": "string", "enum": ["csv", "json", "xlsx"], "required": True}
            }
        },
        {
            "name": "get_export_status",
            "description": "Checks the status of an asynchronous export.",
            "parameters": {"export_id": params_id}
        },
        {
            "name": "download_export",
            "description": "Downloads the exported file.",
            "parameters": {"export_id": params_id}
        },
        {
            "name": "send_report_now",
            "description": "Triggers an immediate send of a report.",
            "parameters": {
                "dashboard_id": {"type": "string", "required": True},
                "recipients": {"type": "array", "items": {"type": "string"}, "required": True}
            }
        },
        {
            "name": "get_report_history",
            "description": "Retrieves execution history of a report.",
            "parameters": {"schedule_id": params_id}
        }
    ])

    # 4. Data Modeling & Metrics (7 tools)
    tools.extend([
        {
            "name": "create_metric",
            "description": "Defines a new business metric.",
            "parameters": {
                "name": {"type": "string", "required": True},
                "sql_expression": {"type": "string", "required": True},
                "format": {"type": "string"}
            }
        },
        {
            "name": "list_metrics",
            "description": "Lists defined metrics.",
            "parameters": {"limit": params_limit}
        },
        {
            "name": "get_metric_definition",
            "description": "Retrieves the definition of a metric.",
            "parameters": {"metric_id": params_id}
        },
        {
            "name": "update_metric",
            "description": "Updates a metric definition.",
            "parameters": {
                "metric_id": params_id,
                "sql_expression": {"type": "string"},
                "description": {"type": "string"}
            }
        },
        {
            "name": "create_dimension",
            "description": "Defines a new dimension for slicing data.",
            "parameters": {
                "name": {"type": "string", "required": True},
                "sql_expression": {"type": "string", "required": True}
            }
        },
        {
            "name": "list_dimensions",
            "description": "Lists defined dimensions.",
            "parameters": {"limit": params_limit}
        },
        {
            "name": "validate_model",
            "description": "Validates the data model for consistency.",
            "parameters": {"model_id": params_id}
        }
    ])

    # 5. Access Control (5 tools)
    tools.extend([
        {
            "name": "grant_access",
            "description": "Grants access to a dashboard or dataset.",
            "parameters": {
                "resource_id": {"type": "string", "required": True},
                "user_email": {"type": "string", "required": True},
                "role": {"type": "string", "enum": ["viewer", "editor", "admin"], "required": True}
            }
        },
        {
            "name": "revoke_access",
            "description": "Revokes access to a resource.",
            "parameters": {
                "resource_id": {"type": "string", "required": True},
                "user_email": {"type": "string", "required": True}
            }
        },
        {
            "name": "list_resource_users",
            "description": "Lists users with access to a resource.",
            "parameters": {"resource_id": params_id}
        },
        {
            "name": "create_user_group",
            "description": "Creates a group of users for easier sharing.",
            "parameters": {
                "name": {"type": "string", "required": True}
            }
        },
        {
            "name": "add_user_to_group",
            "description": "Adds a user to a group.",
            "parameters": {
                "group_id": {"type": "string", "required": True},
                "user_email": {"type": "string", "required": True}
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
        "server_name": "analytics-mcp-server",
        "file_path": "synthetic/analytics_server.py",
        "language": "python",
        "total_tools": len(final_tools),
        "total_schema_tokens": sum(t['estimated_tokens'] for t in final_tools),
        "complexity": "high",
        "tools": final_tools
    }

if __name__ == "__main__":
    server_data = generate_analytics_server()
    output_path = "synthetic_data/analytics_server.json"
    
    with open(output_path, "w") as f:
        json.dump(server_data, f, indent=2)
        
    print(f"Generated {len(server_data['tools'])} tools in {output_path}")
