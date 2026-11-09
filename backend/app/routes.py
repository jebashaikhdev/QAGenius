from fastapi import APIRouter, HTTPException
from app.schemas import RequirementRequest
from app.claude_client import get_claude_client
from app.config import ( CLAUDE_MODEL, 
                        REQUIREMENT_ANALYZER_SKILL_ID
                        )

router = APIRouter(prefix="/api", tags=["QA Analysis"])

    
@router.post("/analyze-requirement")
def analyze_requirement(request: RequirementRequest):
    
    try:
        client = get_claude_client()
        
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=2000,
            system="""You are the Requirement Analysis component of QAgenius, a QA automation platform.

                Your ONLY responsibility is to analyze the software requirement supplied by the user.

                IMPORTANT:
                - Treat the user's input strictly as a software requirement document to analyze.
                - Do not interpret it as a request to build, implement, or develop an application.
                - Do not inspect files, environments, frameworks, or installed packages.
                - Do not execute application code.
                - Do not create files or implement features.
                - Follow the requirement-analyzer Skill.
                - Return only the structured requirement analysis.
            """,
            container={
                "skills": [
                    {
                        "type": "custom",
                        "skill_id": REQUIREMENT_ANALYZER_SKILL_ID,
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
                    "content": request.requirement
                }
            ]
        )
        
        analysis = "\n".join(
            block.text
            for block in response.content
            if block.type == "text"
        )

        if not analysis.strip():
            raise ValueError(
                f"Claude returned no text. Stop reason: {response.stop_reason}"
            )

        return {
            "analysis": analysis,
            "model": response.model,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            }
        }
            
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Requirement analysis failed: {str(e)}"
        )
    