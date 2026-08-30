from fastapi import FastAPI, Request
from pydantic import BaseModel
import uvicorn
from agents.researcher import ResearcherAgent
from agents.falsifier import FalsifierAgent
from agents.verifier import VerifierAgent
from memory.firestore_client import EpistemicMemoryBank

app = FastAPI(title="Winjay Agent Reliability Infrastructure")

# Initialize Systems
memory_bank = EpistemicMemoryBank()
researcher = ResearcherAgent()
falsifier = FalsifierAgent()
verifier = VerifierAgent()

class DeltaEvent(BaseModel):
    repository: str
    commit_id: str
    changes: str

@app.post("/webhook/environment-delta")
async def process_delta(event: DeltaEvent):
    """
    Winjay Concept: Agents wake up based on Environment Deltas, not cron jobs.
    """
    print(f"[*] Received Environment Delta for {event.repository} (Commit: {event.commit_id})")
    
    # 1. Researcher generates Hypothesis
    research_result = researcher.process_delta(event.dict())
    
    # 2. Log to Epistemic Memory
    h_id = memory_bank.log_hypothesis(research_result.hypothesis, event.dict())
    print(f"[+] Researcher Hypothesis Logged: {h_id}")
    
    # 3. Falsifier attempts to destroy the hypothesis
    falsify_result = falsifier.attempt_falsification(
        hypothesis=research_result.hypothesis,
        assumptions=research_result.assumptions
    )
    
    # 4. Log Counter-Evidence
    memory_bank.add_falsifier_evidence(h_id, falsify_result.counter_evidence)
    print(f"[-] Falsifier Counter-Evidence Added.")
    
    # 5. Verifier updates Belief State
    verify_result = verifier.verify_belief(
        hypothesis=research_result.hypothesis,
        counter_evidence=falsify_result.counter_evidence,
        falsifier_confidence=falsify_result.falsification_confidence
    )
    
    # 6. Commit final belief
    memory_bank.update_belief_state(
        h_id=h_id,
        new_confidence=verify_result.final_belief_confidence,
        status=verify_result.status,
        reasoning=verify_result.reasoning
    )
    
    print(f"[*] Final Belief State for {h_id}: {verify_result.status} (Confidence: {verify_result.final_belief_confidence})")
    
    return {
        "hypothesis_id": h_id,
        "status": verify_result.status,
        "confidence": verify_result.final_belief_confidence,
        "reasoning": verify_result.reasoning
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
