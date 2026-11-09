from pydantic import BaseModel, Field

class RequirementRequest(BaseModel):
    requirement: str = Field(
        min_length=10,
        max_length=5000
    )