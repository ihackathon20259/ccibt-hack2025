from typing import Any, Dict, List, Optional
from google.cloud import bigquery
from google.cloud.bigquery import QueryJobConfig, ScalarQueryParameter
import datetime
import random
import time

# --- BigQuery Client Setup (Reusable) ---
def get_bigquery_client() -> bigquery.Client:
    """Get a configured BigQuery client."""
    # This project ID must be valid and linked to your ADC credentials
    return bigquery.Client(project="ccibt-hack25ww7-704")

# -------------------------------------------------------------------
# TOOL 1: Enhanced Historical Reporting (BigQuery)
# -------------------------------------------------------------------
def generate_wire_status_report(
    customer_id: str, 
    start_date: Optional[str] = None, 
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates a read-only historical report of wire statuses for a specific customer 
    for a given date range. If no dates are provided, it defaults to the last 30 days.
    
    Args:
        customer_id: The ID of the customer to report on (e.g., LUMN-5577).
        start_date: The start date for the report in YYYY-MM-DD format (optional).
        end_date: The end date for the report in YYYY-MM-DD format (optional).
    """

    # Default to last 30 days if no date range is provided for historical context
    if not start_date and not end_date:
        default_start = (datetime.date.today() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
        start_date = default_start
        end_date = datetime.date.today().strftime('%Y-%m-%d')
    
    # Build the base query
    query = """
    SELECT
      CustomerID,
      report_id,
      run_ts,
      status
    FROM ccibt-hack25ww7-704.client_report_data.report_event
    WHERE CustomerID = @customer_id
    """
    
    # Add date filtering
    if start_date:
        query += " AND DATE(run_ts) >= @start_date"
    if end_date:
        query += " AND DATE(run_ts) <= @end_date"
    
    # Define parameters (CRITICAL for BigQuery named parameters)
    query_params = [
        ScalarQueryParameter("customer_id", "STRING", customer_id),
    ]
    if start_date:
        query_params.append(ScalarQueryParameter("start_date", "DATE", start_date))
    if end_date:
        query_params.append(ScalarQueryParameter("end_date", "DATE", end_date))

    job_config = QueryJobConfig(query_parameters=query_params)
    client = get_bigquery_client()
    
    try:
        query_job = client.query(query, job_config=job_config)
        results = [dict(row) for row in query_job.result()]
    except Exception as e:
        # Return a structured error response
        return {"error": f"BigQuery execution failed: {e}", "query": query}

    return {
        "customer_id": customer_id,
        "date_range": f"{start_date or 'N/A'} to {end_date or 'N/A'}",
        "report_count": len(results),
        "report": results
    }

# -------------------------------------------------------------------
# TOOL 2: Real-Time Balance (BigQuery - Aggregated by CustomerID/UserID)
# -------------------------------------------------------------------
def get_intraday_balance(customer_id: str) -> Dict[str, Any]:
    """
    Retrieves the total aggregated Current and Available balance for a specific 
    customer/user across all their linked accounts by querying the 
    BigQuery intraday_transactions table.
    
    Args:
        customer_id: The ID of the user (e.g., USR-AstroZen) stored in the CustomerID column.
    """

    # The query is now modified to filter ONLY by CustomerID and GROUP BY ONLY CustomerID.
    query = """
    SELECT
      t.CustomerID AS customer_id,
      SUM(CASE WHEN t.PostedStatus IN ('POSTED', 'SOFT_POSTED') THEN t.Amount ELSE 0 END) AS current_balance,
      SUM(CASE WHEN t.PostedStatus = 'POSTED' THEN t.Amount ELSE 0 END) AS available_balance,
      MAX(t.TransactionTS) AS last_update_ts
    FROM ccibt-hack25ww7-704.client_report_data.AccountBalance AS t
    WHERE t.CustomerID = @customer_id
    GROUP BY 1
    """
    
    job_config = QueryJobConfig(
        query_parameters=[
            # Pass the customer_id argument to the SQL placeholder @customer_id
            ScalarQueryParameter("customer_id", "STRING", customer_id),
        ]
    )

    client = get_bigquery_client()
    
    try:
        query_job = client.query(query, job_config=job_config)
        row = next(query_job.result(), None)
        
        if not row or row['current_balance'] is None:
            return {"error": f"No data found or aggregated balance is zero for customer/user {customer_id}.", 
                    "customer_id": customer_id}
            
        return {
            "customer_id": row['customer_id'],
            # The balance is the aggregated sum across ALL accounts for this customer/user
            "current_balance_total": f"{row['current_balance']:.2f}",
            "available_balance_total": f"{row['available_balance']:.2f}",
            "last_update": row['last_update_ts'].isoformat() if row['last_update_ts'] else None,
            "status": "SUCCESS"
        }

    except Exception as e:
        return {"error": f"BigQuery execution failed: {e}", "customer_id": customer_id}

# -------------------------------------------------------------------
# TOOL 3: Document and Image Retrieval (Simulated DMS Search)
# -------------------------------------------------------------------
def retrieve_document_copy(
    transaction_id: Optional[str] = None, 
    check_number: Optional[str] = None,
    document_type: str = "TRANSACTION_IMAGE"
) -> Dict[str, Any]:
    """
    Searches the Document Management System (DMS) for an image or PDF copy 
    of a transaction, check, or payment document. Requires at least one identifier.
    
    NOTE: This simulates a call to a Document Management System API.
    """
    if not transaction_id and not check_number:
        return {"error": "Must provide either a transaction_id or a check_number to retrieve a document."}

    # --- SIMULATION ---
    search_key = check_number or transaction_id
    
    if search_key == "891472" or search_key.startswith("760995"):
        return {
            "status": "SUCCESS",
            "document_type": document_type,
            "id_searched": search_key,
            "retrieval_link": f"https://dms.bankname.com/view/{search_key}-{document_type}.pdf",
            "message": f"Successfully retrieved document for ID {search_key}. Link provided to customer via secure channel."
        }

    return {"status": "NOT_FOUND", "id_searched": search_key, "message": f"No document found for ID {search_key} in the archive."}


# -------------------------------------------------------------------
# TOOL 4: Workflow and Action (Simulated Payment Gateway)
# -------------------------------------------------------------------
def verify_ach_file(account_number_suffix: str, transaction_amount: float) -> Dict[str, Any]:
    """
    Initiates a check/verification on a pending ACH file based on the account suffix 
    and amount. Used to confirm if a file is ready for processing or has been approved.
    
    NOTE: This simulates a call to a Payment Gateway/Approval Workflow.
    """
    # --- SIMULATION ---
    if account_number_suffix == "8294" and transaction_amount == 41527.93:
        return {
            "verification_status": "APPROVED",
            "account_suffix": account_number_suffix,
            "amount": transaction_amount,
            "next_action": "File is scheduled for settlement (03/03/2025). No further action needed.",
            "source": "PaymentGatewayAPI (Simulated)"
        }
    
    return {
        "verification_status": "PENDING_REVIEW",
        "account_suffix": account_number_suffix,
        "amount": transaction_amount,
        "next_action": "Could not confirm automated approval. Requires manual review by Treasury Ops.",
        "source": "PaymentGatewayAPI (Simulated)"
    }
# -------------------------------------------------------------------
# TOOL 5: Detailed Single Wire Report (BigQuery)
# -------------------------------------------------------------------
def get_detailed_wire_report(report_id: str, customer_id: str) -> Dict[str, Any]:
    # 1. Clean the ID
    clean_id = customer_id.replace("USR-", "")
    
    # 2. Use placeholders (@variable) for BOTH parameters
    query = """
    SELECT
      t.*
    FROM `ccibt-hack25ww7-704.client_report_data.wire_report` AS t
    WHERE t.report_id = @report_id 
      AND t.SenderName = @sender_name
    LIMIT 1
    """
    
    # 3. Add both parameters to the list
    query_params = [
        ScalarQueryParameter("report_id", "STRING", report_id),
        ScalarQueryParameter("sender_name", "STRING", clean_id),
    ]

    job_config = QueryJobConfig(query_parameters=query_params)
    client = get_bigquery_client()
    
    try:
        query_job = client.query(query, job_config=job_config)
        results = query_job.result()
        row = next(results, None)
        
        if not row:
            return {"status": "NOT_FOUND", "message": f"No report found for {report_id}"}

        return {
            "status": "SUCCESS",
            "details": dict(row)
        }
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}
# --------------------------
# Customer Data
# --------------------------
Customer = {
    "shubham": "Bronze",
    "USR-AstroZen": "Gold",
    "USR-NebulaX": "Silver",
    "USR-ApolloX": "Gold",
    "USR-StellarQ": "Bronze",
    "USR-Galactiq": "Gold",
    "USR-OrionEdge": "Silver",
    "USR-Solarix": "Gold",
    "USR-Meteorix": "Gold",
    "USR-LunaSky": "Bronze",
    "USR-Cosmosia": "Silver"
}

PLANS = {
    "Bronze": {
        "included": {
            "General Balance PDF",
            "Reports",
            "Track",
            "Commercial Checking Statement",
            "Commercial Savings Statement",
            "Commercial Foreign Account Statement",
            "Customer Insight Statement",
            "Billable Notifications",
            "Non-Billable Notifications"
        },
        "optional": {
            "Reject Payments & Modify Notices",
            "Deposit Correction",
            "Account Balance Direct API"
        }
    },

    "Silver": {
        "included": {
            "General Balance PDF",
            "Previous Day Combined Balance Detail",
            "Track",
            "Detailed Reports",
            "Intraday Balance",
            "Image Basic",
            "Commercial Checking Statement",
            "Commercial Savings Statement",
            "Commercial Foreign Account Statement",
            "Customer Insight Statement",
            "Billable Notifications",
            "Non-Billable Notifications"
        },
        "optional": {
            "DDA Periodic Statement Non-PDF",
            "Reject Payments & Modify Notices",
            "Deposit Correction",
            "Account Balance Direct API",
            "Account Balance Portal",
            "Payment Detail Direct API",
            "Payment Detail Portal",
            "Image Expanded",
            "Payment Expanded Detail",
            "Yesterday Reports",
            "Transmitted EBS",
            "Direct BAI Standard",
            "Intraday Expanded Detail",
            "Direct BAI Premium",
            "Deposit Detail",
            "Present Day Reports",
            "History Expanded Detail",
            "Payments GBF"
        }
    },

    "Gold": {
        "included": {
            "General Balance PDF",
            "Previous Day Combined Balance Detail",
            "DDA Periodic Statement Non-PDF",
            "Track",
            "Image Basic",
            "Image Expanded",
            "Commercial Checking Statement",
            "Commercial Savings Statement",
            "Commercial Foreign Account Statement",
            "Customer Insight Statement",
            "Account Balance Direct API",
            "Account Balance Portal",
            "Payment Detail Direct API",
            "Payment Detail Portal",
            "Payment Expanded Detail",
            "Yesterday Reports",
            "Transmitted EBS",
            "Direct BAI Standard",
            "Intraday Expanded Detail",
            "Direct BAI Premium",
            "Deposit Detail",
            "Present Day Reports",
            "History Expanded Detail",
            "Payments GBF",
            "Billable Notifications",
            "Non-Billable Notifications",
            "Reject Payments & Modify Notices",
            "Deposit Correction"
        },
        "optional": set()
    }
}

FEATURE_SYNONYMS = {
    "General Balance PDF": ["general balance", "balance pdf", "daily balance"],
    "Previous Day Combined Balance Detail": ["previous day balance", "yesterday balance", "combined balance"],
    "Image Basic": ["check images", "cheque images", "deposit images"],
    "Image Expanded": ["expanded images", "all images"],
    "Intraday Expanded Detail": ["intraday balance", "real time balance", "live balance"],
    "Payment Expanded Detail": ["payment expanded", "detailed payment"],
    "Payments GBF": ["gbf", "gbf payments"],
    "Reports": ["wire reports"],
    "Detailed Reports": ["wire detailed reports"]
}

PLAN_HIERARCHY = ["Bronze", "Silver", "Gold"]

# --------------------------
# Helper Functions
# --------------------------
def extract_feature(user_query: str) -> str | None:
    query = user_query.lower()
    for canonical, phrases in FEATURE_SYNONYMS.items():
        for phrase in phrases:
            if phrase in query:
                return canonical
    return None

def extract_customer_id(user_query: str) -> str | None:
    query = user_query.lower()
    for customer_id in Customer.keys():
        if customer_id.lower() in query:
            return customer_id
    return None

def suggest_upgrade(current_plan: str) -> str | None:
    if current_plan not in PLAN_HIERARCHY:
        return None
    idx = PLAN_HIERARCHY.index(current_plan)
    if idx < len(PLAN_HIERARCHY) - 1:
        return PLAN_HIERARCHY[idx + 1]
    return None

# --------------------------
# Tools
# --------------------------
def check_eligibility(user_query: str):
    customer_id = extract_customer_id(user_query)
    if not customer_id:
        return {"error": "UNKNOWN_CUSTOMER", "message": "Could not identify customer from the query", "original_query": user_query}

    feature = extract_feature(user_query)
    if not feature:
        return {"error": "UNKNOWN_FEATURE", "message": "Could not confidently identify requested report/feature", "original_query": user_query}

    plan = Customer.get(customer_id)
    if plan not in PLANS:
        return {"error": "INVALID_PLAN", "message": "Unknown subscription plan"}

    plan_data = PLANS[plan]

    if feature in plan_data["included"]:
        status = "INCLUDED"
        message = "This report/feature is included in your plan."
        return {"customer_id": customer_id, "plan": plan, "requested_report": feature, "eligibility": status, "message": message}
    else:
        status = "OPTIONAL" if feature in plan_data["optional"] else "NOT_AVAILABLE"
        upgrade_plan = suggest_upgrade(plan)
        alert_message = f"⚠️ The requested report/feature '{feature}' is {status} for your current plan ({plan})."
        if upgrade_plan:
            alert_message += f" Consider upgrading to {upgrade_plan} to access this feature."
        else:
            alert_message += " No higher plan available."
        return {"customer_id": customer_id, "plan": plan, "requested_report": feature, "eligibility": status, "message": alert_message}

def get_customer_plan(user_query: str):
    customer_id = extract_customer_id(user_query)
    if not customer_id:
        return {"error": "UNKNOWN_CUSTOMER", "message": "Could not identify customer from the query", "original_query": user_query}

    plan = Customer.get(customer_id)
    if not plan:
        return {"error": "INVALID_PLAN", "message": "Customer plan not found"}

    return {"customer_id": customer_id, "current_plan": plan, "message": f"The current plan for {customer_id} is {plan}."}


def suggest_higher_plan_with_benefits(user_query: str):
    """
    Suggest the next higher plan along with the benefits the customer will get.
    """
    customer_id = extract_customer_id(user_query)
    if not customer_id:
        return {
            "error": "UNKNOWN_CUSTOMER",
            "message": "Could not identify customer from the query",
            "original_query": user_query
        }

    current_plan = Customer.get(customer_id)
    if not current_plan or current_plan not in PLAN_HIERARCHY:
        return {
            "error": "INVALID_PLAN",
            "message": "Customer plan not found or invalid"
        }

    # Determine next higher plan
    idx = PLAN_HIERARCHY.index(current_plan)
    if idx >= len(PLAN_HIERARCHY) - 1:
        return {
            "message": f"{customer_id} is already on the highest plan ({current_plan}). No higher plan available."
        }

    next_plan = PLAN_HIERARCHY[idx + 1]
    current_features = PLANS[current_plan]["included"].union(PLANS[current_plan]["optional"])
    next_plan_features = PLANS[next_plan]["included"].union(PLANS[next_plan]["optional"])
    
    # Only show features not already in current plan
    additional_features = next_plan_features - current_features
    benefits_list = "\n- ".join(additional_features) if additional_features else "No additional features."

    message = (
        f"⚡ {customer_id}, your current plan is {current_plan}. "
        f"Consider upgrading to {next_plan} to access additional benefits:\n- {benefits_list}"
    )

    return {"customer_id": customer_id, "current_plan": current_plan, "suggested_plan": next_plan, "message": message}
