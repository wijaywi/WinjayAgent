from fastapi import FastAPI, HTTPException, Request, Header
from pydantic import BaseModel
import uvicorn
import hmac
import hashlib
import os
from agents.researcher import ResearcherAgent
from agents.falsifier import FalsifierAgent
from adapters.code_inspector import CodeInspectorAdapter
from engine.policy import DeterministicBeliefEngine
from memory.firestore_client import EpistemicMemoryBank

app = FastAPI(title="Winjay OS - Agent Reliability Infrastructure")

memory_bank = EpistemicMemoryBank()
researcher = ResearcherAgent()
falsifier = FalsifierAgent()

class DeltaEvent(BaseModel):
    repository: str
    commit_id: str
    changes: str

def verify_signature(payload: bytes, signature: str):
    """P3: Validates the HMAC signature to prevent unauthenticated access."""
    env = os.getenv("ENVIRONMENT", "development")
    secret = os.getenv("WEBHOOK_SECRET")
    
    if not secret:
        if env == "production":
            raise HTTPException(status_code=500, detail="CRITICAL: WEBHOOK_SECRET missing in production. Failing closed.")
        secret = "winjay-hackathon-secret" # Dev fallback only
        
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(f"sha256={expected}", signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

@app.post("/webhook/environment-delta")
async def process_delta(event: DeltaEvent, request: Request, x_hub_signature_256: str = Header(None)):
    env = os.getenv("ENVIRONMENT", "development")
    # In production, require the signature header
    if env == "production" and not x_hub_signature_256:
        raise HTTPException(status_code=401, detail="Missing webhook signature")

    if x_hub_signature_256:
        body = await request.body()
        verify_signature(body, x_hub_signature_256)
        
    # 1. P2: Atomic Idempotency Check & Event Deduplication
    event_id = f"github:{event.repository}:{event.commit_id}"
    if not memory_bank.check_and_mark_event(event_id):
        return {"status": "SKIPPED", "reason": "Event already processed concurrently."}
    
    print(f"[*] Received & Authenticated Environment Delta: {event_id}")
    
    try:
        # 2. Researcher generates Hypothesis & Falsification Contract
        research_result = researcher.process_delta(event.model_dump())
        h_id = memory_bank.log_hypothesis(event_id, research_result)
        
        # 3. P0: Falsifier ONLY PROPOSES what to check. 
        falsify_proposal = falsifier.attempt_falsification(
            hypothesis=research_result.hypothesis,
            contract=research_result.falsification_contract.model_dump(),
            delta_info=event.model_dump()
        )
        
        # 4. P1: Execution of Real Deterministic Adapters
        # The LLM output is NOT appended to the ledger. It is consumed by the adapter.
        real_evidence = CodeInspectorAdapter.inspect(
            changes=event.changes,
            proposals=falsify_proposal.investigations
        )
        
        memory_bank.add_evidence(h_id, real_evidence)
        
        # 5. Deterministic Belief Engine
        # Only deterministic adapter results go into the engine.
        decision = DeterministicBeliefEngine.evaluate(real_evidence)
        
        # 6. P4: Tamper-Evident Immutable Audit Trail
        memory_bank.append_belief_state(
            h_id=h_id,
            status=decision["status"],
            confidence=decision["confidence"],
            reason=decision["reason"]
        )
        
        return {
            "event_id": event_id,
            "hypothesis_id": h_id,
            "final_status": decision["status"],
            "evidence_ledger_size": len(real_evidence),
            "contains_deterministic_evidence": True
        }
        
    except Exception as e:
        print(f"[!] System Failure: {str(e)}")
        return {"status": "AGENT_FAILURE", "reason": str(e), "action_required": "SYSTEM_ESCALATION"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
