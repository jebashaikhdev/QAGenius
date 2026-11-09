from app.config import ANTHROPIC_API_KEY

if ANTHROPIC_API_KEY:
    print("Anthropic API key loaded successfully")
else:
    print("Anthropic API key is missing")