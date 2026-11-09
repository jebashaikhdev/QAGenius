from fastapi import FastAPI, HTTPException
from app.routes import router
from app.test_case_routes import router as test_case_router
from app.review_routes import router as review_router

from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel, Field

from app.claude_client import get_claude_client
from app.config import CLAUDE_MODEL
from app.mcp_client import get_mcp_tools, call_mcp_tool
from app.jira_service import get_jira_projects

from app.agent.graph import run_qa_workflow
from app.schemas import RequirementRequest

from contextlib import asynccontextmanager
from app.database import (
    init_db, 
    save_test_run, 
    get_test_run, 
    get_test_cases,
    approve_test_run, 
    reject_test_run,
    get_jira_issue,
    save_jira_issue
)

import json


class AgentRequest(BaseModel):
    prompt: str = Field(min_length=5, max_length=3000)
    
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="QAGenius API",
    description="Claude-powered Agentic QA Automation Platform",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(test_case_router)
app.include_router(review_router)

@app.get("/")
def root():
    return {
        "message": "Welcome to QAGenius API"
    }
    
@app.get("/health")
def health_check():
    return {
        "status" : "healthy",
        "application": "QAGenius"
    }

@app.post("/api/mcp/get-requirements")
async def mcp_get_requirements(requirement: str):
    try:
        result = await call_mcp_tool(
            "get_requirements",
            { "requirement": requirement }
        )
        
        return {
            "tool": "get_requirements",
            "result": result
        }
        
    except Exception as e:
        import traceback
        traceback.print_exception(e)
        raise HTTPException(
            status_code=500,
            detail=repr(e)
        )


@app.post("/api/mcp/agent")
async def mcp_agent(request: AgentRequest):
    try:
        client = get_claude_client()

        # Discover MCP tools dynamically
        tools = await get_mcp_tools()

        # Let Claude decide whether to call a tool
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1000,
            tools=tools,
            tool_choice={"type": "auto"},
            system = """
                You are the QAgenius AI assistant.

                Understand the user's intent and use the available tools
                when necessary to fulfil their request.

                Rules:
                1. Never require the user to mention a tool name.
                2. Select tools based on the user's natural-language intent.
                3. Use get_requirements when the user needs to retrieve
                or inspect software requirements.
                4. Use save_test_cases when the user explicitly wants
                available test cases to be saved.
                5. Do not call tools when they are unnecessary.
                6. Never claim that an operation succeeded unless the
                tool returns a successful result.
                7. If required information is missing, ask the user.
            """,
            messages=[
                {
                    "role": "user",
                    "content": request.prompt
                }
            ]
        )

        # Check whether Claude selected a tool
        tool_calls = [
            block for block in response.content
            if block.type == "tool_use"
        ]

        # If no tool was selected, return Claude's answer
        if not tool_calls:
            answer = "\n".join(
                block.text for block in response.content
                if block.type == "text"
            )

            return {
                "tool_called": False,
                "response": answer
            }

        # Execute the tools selected by Claude
        tool_results = []

        for tool_call in tool_calls:
            result = await call_mcp_tool(
                tool_call.name,
                tool_call.input
            )

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_call.id,
                "content": result
            })

        # Send tool results back to Claude
        final_response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": request.prompt
                },
                {
                    "role": "assistant",
                    "content": tool_calls
                },
                {
                    "role": "user",
                    "content": tool_results
                }
            ]
        )

        answer = "\n".join(
            block.text for block in final_response.content
            if block.type == "text"
        )

        return {
            "tool_called": True,
            "tools_executed": [tool.name for tool in tool_calls],
            "response": answer
        }

    except Exception as e:
        import traceback
        traceback.print_exception(e)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jira/test-connection")
async def test_jira_connection():
    try:
        project = await get_jira_projects()
        
        return {
            "connected": True,
            "project_key": project["key"],
            "project_name": project["name"]
        }
        
    except Exception as e:
        import traceback
        traceback.print_exception(e)
        raise HTTPException(status_code=500, detail=(str(e)))
    

@app.post("/api/agent/run")
def run_agent_workflow(request: RequirementRequest):
    try:
        result = run_qa_workflow(request.requirement)

        test_cases_data = json.loads(result["test_cases"])

        test_run_id = save_test_run(
            requirement=result["requirement"],
            analysis=result["analysis"],
            test_cases=json.dumps(test_cases_data["test_cases"]),
            review=result["review"],
            agent_status=result["status"]
        )

        return {
            **result,
            "test_cases": test_cases_data["test_cases"],
            "test_run_id": test_run_id,
            "human_approved": False
        }

    except Exception as e:
        import traceback
        traceback.print_exception(e)
        raise HTTPException(status_code=500, detail=str(e))

    
@app.get("/api/agent/runs/{test_run_id}")
def fetch_test_run(test_run_id: int):
    test_run = get_test_run(test_run_id)
    
    if test_run is None:
        raise HTTPException(
            status_code=404,
            detail="Test run not found"
        )
        
    test_run["test_cases"] = get_test_cases(test_run_id)
        
    return test_run

@app.post("/api/agent/runs/{test_run_id}/approve")
def approve_agent_run(test_run_id: int):
    approved = approve_test_run(test_run_id)
    
    if not approved:
        raise HTTPException(
            status_code=400,
            detail="Test run cannot be approved. It may not exist or may not have AI approval."
        )
        
    return {
        "message": "Test run approved successfully",
        "test_run_id": test_run_id,
        "human_approved": True,
        "human_decision": "approved",
    }

@app.post("/api/agent/runs/{test_run_id}/reject")
def reject_agent_run(test_run_id: int):
    rejected = reject_test_run(test_run_id)
    
    if not rejected:
        raise HTTPException(
            status_code=400,
            detail="Test run cannot be rejected. It may not exist or it may already have a human decision."
        )
    
    return {
        "message": "Test run rejected successfully.",
        "test_run_id": test_run_id,
        "human_approved": False,
        "human_decision": "rejected"
    }

@app.post("/api/agent/runs/{test_run_id}/create-jira-issues")
async def create_jira_issues(test_run_id: int):

    # Verify that the test run exists
    test_run = get_test_run(test_run_id)

    if not test_run:
        raise HTTPException(
            status_code=404,
            detail="Test run not found."
        )

    # Enforce AI approval
    if test_run["agent_status"] != "approved":
        raise HTTPException(
            status_code=400,
            detail="AI approval is required."
        )

    # Enforce human approval
    if test_run["human_decision"] != "approved":
        raise HTTPException(
            status_code=403,
            detail="Human approval is required before Jira creation."
        )

    test_cases = get_test_cases(test_run_id)

    if not test_cases:
        raise HTTPException(
            status_code=400,
            detail="No test cases found for this test run."
        )

    created_issues = []
    existing_issues = []
    failed_issues = []

    for case in test_cases:

        # Prevent duplicate Jira issue creation
        existing = get_jira_issue(case["id"])

        if existing:
            existing_issues.append({
                "test_case_id": case["case_id"],
                "jira_issue_key": existing["jira_issue_key"]
            })
            continue

        summary = f'{case["case_id"]}: {case["scenario"]}'

        description = f"""
            Test Case ID: {case["case_id"]}

            Requirement:
            {test_run["requirement"]}

            Scenario:
            {case["scenario"]}

            Preconditions:
            {case["preconditions"]}

            Steps:
            {chr(10).join(
                f"{index}. {step}"
                for index, step in enumerate(case["steps"], start=1)
            )}

            Test Data:
            {case["test_data"]}

            Expected Result:
            {case["expected_result"]}

            Test Type: {case["test_type"]}
            Priority: {case["priority"]}
        """

        try:
            result = await call_mcp_tool(
                "create_jira_issue_tool",
                {
                    "summary": summary,
                    "description": description
                }
            )

            jira_data = json.loads(result)

            save_jira_issue(
                test_case_id=case["id"],
                jira_issue_key=jira_data["key"],
                jira_issue_id=jira_data["id"]
            )

            created_issues.append({
                "test_case_id": case["case_id"],
                "jira_issue_key": jira_data["key"]
            })

        except Exception as e:
            failed_issues.append({
                "test_case_id": case["case_id"],
                "error": str(e)
            })

    return {
        "test_run_id": test_run_id,
        "created_count": len(created_issues),
        "skipped_count": len(existing_issues),
        "failed_count": len(failed_issues),
        "created_issues": created_issues,
        "existing_issues": existing_issues,
        "failed_issues": failed_issues
    }
