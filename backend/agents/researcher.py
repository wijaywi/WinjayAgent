from google import genai
from pydantic import BaseModel, Field
import os

# Using the recommended genai SDK for Gemini 3.5
# Set GEMINI_API_KEY in environment variables
client = genai.Client()

class ResearchHypothesis(BaseModel):
    hypothesis: str = Field(description="The core security hypothesis generated from the delta.")
    assumptions: list[str] = Field(description="Assumptions made in this hypothesis.")

class ResearcherAgent:
    """
    Winjay Concept: The Researcher generates hypotheses from an Environment Delta.
    """
    def __init__(self):
        self.model_name = "gemini-3.5-flash"

    def process_delta(self, delta_info: dict) -> ResearchHypothesis:
        prompt = f"""
        You are an advanced Security Researcher Agent.
        Analyze the following Environment Delta (e.g. a Git commit).
        Generate a specific, falsifiable security hypothesis about what vulnerability might have been introduced.
        
        Delta Information:
        {delta_info}
        """
        
        try:
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": ResearchHypothesis,
                    "temperature": 0.2
                }
            )
            return response.parsed
        except Exception as e:
            # Fallback for local mock if API key isn't set yet
            print(f"Researcher API Error: {e}")
            return ResearchHypothesis(
                hypothesis="The change to the authentication middleware bypasses token validation for the /api/admin route.",
                assumptions=["The route does not have secondary checks", "The delta modified the core auth file"]
            )
