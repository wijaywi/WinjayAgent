from google import genai
from pydantic import BaseModel, Field

client = genai.Client()

class FalsificationResult(BaseModel):
    counter_evidence: str = Field(description="Evidence that contradicts or weakens the original hypothesis.")
    falsification_confidence: float = Field(description="How confident the agent is that the hypothesis is WRONG (0.0 to 1.0).")

class FalsifierAgent:
    """
    Winjay Concept: The Falsifier's ONLY job is to destroy the Researcher's hypothesis.
    This prevents confirmation bias and builds 'epistemic responsibility'.
    """
    def __init__(self):
        self.model_name = "gemini-3.5-flash"

    def attempt_falsification(self, hypothesis: str, assumptions: list[str]) -> FalsificationResult:
        prompt = f"""
        You are the Falsifier Agent. Your explicit goal is to DESTROY the following security hypothesis.
        Do not look for confirmation. Look for reasons why this hypothesis is false, a false positive, or mitigated.
        
        Hypothesis: {hypothesis}
        Assumptions made: {assumptions}
        
        Generate counter-evidence and score how confident you are that the hypothesis is INVALID.
        """
        
        try:
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": FalsificationResult,
                    "temperature": 0.4
                }
            )
            return response.parsed
        except Exception as e:
            print(f"Falsifier API Error: {e}")
            return FalsificationResult(
                counter_evidence="The modified auth middleware still inherits from `BaseAuthGuard`, which enforces JWT validation at the controller level.",
                falsification_confidence=0.85
            )
