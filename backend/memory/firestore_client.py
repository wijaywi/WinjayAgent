import os
from google.cloud import firestore
from datetime import datetime, timezone
import uuid

class EpistemicMemoryBank:
    """
    Winjay Concept: The Memory Bank is not just for chat logs.
    It stores Hypothesis Ledgers, Beliefs, Evidence, and Confidence.
    """
    def __init__(self, project_id=None):
        try:
            self.db = firestore.Client(project=project_id)
        except Exception as e:
            print(f"Warning: Firestore initialization failed (running locally without credentials?). Error: {e}")
            self.db = None # Mock mode if not deployed
            self.mock_store = {}

    def log_hypothesis(self, hypothesis_text: str, source_event: dict) -> str:
        h_id = f"H-{uuid.uuid4().hex[:8]}"
        data = {
            "hypothesis_id": h_id,
            "text": hypothesis_text,
            "source_delta": source_event,
            "status": "investigating",
            "confidence": 0.0,
            "evidence": [],
            "counter_evidence": [],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        if self.db:
            self.db.collection("hypothesis_ledger").document(h_id).set(data)
        else:
            self.mock_store[h_id] = data
            print(f"[MOCK FIRESTORE] Logged Hypothesis: {h_id}")
            
        return h_id

    def add_falsifier_evidence(self, h_id: str, counter_evidence: str):
        if self.db:
            doc_ref = self.db.collection("hypothesis_ledger").document(h_id)
            doc_ref.update({
                "counter_evidence": firestore.ArrayUnion([counter_evidence])
            })
        else:
            if h_id in self.mock_store:
                self.mock_store[h_id]["counter_evidence"].append(counter_evidence)
                print(f"[MOCK FIRESTORE] Added counter-evidence to {h_id}")

    def update_belief_state(self, h_id: str, new_confidence: float, status: str, reasoning: str):
        if self.db:
            doc_ref = self.db.collection("hypothesis_ledger").document(h_id)
            doc_ref.update({
                "confidence": new_confidence,
                "status": status,
                "verifier_reasoning": reasoning,
                "updated_at": datetime.now(timezone.utc).isoformat()
            })
        else:
            if h_id in self.mock_store:
                self.mock_store[h_id]["confidence"] = new_confidence
                self.mock_store[h_id]["status"] = status
                self.mock_store[h_id]["verifier_reasoning"] = reasoning
                print(f"[MOCK FIRESTORE] Updated Belief State for {h_id}: {status} ({new_confidence})")
                
    def get_hypothesis(self, h_id: str):
        if self.db:
            doc = self.db.collection("hypothesis_ledger").document(h_id).get()
            return doc.to_dict() if doc.exists else None
        else:
            return self.mock_store.get(h_id)
