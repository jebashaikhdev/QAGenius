from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.claude_client import get_claude_client
from app.config import CLAUDE_MODEL, TEST_CASE_GENERATOR_SKILL_ID

router = APIRouter(prefix="/api", tags=["Test Case Generation"])

class TestCaseRequest(BaseModel):
    requirement: str = Field( min_length=10, max_length=5000 )
    analysis: str = Field( min_length=10, max_length=10000 )
    
@router.post("/generate-test-cases")
def generate_test_cases(request: TestCaseRequest):
    try:
        client = get_claude_client()
        
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4000,
            system="""You are the Test Case Generation component of QAgenius.

            Your ONLY responsibility is to generate software test cases using the supplied requirement and requirement analysis.

            Do not build or implement applications.
            Do not inspect files or environments.
            Follow the test-case-generator Skill.
            Return structured test cases only.""",
            container={
                "skills": [
                    {
                        "type": "custom",
                        "skill_id": TEST_CASE_GENERATOR_SKILL_ID,
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
                    
                    Generate structured test cases based on the above requirement and analysis. Return only the structured test cases without any additional explanations or commentary.
                    """
                }
            ]
        )
        
        result = "\n".join(
            block.text
            for block in response.content
            if block.type == "text"
        )
        
        if not result.strip():
            raise ValueError(
                f"Claude returned no text. Stop reason: {response.stop_reason}"
            )
            
        return {
            "test_cases": result,
            "model": response.model,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Test case generation failed: {str(e)}"
        ) 