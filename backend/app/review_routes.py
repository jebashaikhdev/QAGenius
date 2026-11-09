from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.claude_client import get_claude_client
from app.config import CLAUDE_MODEL, TEST_CASE_REVIEWER_SKILL_ID

router = APIRouter(prefix="/api", tags=["Test Case Review"])

class TestCaseReviewRequest(BaseModel):
    requirement: str = Field(min_length=10, max_length=5000)
    analysis: str = Field(min_length=10, max_length=10000)
    test_cases: str = Field(min_length=10, max_length=20000)
    
@router.post("/review-test-cases")
def review_test_cases(request: TestCaseReviewRequest):
    try:
        client = get_claude_client()
        
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4000,
            system="""
            You are the Test Case Review component of QAgenius.

            Your ONLY responsibility is to review generated test cases against the original requirement and requirement analysis.

            Do not build or implement applications.
            Do not inspect files or environments.
            Do not generate a new test suite.
            Follow the test-case-reviewer Skill.
            Return only the structured review.
            """,
            container={
                "skills":[
                    {
                        "type": "custom",
                        "skill_id": TEST_CASE_REVIEWER_SKILL_ID,
                        "version": "latest"
                    }
                ]
            },
            tools=[
                {
                    "type": "code_execution_20250825",
                    "name": "code_execution",
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": f"""
                    Original Requirement:
                    {request.requirement}

                    Requirement Analysis:
                    {request.analysis}

                    Generated Test Cases:
                    {request.test_cases}

                    Review the generated test cases against the original requirement and requirement analysis. 
                    Provide a structured review highlighting any discrepancies, issues, or areas for improvement. 
                    Return only the structured review without any additional explanations or commentary.
                    """   
                }
            ]
        )
        review = "\n".join(
            block.text
            for block in response.content
            if block.type == "text"
        )
        
        if not review.strip():
            raise ValueError(
                f"Claude returned no text. Stop reason: {response.stop_reason}"
            )
        
        return {
            "review": review,
            "model": response.model,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Test case review failed: {str(e)}"
        )