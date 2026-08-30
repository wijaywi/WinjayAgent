from google import genai
from pydantic import BaseModel, Field
import os

client = genai.Client()

class EvidenceItem(BaseModel):
    evidence_type: str = Field(description="e.g., code_inspection, static_analysis, test_result, dependency_analysis")
    claim: str = Field(description="What this specific piece of evidence shows.")
    score: int = Field(description="Deterministic score: +3 (strong confirm) to -3 (strong disprove)")

class FalsificationResult(BaseModel):
    evidence_ledger: list[EvidenceItem]

class FalsifierAgent:
    """
    Winjay Architecture: The Falsifier acts on the Falsification Contract to produce scored Evidence Items.
    It does not just argue; it 'inspects' and scores.
    """
    def __init__(self):
        self.model_name = os.getenv("MODEL_NAME", "gemini-3.5-flash")

    def attempt_falsification(self, hypothesis: str, contract: dict, delta_info: dict) -> FalsificationResult:
        prompt = f"""
        You are the Falsifier Agent. Your explicit goal is to attack the hypothesis based on its Falsification Contract.
        (For this architecture demo, simulate the output of static analysis, code inspection, and test results based on standard framework behaviors).
        
        Generate a list of structured EVIDENCE items. 
        Score them deterministically:
        -3 = Verified mitigation / reproduction fails
        -2 = Contradictory code path
         0 = Inconclusive
        +2 = Direct code path confirms
        +3 = Independent static analyzer confirms
        
        Hypothesis: {hypothesis}
        Contract: {contract}
        Delta: {delta_info}
        """
        
        # REMOVED FABRICATED FALLBACK. Failures should propagate cleanly.
        response = client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": FalsificationResult,
                "temperature": 0.1
            }
        )
        return response.parsed
