import json
import os

def generate_payments_server():
    tools = []
    
    # Common parameter definitions
    params_id = {"type": "string", "description": "Unique identifier of the record", "required": True}
    params_limit = {"type": "integer", "description": "Maximum number of results to return", "default": 50}
    params_currency = {"type": "string", "default": "usd", "description": "Three-letter ISO currency code"}
    
    # 1. Payment Processing (10 tools)
    tools.extend([
        {
            "name": "create_charge",
            "description": "Creates a new payment charge.",
            "parameters": {
                "amount": {"type": "integer", "required": True, "description": "Amount in cents"},
                "currency": params_currency,
                "source": {"type": "string", "required": True, "description": "Token or payment source ID"},
                "description": {"type": "string"},
                "capture": {"type": "boolean", "default": True}
            }
        },
        {
            "name": "get_charge",
            "description": "Retrieves details of a charge.",
            "parameters": {"charge_id": params_id}
        },
        {
            "name": "update_charge",
            "description": "Updates a charge (e.g., description, metadata).",
            "parameters": {
                "charge_id": params_id,
                "description": {"type": "string"},
                "metadata": {"type": "object"}
            }
        },
        {
            "name": "capture_charge",
            "description": "Captures a previously uncaptured charge.",
            "parameters": {
                "charge_id": params_id,
                "amount": {"type": "integer", "description": "Amount to capture (if less than authorized)"}
            }
        },
        {
            "name": "create_refund",
            "description": "Refunds a charge.",
            "parameters": {
                "charge_id": {"type": "string", "required": True},
                "amount": {"type": "integer", "description": "Amount to refund (default is full)"},
                "reason": {"type": "string", "enum": ["duplicate", "fraudulent", "requested_by_customer"]}
            }
        },
        {
            "name": "get_refund",
            "description": "Retrieves details of a refund.",
            "parameters": {"refund_id": params_id}
        },
        {
            "name": "list_charges",
            "description": "Lists charges filtering by customer or date.",
            "parameters": {
                "customer_id": {"type": "string"},
                "limit": params_limit,
                "created_gte": {"type": "integer", "description": "Timestamp"}
            }
        },
        {
            "name": "create_payment_intent",
            "description": "Creates a payment intent for a future payment.",
            "parameters": {
                "amount": {"type": "integer", "required": True},
                "currency": params_currency,
                "payment_method_types": {"type": "array", "items": {"type": "string"}}
            }
        },
        {
            "name": "confirm_payment_intent",
            "description": "Confirms a payment intent to finalize payment.",
            "parameters": {
                "intent_id": params_id,
                "payment_method": {"type": "string"}
            }
        },
        {
            "name": "cancel_payment_intent",
            "description": "Cancels a payment intent.",
            "parameters": {"intent_id": params_id}
        }
    ])

    # 2. Customers & Payment Methods (8 tools)
    tools.extend([
        {
            "name": "create_customer",
            "description": "Creates a new customer record.",
            "parameters": {
                "email": {"type": "string", "required": True},
                "name": {"type": "string"},
                "phone": {"type": "string"},
                "payment_method": {"type": "string", "description": "ID of default payment method"}
            }
        },
        {
            "name": "get_customer",
            "description": "Retrieves customer details.",
            "parameters": {"customer_id": params_id}
        },
        {
            "name": "update_customer",
            "description": "Updates customer information.",
            "parameters": {
                "customer_id": params_id,
                "email": {"type": "string"},
                "default_source": {"type": "string"}
            }
        },
        {
            "name": "delete_customer",
            "description": "Deletes a customer.",
            "parameters": {"customer_id": params_id}
        },
        {
            "name": "list_customers",
            "description": "Lists customers.",
            "parameters": {
                "email": {"type": "string"},
                "limit": params_limit
            }
        },
        {
            "name": "attach_payment_method",
            "description": "Attaches a payment method to a customer.",
            "parameters": {
                "payment_method_id": {"type": "string", "required": True},
                "customer_id": {"type": "string", "required": True}
            }
        },
        {
            "name": "detach_payment_method",
            "description": "Detaches a payment method from a customer.",
            "parameters": {"payment_method_id": params_id}
        },
        {
            "name": "list_payment_methods",
            "description": "Lists payment methods for a customer.",
            "parameters": {
                "customer_id": {"type": "string", "required": True},
                "type": {"type": "string", "required": True}
            }
        }
    ])

    # 3. Subscriptions (10 tools)
    tools.extend([
        {
            "name": "create_product",
            "description": "Creates a product for subscription.",
            "parameters": {
                "name": {"type": "string", "required": True},
                "type": {"type": "string", "enum": ["service", "good"], "default": "service"}
            }
        },
        {
            "name": "create_price",
            "description": "Creates a price for a product.",
            "parameters": {
                "product_id": {"type": "string", "required": True},
                "unit_amount": {"type": "integer", "required": True},
                "currency": params_currency,
                "recurring": {"type": "object", "description": "Interval details (e.g., month)"}
            }
        },
        {
            "name": "create_subscription",
            "description": "Subscribes a customer to a price.",
            "parameters": {
                "customer_id": {"type": "string", "required": True},
                "items": {"type": "array", "items": {"type": "object"}, "required": True}
            }
        },
        {
            "name": "get_subscription",
            "description": "Retrieves subscription details.",
            "parameters": {"subscription_id": params_id}
        },
        {
            "name": "update_subscription",
            "description": "Updates a subscription (e.g., change plan).",
            "parameters": {
                "subscription_id": params_id,
                "items": {"type": "array", "items": {"type": "object"}},
                "cancel_at_period_end": {"type": "boolean"}
            }
        },
        {
            "name": "cancel_subscription",
            "description": "Cancels a subscription.",
            "parameters": {"subscription_id": params_id}
        },
        {
            "name": "list_subscriptions",
            "description": "Lists active subscriptions.",
            "parameters": {
                "customer_id": {"type": "string"},
                "status": {"type": "string", "default": "active"},
                "limit": params_limit
            }
        },
        {
            "name": "create_coupon",
            "description": "Creates a discount coupon.",
            "parameters": {
                "percent_off": {"type": "number"},
                "amount_off": {"type": "integer"},
                "duration": {"type": "string", "enum": ["once", "repeating", "forever"], "required": True}
            }
        },
        {
            "name": "delete_coupon",
            "description": "Deletes a coupon.",
            "parameters": {"coupon_id": params_id}
        },
        {
            "name": "apply_discount",
            "description": "Applies a discount to a customer or subscription.",
            "parameters": {
                "customer_id": {"type": "string"},
                "subscription_id": {"type": "string"},
                "coupon_id": {"type": "string", "required": True}
            }
        }
    ])

    # 4. Invoices & Disputes (7 tools)
    tools.extend([
        {
            "name": "create_invoice",
            "description": "Creates a draft invoice.",
            "parameters": {
                "customer_id": {"type": "string", "required": True},
                "collection_method": {"type": "string", "default": "charge_automatically"}
            }
        },
        {
            "name": "finalize_invoice",
            "description": "Finalizes a draft invoice.",
            "parameters": {"invoice_id": params_id}
        },
        {
            "name": "pay_invoice",
            "description": "Pays an invoice.",
            "parameters": {
                "invoice_id": params_id,
                "payment_method": {"type": "string"}
            }
        },
        {
            "name": "void_invoice",
            "description": "Voids an invoice.",
            "parameters": {"invoice_id": params_id}
        },
        {
            "name": "get_invoice",
            "description": "Retrieves an invoice.",
            "parameters": {"invoice_id": params_id}
        },
        {
            "name": "list_invoices",
            "description": "Lists invoices.",
            "parameters": {
                "customer_id": {"type": "string"},
                "status": {"type": "string"},
                "limit": params_limit
            }
        },
        {
            "name": "list_disputes",
            "description": "Lists disputes filed by cardholders.",
            "parameters": {
                "status": {"type": "string"},
                "limit": params_limit
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
        "server_name": "payments-mcp-server",
        "file_path": "synthetic/payments_server.py",
        "language": "python",
        "total_tools": len(final_tools),
        "total_schema_tokens": sum(t['estimated_tokens'] for t in final_tools),
        "complexity": "medium",
        "tools": final_tools
    }

if __name__ == "__main__":
    server_data = generate_payments_server()
    output_path = "synthetic_data/payments_server.json"
    
    with open(output_path, "w") as f:
        json.dump(server_data, f, indent=2)
        
    print(f"Generated {len(server_data['tools'])} tools in {output_path}")
