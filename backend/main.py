from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import uvicorn
from agents.researcher import ResearcherAgent
from agents.falsifier import FalsifierAgent
from engine.policy import DeterministicBeliefEngine
from memory.firestore_client import EpistemicMemoryBank

app = FastAPI(title="Winjay OS - Agent Reliability Infrastructure")

# Initialize Systems
memory_bank = EpistemicMemoryBank()
researcher = ResearcherAgent()
falsifier = FalsifierAgent()

class DeltaEvent(BaseModel):
    repository: str
    commit_id: str
    changes: str

@app.post("/webhook/environment-delta")
async def process_delta(event: DeltaEvent):
    # 1. Idempotency Check & Event Deduplication
    event_id = f"github:{event.repository}:{event.commit_id}"
    if memory_bank.check_idempotency(event_id):
        return {"status": "SKIPPED", "reason": "Event already processed. Preventing duplicate hypothesis."}
    
    memory_bank.mark_event_received(event_id)
    print(f"[*] Received Environment Delta: {event_id}")
    
    try:
        # 2. Researcher generates Hypothesis & Falsification Contract
        research_result = researcher.process_delta(event.model_dump())
        
        # 3. Log to Epistemic Memory Bank (Immutable Setup)
        h_id = memory_bank.log_hypothesis(event_id, research_result)
        print(f"[+] Hypothesis Logged with Contract: {h_id}")
        
        # 4. Falsifier attempts to destroy the hypothesis based on the Contract
        falsify_result = falsifier.attempt_falsification(
            hypothesis=research_result.hypothesis,
            contract=research_result.falsification_contract.model_dump(),
            delta_info=event.model_dump()
        )
        
        # 5. Log Structured Evidence
        evidence_items = [item.model_dump() for item in falsify_result.evidence_ledger]
        memory_bank.add_evidence(h_id, evidence_items)
        print(f"[-] Evidence Ledger updated with {len(evidence_items)} items.")
        
        # 6. Deterministic Belief Engine (LLM does not have authority here)
        decision = DeterministicBeliefEngine.evaluate(evidence_items)
        
        # 7. Commit final belief to the Immutable Audit Trail
        memory_bank.append_belief_state(
            h_id=h_id,
            status=decision["status"],
            confidence=decision["confidence"],
            reason=decision["reason"]
        )
        
        print(f"[*] Belief Engine Decision: {decision['status']} (Confidence: {decision['confidence']})")
        
        return {
            "event_id": event_id,
            "hypothesis_id": h_id,
            "final_status": decision["status"],
            "confidence": decision["confidence"],
            "reasoning": decision["reason"],
            "evidence_ledger_size": len(evidence_items)
        }
        
    except Exception as e:
        # ABSOLUTELY NO FABRICATED FALLBACKS.
        # Failures map to an explicit UNKNOWN / FAILURE state for the Human-on-the-loop.
        print(f"[!] Critical System Failure during Agent execution: {str(e)}")
        return {
            "event_id": event_id,
            "status": "AGENT_FAILURE",
            "reason": str(e),
            "action_required": "SYSTEM_ESCALATION_REQUIRED"
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
