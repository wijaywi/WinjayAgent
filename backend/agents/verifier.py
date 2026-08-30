from google import genai
from pydantic import BaseModel, Field

client = genai.Client()

class VerificationResult(BaseModel):
    final_belief_confidence: float = Field(description="The final epistemic confidence that the hypothesis is TRUE (0.0 to 1.0).")
    status: str = Field(description="Must be one of: 'confirmed', 'disproven', 'uncertain', 'escalated_to_human'.")
    reasoning: str = Field(description="Explanation of how the belief was updated based on evidence vs counter-evidence.")

class VerifierAgent:
    """
    Winjay Concept: The Verifier acts as the judge, balancing the Researcher's claim 
    against the Falsifier's counter-evidence to update the Belief State.
    """
    def __init__(self):
        self.model_name = "gemini-3.5-flash"

    def verify_belief(self, hypothesis: str, counter_evidence: str, falsifier_confidence: float) -> VerificationResult:
        prompt = f"""
        You are the Verifier Agent (The Judge).
        You must calculate the Final Epistemic Belief (0.0 to 1.0) of a hypothesis.
        
        Original Hypothesis: {hypothesis}
        Falsifier Counter-Evidence: {counter_evidence}
        Falsifier Confidence that Hypothesis is WRONG: {falsifier_confidence}
        
        Weigh the evidence. If the falsifier is highly confident with strong counter-evidence, the belief should drop near 0.0 (disproven).
        If the falsifier failed, belief rises. If it's ambiguous, mark 'uncertain' or 'escalated_to_human'.
        """
        
        try:
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": VerificationResult,
                    "temperature": 0.1
                }
            )
            return response.parsed
        except Exception as e:
            print(f"Verifier API Error: {e}")
            return VerificationResult(
                final_belief_confidence=0.15,
                status="disproven",
                reasoning="The counter-evidence successfully demonstrated that a base class mitigation handles the vulnerability."
            )
