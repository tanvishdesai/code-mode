import json
import os

def generate_devops_server():
    tools = []
    
    # Common parameter definitions
    params_id = {"type": "string", "description": "Unique identifier of the resource", "required": True}
    params_limit = {"type": "integer", "description": "Maximum number of results to return", "default": 50}
    params_env = {"type": "string", "description": "Target environment (e.g., production, staging)", "required": True}
    
    # 1. CI/CD Pipelines (12 tools)
    tools.extend([
        {
            "name": "trigger_pipeline",
            "description": "Triggers a new pipeline run.",
            "parameters": {
                "pipeline_id": {"type": "string", "required": True},
                "branch": {"type": "string", "default": "main"},
                "variables": {"type": "object", "description": "Environment variables for the run"}
            }
        },
        {
            "name": "get_pipeline_status",
            "description": "Retrieves the status of a pipeline run.",
            "parameters": {"run_id": params_id}
        },
        {
            "name": "list_pipelines",
            "description": "Lists defined pipelines in a project.",
            "parameters": {
                "project_id": {"type": "string", "required": True},
                "limit": params_limit
            }
        },
        {
            "name": "cancel_pipeline",
            "description": "Cancels a running pipeline.",
            "parameters": {"run_id": params_id}
        },
        {
            "name": "get_build_logs",
            "description": "Retrieves the logs for a specific build job.",
            "parameters": {
                "job_id": {"type": "string", "required": True},
                "offset": {"type": "integer", "default": 0}
            }
        },
        {
            "name": "retry_pipeline",
            "description": "Retries a failed pipeline run.",
            "parameters": {"run_id": params_id}
        },
        {
            "name": "create_pipeline_schedule",
            "description": "Schedules a pipeline to run periodically.",
            "parameters": {
                "pipeline_id": {"type": "string", "required": True},
                "cron_expression": {"type": "string", "required": True},
                "description": {"type": "string"}
            }
        },
        {
            "name": "list_pipeline_schedules",
            "description": "Lists schedules for a pipeline.",
            "parameters": {"pipeline_id": {"type": "string", "required": True}}
        },
        {
            "name": "delete_pipeline_schedule",
            "description": "Deletes a pipeline schedule.",
            "parameters": {"schedule_id": params_id}
        },
        {
            "name": "approve_deployment",
            "description": "Approves a manual deployment step.",
            "parameters": {
                "run_id": {"type": "string", "required": True},
                "environment": params_env,
                "comment": {"type": "string"}
            }
        },
        {
            "name": "get_test_report",
            "description": "Retrieves test results for a pipeline run.",
            "parameters": {"run_id": params_id}
        },
        {
            "name": "get_coverage_report",
            "description": "Retrieves code coverage statistics.",
            "parameters": {"run_id": params_id}
        }
    ])

    # 2. Infrastructure as Code (8 tools)
    tools.extend([
        {
            "name": "plan_infrastructure",
            "description": "Generates an execution plan for infrastructure changes.",
            "parameters": {
                "stack_id": {"type": "string", "required": True},
                "template_body": {"type": "string"},
                "parameters": {"type": "object"}
            }
        },
        {
            "name": "apply_infrastructure",
            "description": "Applies infrastructure changes.",
            "parameters": {
                "stack_id": {"type": "string", "required": True},
                "plan_id": {"type": "string"}
            }
        },
        {
            "name": "destroy_infrastructure",
            "description": "Tears down infrastructure resources.",
            "parameters": {
                "stack_id": {"type": "string", "required": True},
                "force": {"type": "boolean", "default": False}
            }
        },
        {
            "name": "get_stack_status",
            "description": "Retrieves the current status of an infrastructure stack.",
            "parameters": {"stack_id": params_id}
        },
        {
            "name": "get_stack_outputs",
            "description": "Retrieves output values from a stack.",
            "parameters": {"stack_id": params_id}
        },
        {
            "name": "validate_template",
            "description": "Validates an IaC template for syntax errors.",
            "parameters": {
                "template_body": {"type": "string", "required": True},
                "type": {"type": "string", "enum": ["terraform", "cloudformation"], "default": "terraform"}
            }
        },
        {
            "name": "list_stacks",
            "description": "Lists all infrastructure stacks.",
            "parameters": {"limit": params_limit}
        },
        {
            "name": "drift_detection",
            "description": "Checks for drift between state and actual infrastructure.",
            "parameters": {"stack_id": params_id}
        }
    ])

    # 3. Artifact Registry (6 tools)
    tools.extend([
        {
            "name": "list_repositories",
            "description": "Lists artifact repositories.",
            "parameters": {"limit": params_limit}
        },
        {
            "name": "list_artifacts",
            "description": "Lists packages/images in a repository.",
            "parameters": {
                "repository_id": {"type": "string", "required": True},
                "limit": params_limit
            }
        },
        {
            "name": "get_artifact_metadata",
            "description": "Retrieves metadata for a specific artifact version.",
            "parameters": {
                "repository_id": {"type": "string", "required": True},
                "artifact_id": {"type": "string", "required": True},
                "version": {"type": "string", "required": True}
            }
        },
        {
            "name": "delete_artifact_version",
            "description": "Deletes a specific version of an artifact.",
            "parameters": {
                "repository_id": {"type": "string", "required": True},
                "artifact_id": {"type": "string", "required": True},
                "version": {"type": "string", "required": True}
            }
        },
        {
            "name": "scan_artifact",
            "description": "Triggers a security scan on an artifact.",
            "parameters": {
                "repository_id": {"type": "string", "required": True},
                "artifact_id": {"type": "string", "required": True},
                "version": {"type": "string", "required": True}
            }
        },
        {
            "name": "get_scan_results",
            "description": "Retrieves results of a security scan.",
            "parameters": {"scan_id": params_id}
        }
    ])

    # 4. Monitoring & Observability (8 tools)
    tools.extend([
        {
            "name": "get_metric_data",
            "description": "Retrieves time-series data for a metric.",
            "parameters": {
                "metric_name": {"type": "string", "required": True},
                "start_time": {"type": "string", "format": "datetime", "required": True},
                "end_time": {"type": "string", "format": "datetime", "required": True},
                "dimensions": {"type": "object"}
            }
        },
        {
            "name": "list_alerts",
            "description": "Lists active alerts.",
            "parameters": {
                "status": {"type": "string", "enum": ["firing", "resolved"]},
                "severity": {"type": "string"}
            }
        },
        {
            "name": "acknowledge_alert",
            "description": "Acknowledges an alert.",
            "parameters": {
                "alert_id": params_id,
                "user_id": {"type": "string", "required": True}
            }
        },
        {
            "name": "create_dashboard",
            "description": "Creates a new monitoring dashboard.",
            "parameters": {
                "name": {"type": "string", "required": True},
                "widgets": {"type": "array", "items": {"type": "object"}}
            }
        },
        {
            "name": "query_logs",
            "description": "Queries log data.",
            "parameters": {
                "query": {"type": "string", "required": True},
                "start_time": {"type": "string", "format": "datetime"},
                "end_time": {"type": "string", "format": "datetime"},
                "limit": params_limit
            }
        },
        {
            "name": "create_alert_rule",
            "description": "Creates a new alerting rule.",
            "parameters": {
                "name": {"type": "string", "required": True},
                "condition": {"type": "string", "required": True},
                "threshold": {"type": "number", "required": True},
                "duration_minutes": {"type": "integer", "default": 5}
            }
        },
        {
            "name": "list_services",
            "description": "Lists monitored services and their health status.",
            "parameters": {"limit": params_limit}
        },
        {
            "name": "get_service_health",
            "description": "Retrieves detailed health information for a service.",
            "parameters": {"service_id": params_id}
        }
    ])

    # 5. Secrets Management (6 tools)
    tools.extend([
        {
            "name": "get_secret",
            "description": "Retrieves a secret value.",
            "parameters": {
                "name": {"type": "string", "required": True},
                "version": {"type": "string"}
            }
        },
        {
            "name": "set_secret",
            "description": "Creates or updates a secret.",
            "parameters": {
                "name": {"type": "string", "required": True},
                "value": {"type": "string", "required": True},
                "description": {"type": "string"}
            }
        },
        {
            "name": "list_secrets",
            "description": "Lists available secrets.",
            "parameters": {"limit": params_limit}
        },
        {
            "name": "delete_secret",
            "description": "Deletes a secret.",
            "parameters": {"name": {"type": "string", "required": True}}
        },
        {
            "name": "rotate_secret",
            "description": "Triggers rotation for a secret.",
            "parameters": {"name": {"type": "string", "required": True}}
        },
        {
            "name": "get_secret_metadata",
            "description": "Retrieves metadata about a secret (not the value).",
            "parameters": {"name": {"type": "string", "required": True}}
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
        "server_name": "devops-mcp-server",
        "file_path": "synthetic/devops_server.py",
        "language": "python",
        "total_tools": len(final_tools),
        "total_schema_tokens": sum(t['estimated_tokens'] for t in final_tools),
        "complexity": "high",
        "tools": final_tools
    }

if __name__ == "__main__":
    server_data = generate_devops_server()
    output_path = "synthetic_data/devops_server.json"
    
    with open(output_path, "w") as f:
        json.dump(server_data, f, indent=2)
        
    print(f"Generated {len(server_data['tools'])} tools in {output_path}")
