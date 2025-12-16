from __future__ import annotations
from google.adk import Agent
from google.adk.tools.bigquery import BigQueryCredentialsConfig
from google.adk.tools.bigquery import BigQueryToolset
from google.adk.tools.bigquery.config import BigQueryToolConfig
from google.adk.tools.bigquery.config import WriteMode
import google.auth
# Import all tools from the separate tools.py file
from .tools import (
    generate_wire_status_report,
    get_detailed_wire_report, 
    get_intraday_balance, 
    retrieve_document_copy, 
    verify_ach_file,
    
    # <<< NEW IMPORTS: The Plan Eligibility Tools >>>
    check_eligibility,
    get_customer_plan,
    suggest_higher_plan_with_benefits
)

# --- BigQuery Toolset Configuration ---
tool_config = BigQueryToolConfig(write_mode=WriteMode.BLOCKED)

application_default_credentials, _ = google.auth.default()
credentials_config = BigQueryCredentialsConfig(
    credentials=application_default_credentials
)

bigquery_toolset = BigQueryToolset(
    credentials_config=credentials_config, bigquery_tool_config=tool_config
)

# -------------------------------------------------------------------
# Reporting Agent (with Plan Eligibility Gate)
# -------------------------------------------------------------------
REPORTING_INSTRUCTION = """
You are the Report Execution Agent. Your primary goal is to fulfill report and data requests, 
but you must **always** enforce the data access eligibility rules.

Rules:
1. **MANDATORY GATE:** Before calling any data retrieval tool 
   (e.g., generate_wire_status_report, get_intraday_balance, retrieve_document_copy), 
   you MUST first call the `check_eligibility` tool using the user's query.
2. **Eligibility Check:**
    - If `check_eligibility` returns a status of "INCLUDED", proceed immediately to call 
      the relevant data retrieval tool (e.g., generate_wire_status_report).
    - If `check_eligibility` returns "OPTIONAL" or "NOT_AVAILABLE", **DO NOT** proceed 
      with the data retrieval. Instead, respond directly to the user with the warning 
      message provided by the `check_eligibility` tool.
3. **Tool Selection:** Determine which specific data tool is required by the query 
   (e.g., "live balance" -> get_intraday_balance; "historical report" -> generate_wire_status_report; detailed report -> get_detailed_wire_report).
4. **Friendly Response:** Use the output of the final successful data tool call to provide a 
   clear, user-friendly summary.
"""

reporting_agent = Agent(
    name="reporting_agent",
    model="gemini-2.0-flash",
    description=(
        "A multi-functional financial assistant that enforces a mandatory plan eligibility "
        "check before executing any data retrieval (reports, balances, documents) or action."
    ),
    instruction=REPORTING_INSTRUCTION, # <<< NEW INSTRUCTION ADDED
    # Register all the implemented tool functions
    tools=[
        # Plan management tools (MUST be used for eligibility check first)
        check_eligibility,
        get_customer_plan,
        suggest_higher_plan_with_benefits,
        
        # Data and operational tools (The actual work)
        generate_wire_status_report,
        get_detailed_wire_report,
        get_intraday_balance,
        retrieve_document_copy,
        verify_ach_file,
    ],
)