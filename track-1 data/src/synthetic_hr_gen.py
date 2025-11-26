import json
import os

def generate_hr_server():
    tools = []
    
    # Common parameter definitions
    params_id = {"type": "string", "description": "Unique identifier of the record", "required": True}
    params_limit = {"type": "integer", "description": "Maximum number of results to return", "default": 50}
    
    # 1. Employee Management (10 tools)
    tools.extend([
        {
            "name": "get_employee_profile",
            "description": "Retrieves the full profile of an employee including personal and job details.",
            "parameters": {"employee_id": params_id}
        },
        {
            "name": "create_employee",
            "description": "Onboards a new employee into the system.",
            "parameters": {
                "first_name": {"type": "string", "required": True},
                "last_name": {"type": "string", "required": True},
                "email": {"type": "string", "required": True},
                "start_date": {"type": "string", "format": "date", "required": True},
                "job_title": {"type": "string", "required": True},
                "department": {"type": "string", "required": True}
            }
        },
        {
            "name": "update_employee_job",
            "description": "Updates an employee's job information (e.g., promotion, transfer).",
            "parameters": {
                "employee_id": params_id,
                "new_title": {"type": "string"},
                "new_department": {"type": "string"},
                "new_manager_id": {"type": "string"},
                "effective_date": {"type": "string", "format": "date", "required": True}
            }
        },
        {
            "name": "terminate_employee",
            "description": "Processes an employee termination.",
            "parameters": {
                "employee_id": params_id,
                "termination_date": {"type": "string", "format": "date", "required": True},
                "reason": {"type": "string", "enum": ["Voluntary", "Involuntary", "Retirement"], "required": True},
                "eligible_for_rehire": {"type": "boolean", "default": True}
            }
        },
        {
            "name": "search_employees",
            "description": "Searches for employees by name, department, or location.",
            "parameters": {
                "query": {"type": "string", "required": True},
                "department": {"type": "string"},
                "location": {"type": "string"},
                "active_only": {"type": "boolean", "default": True}
            }
        },
        {
            "name": "get_org_chart",
            "description": "Retrieves the direct reports and manager for a given employee.",
            "parameters": {"employee_id": params_id}
        },
        {
            "name": "update_personal_info",
            "description": "Updates an employee's personal contact information.",
            "parameters": {
                "employee_id": params_id,
                "address": {"type": "string"},
                "phone_number": {"type": "string"},
                "emergency_contact": {"type": "string"}
            }
        },
        {
            "name": "get_employment_history",
            "description": "Retrieves the history of job changes and compensation for an employee.",
            "parameters": {"employee_id": params_id}
        },
        {
            "name": "verify_employment",
            "description": "Generates an employment verification letter.",
            "parameters": {
                "employee_id": params_id,
                "include_salary": {"type": "boolean", "default": False},
                "addressee": {"type": "string", "description": "Who the letter is addressed to"}
            }
        },
        {
            "name": "list_department_members",
            "description": "Lists all employees in a specific department.",
            "parameters": {
                "department_id": {"type": "string", "required": True},
                "limit": params_limit
            }
        }
    ])

    # 2. Time & Absence (8 tools)
    tools.extend([
        {
            "name": "submit_time_off_request",
            "description": "Submits a request for time off (vacation, sick leave, etc.).",
            "parameters": {
                "employee_id": params_id,
                "start_date": {"type": "string", "format": "date", "required": True},
                "end_date": {"type": "string", "format": "date", "required": True},
                "type": {"type": "string", "enum": ["Vacation", "Sick", "Personal", "Jury Duty"], "required": True},
                "comments": {"type": "string"}
            }
        },
        {
            "name": "approve_time_off",
            "description": "Approves or rejects a time off request.",
            "parameters": {
                "request_id": params_id,
                "approver_id": {"type": "string", "required": True},
                "status": {"type": "string", "enum": ["Approved", "Rejected"], "required": True},
                "rejection_reason": {"type": "string"}
            }
        },
        {
            "name": "get_time_off_balance",
            "description": "Checks the remaining time off balance for an employee.",
            "parameters": {
                "employee_id": params_id,
                "as_of_date": {"type": "string", "format": "date"}
            }
        },
        {
            "name": "submit_timesheet",
            "description": "Submits a weekly timesheet for hourly employees.",
            "parameters": {
                "employee_id": params_id,
                "week_start_date": {"type": "string", "format": "date", "required": True},
                "hours_worked": {"type": "number", "required": True},
                "project_codes": {"type": "object", "description": "Map of project ID to hours"}
            }
        },
        {
            "name": "get_team_absence_calendar",
            "description": "Retrieves the absence schedule for a manager's team.",
            "parameters": {
                "manager_id": params_id,
                "start_date": {"type": "string", "format": "date", "required": True},
                "end_date": {"type": "string", "format": "date", "required": True}
            }
        },
        {
            "name": "cancel_time_off_request",
            "description": "Cancels a previously submitted time off request.",
            "parameters": {"request_id": params_id}
        },
        {
            "name": "adjust_time_balance",
            "description": "Manually adjusts an employee's time off balance (Admin only).",
            "parameters": {
                "employee_id": params_id,
                "type": {"type": "string", "required": True},
                "adjustment_hours": {"type": "number", "required": True},
                "reason": {"type": "string", "required": True}
            }
        },
        {
            "name": "list_pending_approvals",
            "description": "Lists all time off and timesheet requests waiting for approval.",
            "parameters": {"approver_id": params_id}
        }
    ])

    # 3. Compensation & Payroll (8 tools)
    tools.extend([
        {
            "name": "get_payslip",
            "description": "Retrieves a specific payslip for an employee.",
            "parameters": {
                "employee_id": params_id,
                "pay_period_end_date": {"type": "string", "format": "date", "required": True}
            }
        },
        {
            "name": "update_salary_band",
            "description": "Updates the salary band/grade for a job profile.",
            "parameters": {
                "job_profile_id": {"type": "string", "required": True},
                "min_salary": {"type": "number", "required": True},
                "max_salary": {"type": "number", "required": True},
                "currency": {"type": "string", "default": "USD"}
            }
        },
        {
            "name": "award_bonus",
            "description": "Grants a one-time bonus to an employee.",
            "parameters": {
                "employee_id": params_id,
                "amount": {"type": "number", "required": True},
                "reason": {"type": "string", "required": True},
                "payout_date": {"type": "string", "format": "date"}
            }
        },
        {
            "name": "update_direct_deposit",
            "description": "Updates an employee's bank account information for payroll.",
            "parameters": {
                "employee_id": params_id,
                "bank_name": {"type": "string", "required": True},
                "account_number": {"type": "string", "required": True},
                "routing_number": {"type": "string", "required": True}
            }
        },
        {
            "name": "get_compensation_history",
            "description": "Retrieves the history of salary changes and bonuses.",
            "parameters": {"employee_id": params_id}
        },
        {
            "name": "generate_payroll_report",
            "description": "Generates a summary report for a pay period.",
            "parameters": {
                "pay_period_id": {"type": "string", "required": True},
                "department_id": {"type": "string"}
            }
        },
        {
            "name": "update_tax_withholding",
            "description": "Updates an employee's tax withholding elections (e.g., W-4).",
            "parameters": {
                "employee_id": params_id,
                "filing_status": {"type": "string", "required": True},
                "allowances": {"type": "integer", "required": True}
            }
        },
        {
            "name": "get_total_rewards_statement",
            "description": "Generates a statement showing total compensation including benefits.",
            "parameters": {
                "employee_id": params_id,
                "year": {"type": "integer", "required": True}
            }
        }
    ])

    # 4. Recruiting & Talent (8 tools)
    tools.extend([
        {
            "name": "list_open_positions",
            "description": "Lists all open job requisitions.",
            "parameters": {
                "department": {"type": "string"},
                "location": {"type": "string"},
                "status": {"type": "string", "default": "Open"}
            }
        },
        {
            "name": "create_job_requisition",
            "description": "Opens a new job requisition for hiring.",
            "parameters": {
                "job_title": {"type": "string", "required": True},
                "hiring_manager_id": {"type": "string", "required": True},
                "headcount": {"type": "integer", "default": 1},
                "description": {"type": "string", "required": True}
            }
        },
        {
            "name": "get_candidate_profile",
            "description": "Retrieves details about a job candidate.",
            "parameters": {"candidate_id": params_id}
        },
        {
            "name": "schedule_interview",
            "description": "Schedules an interview with a candidate.",
            "parameters": {
                "candidate_id": params_id,
                "interviewer_ids": {"type": "array", "items": {"type": "string"}, "required": True},
                "start_time": {"type": "string", "format": "datetime", "required": True},
                "duration_minutes": {"type": "integer", "default": 60}
            }
        },
        {
            "name": "submit_interview_feedback",
            "description": "Submits feedback and a rating for a candidate interview.",
            "parameters": {
                "interview_id": {"type": "string", "required": True},
                "interviewer_id": {"type": "string", "required": True},
                "rating": {"type": "integer", "min": 1, "max": 5, "required": True},
                "comments": {"type": "string", "required": True},
                "recommendation": {"type": "string", "enum": ["Hire", "No Hire", "Strong Hire"], "required": True}
            }
        },
        {
            "name": "extend_offer",
            "description": "Generates and sends a job offer to a candidate.",
            "parameters": {
                "candidate_id": params_id,
                "requisition_id": {"type": "string", "required": True},
                "start_date": {"type": "string", "format": "date", "required": True},
                "salary": {"type": "number", "required": True}
            }
        },
        {
            "name": "update_candidate_status",
            "description": "Moves a candidate to a different stage (e.g., Screen, Interview, Offer).",
            "parameters": {
                "candidate_id": params_id,
                "status": {"type": "string", "required": True}
            }
        },
        {
            "name": "search_candidates",
            "description": "Searches the candidate database by skills or experience.",
            "parameters": {
                "skills": {"type": "array", "items": {"type": "string"}},
                "min_experience_years": {"type": "integer"}
            }
        }
    ])

    # 5. Benefits & Performance (6 tools)
    tools.extend([
        {
            "name": "enroll_in_benefits",
            "description": "Enrolls an employee in a benefits plan.",
            "parameters": {
                "employee_id": params_id,
                "plan_id": {"type": "string", "required": True},
                "coverage_level": {"type": "string", "enum": ["Employee Only", "Employee + Spouse", "Family"], "required": True}
            }
        },
        {
            "name": "get_current_benefits",
            "description": "Retrieves an employee's current benefit elections.",
            "parameters": {"employee_id": params_id}
        },
        {
            "name": "create_performance_review",
            "description": "Initiates a performance review cycle for an employee.",
            "parameters": {
                "employee_id": params_id,
                "period_start": {"type": "string", "format": "date", "required": True},
                "period_end": {"type": "string", "format": "date", "required": True},
                "type": {"type": "string", "enum": ["Annual", "Mid-Year", "Probation"], "default": "Annual"}
            }
        },
        {
            "name": "submit_self_evaluation",
            "description": "Submits the employee's self-evaluation for a review.",
            "parameters": {
                "review_id": {"type": "string", "required": True},
                "content": {"type": "string", "required": True}
            }
        },
        {
            "name": "submit_manager_evaluation",
            "description": "Submits the manager's evaluation and rating.",
            "parameters": {
                "review_id": {"type": "string", "required": True},
                "rating": {"type": "string", "required": True},
                "comments": {"type": "string", "required": True}
            }
        },
        {
            "name": "get_performance_history",
            "description": "Retrieves past performance review ratings and documents.",
            "parameters": {"employee_id": params_id}
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
        "server_name": "hr-management-mcp-server",
        "file_path": "synthetic/hr_server.py",
        "language": "python",
        "total_tools": len(final_tools),
        "total_schema_tokens": sum(t['estimated_tokens'] for t in final_tools),
        "complexity": "medium",
        "tools": final_tools
    }

if __name__ == "__main__":
    server_data = generate_hr_server()
    output_path = "synthetic_data/hr_server.json"
    
    with open(output_path, "w") as f:
        json.dump(server_data, f, indent=2)
        
    print(f"Generated {len(server_data['tools'])} tools in {output_path}")
