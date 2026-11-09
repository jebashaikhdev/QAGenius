from anthropic import Anthropic
from app.config import ANTHROPIC_API_KEY
# from app.config import CLAUDE_MODEL

def get_claude_client():
    
    if not ANTHROPIC_API_KEY:
        raise ValueError("Anthropic key is not configured.")
    
    # if not CLAUDE_MODEL:
    #     raise ValueError("Claude model is not configured.")
    
    client = Anthropic(
        api_key=ANTHROPIC_API_KEY,
        # model=CLAUDE_MODEL
        )
    
    return client
