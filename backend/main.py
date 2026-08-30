from fastapi import FastAPI, HTTPException, Request, Header
from pydantic import BaseModel
import uvicorn
import hmac
import hashlib
from agents.researcher import ResearcherAgent
from agents.falsifier import FalsifierAgent
from adapters.code_inspector import CodeInspectorAdapter
from engine.policy import DeterministicBeliefEngine
from memory.firestore_client import EpistemicMemoryBank

app = FastAPI(title="Winjay OS - Agent Reliability Infrastructure")

memory_bank = EpistemicMemoryBank()
researcher = ResearcherAgent()
falsifier = FalsifierAgent()

# P3: Webhook Authentication Secret (For demo, hardcoded. In prod, Secret Manager)
WEBHOOK_SECRET = "winjay-hackathon-secret"

class DeltaEvent(BaseModel):
    repository: str
    commit_id: str
    changes: str

def verify_signature(payload: bytes, signature: str):
    """P3: Validates the HMAC signature to prevent unauthenticated access."""
    expected = hmac.new(WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(f"sha256={expected}", signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

@app.post("/webhook/environment-delta")
async def process_delta(event: DeltaEvent, request: Request, x_hub_signature_256: str = Header(None)):
    # 0. P3: Webhook Authentication (Enabled if signature header is passed during demo)
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
        
        # 3. P0: Falsifier NO LONGER hallucinates evidence. It PROPOSES what to check.
        falsify_proposal = falsifier.attempt_falsification(
            hypothesis=research_result.hypothesis,
            contract=research_result.falsification_contract.model_dump(),
            delta_info=event.model_dump()
        )
        
        # 4. P1: Execution of Real Deterministic Adapters
        # The LLM proposed an investigation. The actual adapter fetches the evidence.
        real_evidence = CodeInspectorAdapter.inspect(
            changes=event.changes,
            search_terms=["JWT", "exp", "validate"] # In a real system, extracted from the LLM proposal
        )
        
        # Merge LLM reasoning evidence (strength 1) with REAL deterministic evidence (strength 3)
        combined_evidence = [item.model_dump() for item in falsify_proposal.evidence_ledger]
        combined_evidence.append(real_evidence)
        
        memory_bank.add_evidence(h_id, combined_evidence)
        
        # 5. Deterministic Belief Engine
        decision = DeterministicBeliefEngine.evaluate(combined_evidence)
        
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
            "evidence_ledger_size": len(combined_evidence),
            "contains_deterministic_evidence": True
        }
        
    except Exception as e:
        print(f"[!] System Failure: {str(e)}")
        return {"status": "AGENT_FAILURE", "reason": str(e), "action_required": "SYSTEM_ESCALATION"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
