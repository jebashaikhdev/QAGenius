from app.claude_client import get_claude_client
from app.config import (
    CLAUDE_MODEL, 
    REQUIREMENT_ANALYZER_SKILL_ID, 
    TEST_CASE_GENERATOR_SKILL_ID,
    TEST_CASE_REVIEWER_SKILL_ID
    )
import json

TEST_CASE_OUTPUT_TOOL = {
    "name": "submit_test_cases",
    "description": "Submit the complete collection of generated QA test cases.",
    "input_schema": {
        "type": "object",
        "properties": {
            "test_cases": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "scenario": {"type": "string"},
                        "preconditions": {"type": "string"},
                        "steps": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "test_data": {"type": "string"},
                        "expected_result": {"type": "string"},
                        "test_type": {"type": "string"},
                        "priority": {
                            "type": "string",
                            "enum": ["High", "Medium", "Low"]
                        }
                    },
                    "required": [
                        "id",
                        "scenario",
                        "preconditions",
                        "steps",
                        "test_data",
                        "expected_result",
                        "test_type",
                        "priority"
                    ],
                    "additionalProperties": False
                }
            }
        },
        "required": ["test_cases"],
        "additionalProperties": False
    }
}

def invoke_skill(
    skill_id: str,
    prompt: str,
    max_tokens: int = 5000,
    output_tool: dict | None = None
) -> str:
    client = get_claude_client()

    tools = [
        {
            "type": "code_execution_20250825",
            "name": "code_execution"
        }
    ]

    if output_tool:
        tools.append(output_tool)

        prompt += """

        IMPORTANT:
        Submit your complete response using the
        submit_test_cases tool.

        Do not return the test cases as ordinary text.
        Call the tool with the structured test case data.
        """

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=max_tokens,
        container={
            "skills": [
                {
                    "type": "custom",
                    "skill_id": skill_id,
                    "version": "latest"
                }
            ]
        },
        tools=tools,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    if response.stop_reason == "max_tokens":
        raise RuntimeError(
            f"Claude response was truncated for skill: {skill_id}"
        )

    if output_tool:
        tool_blocks = [
            block
            for block in response.content
            if block.type == "tool_use"
            and block.name == output_tool["name"]
        ]

        if not tool_blocks:
            raise RuntimeError(
                "Claude did not submit structured test cases "
                "using the required tool."
            )

        tool_input = tool_blocks[0].input
        test_cases = tool_input.get("test_cases")

        if not isinstance(test_cases, list) or not test_cases:
            raise ValueError("Invalid or empty test case output.")

        required_fields = {
            "id",
            "scenario",
            "preconditions",
            "steps",
            "test_data",
            "expected_result",
            "test_type",
            "priority"
        }

        for index, test_case in enumerate(test_cases, start=1):

            if not isinstance(test_case, dict):
                raise ValueError(f"Test case {index} must be a JSON object.")

            missing_fields = required_fields - test_case.keys()

            if missing_fields:
                raise ValueError(
                    f"Test case {index} is missing fields: {missing_fields}"
                )

            if not isinstance(test_case["steps"], list):
                raise ValueError(f"Test case {index} has invalid steps.")

            if not all(isinstance(step, str) for step in test_case["steps"]):
                raise ValueError(f"Test case {index} contains invalid steps.")

            if test_case["priority"] not in ["High", "Medium", "Low"]:
                raise ValueError(f"Test case {index} has invalid priority.")

            for field in required_fields - {"steps"}:
                if not isinstance(test_case[field], str):
                    raise ValueError(
                        f"Test case {index} has an invalid {field} field."
                    )

        return json.dumps(tool_input)

    text_blocks = [
        block.text
        for block in response.content
        if block.type == "text"
    ]

    if not text_blocks:
        raise RuntimeError(
            f"No text returned by Claude for skill: {skill_id}. "
            f"Stop reason: {response.stop_reason}"
        )

    return "\n".join(text_blocks)

    
def analyze_node(state):
    analysis = invoke_skill(
        REQUIREMENT_ANALYZER_SKILL_ID,
        state["requirement"],
        max_tokens=1500
    )
    return { "analysis": analysis }


def generate_node(state):
    prompt = f"""
    Original Requirement:
    {state["requirement"]}

    Requirement Analysis:
    {state["analysis"]}

    Generate structured functional test cases for this requirement.

    Follow the mandatory output contract defined in your Skill.
    """

    test_cases = invoke_skill(
        TEST_CASE_GENERATOR_SKILL_ID,
        prompt,
        max_tokens=5000,
        output_tool=TEST_CASE_OUTPUT_TOOL
    )

    return {"test_cases": test_cases}



def review_node(state):
    test_cases_data = json.loads(state["test_cases"])

    prompt = f"""
    Original Requirement:
    {state["requirement"]}

    Requirement Analysis:
    {state["analysis"]}

    Generated Test Cases (structured JSON):
    {json.dumps(test_cases_data, indent=2)}

    Review these test cases against the original requirement.

    Check requirement coverage, clarity, correctness of expected results,
    duplicate scenarios, and whether any functionality is unsupported.

    Follow the review guidelines defined in your Skill.
    """

    review = invoke_skill(
        TEST_CASE_REVIEWER_SKILL_ID,
        prompt,
        max_tokens=1500
    )

    return {"review": review}

    
def decide_node(state):
    client = get_claude_client()
    
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=100,
        system="""
        You are a QAgenius workflow decision maker.
        
        Evaluate the test case review.
        
        Return exactly one of these responses:
        APPROVED
        NEEDS_IMPROVEMENT
        
        Approve only when the reviewer considers the test case sufficiently complete and correct.
        Otherwise return NEEDS_IMPROVEMENT.
        """,
        messages=[
            {
                "role": "user",
                "content": state["review"]
            }
        ]
    )
    
    if response.stop_reason == "max_tokens":
        raise RuntimeError("Claude decision response was truncated.")
    
    text_blocks = [
        block.text.strip()
        for block in response.content
        if block.type == "text"
    ]
    
    if not text_blocks:
        block_types = [block.type for block in response.content]
        
        raise RuntimeError(
            f"Claude returned no text in decision response. "
            f"Stop reason: {response.stop_reason}. "
            f"Block types: {block_types}"
        )
        
    decision = text_blocks[0].upper().replace("_", " ").strip()

    if decision not in ["APPROVED", "NEEDS IMPROVEMENT"]:
        raise RuntimeError(
            f"Unexpected decision from Claude: {decision}"
        )
    
    status = (
        "approved"
        if decision == "APPROVED"
        else "needs_improvement"
    )
    return { "status": status }


def improve_node(state):
    prompt = f"""
    Original Requirement:
    {state["requirement"]}

    Requirement Analysis:
    {state["analysis"]}

    Previously Generated Test Cases:
    {state["test_cases"]}

    Reviewer Feedback:
    {state["review"]}

    Improve the test cases by addressing the reviewer's feedback.

    Preserve valid existing test cases where possible.
    Do not introduce functionality unsupported by the requirement.

    Follow the mandatory structured JSON output contract defined in your Skill.
    """

    test_cases = invoke_skill(
        TEST_CASE_GENERATOR_SKILL_ID,
        prompt,
        max_tokens=5000,
        output_tool=TEST_CASE_OUTPUT_TOOL
    )

    return {
        "test_cases": test_cases,
        "iteration": state["iteration"] + 1
    }
