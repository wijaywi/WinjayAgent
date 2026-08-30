import os
from google.cloud import firestore
from datetime import datetime, timezone
import uuid

class EpistemicMemoryBank:
    """
    Winjay Architecture: Immutable Event Ledger & Hypothesis Ledger.
    """
    def __init__(self, project_id=None):
        try:
            self.db = firestore.Client(project=project_id)
        except Exception as e:
            print(f"Warning: Firestore initialization failed. Running volatile memory fallback. Error: {e}")
            self.db = None 
            self.mock_store = {}
            self.mock_events = set()

    def check_idempotency(self, event_id: str) -> bool:
        """Prevents duplicate hypotheses for the same event."""
        if self.db:
            doc = self.db.collection("events").document(event_id).get()
            return doc.exists
        else:
            return event_id in self.mock_events

    def mark_event_received(self, event_id: str):
        if self.db:
            self.db.collection("events").document(event_id).set({"received_at": datetime.now(timezone.utc).isoformat()})
        else:
            self.mock_events.add(event_id)

    def log_hypothesis(self, event_id: str, hypothesis_data) -> str:
        h_id = f"H-{uuid.uuid4().hex[:8]}"
        data = {
            "hypothesis_id": h_id,
            "event_id": event_id,
            "hypothesis": hypothesis_data.hypothesis,
            "falsification_contract": hypothesis_data.falsification_contract.model_dump(),
            "current_status": "RESEARCHING",
            "belief_history": [],  # IMMUTABLE AUDIT TRAIL
            "evidence_ledger": [],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        if self.db:
            self.db.collection("hypothesis_ledger").document(h_id).set(data)
        else:
            self.mock_store[h_id] = data
            
        return h_id

    def add_evidence(self, h_id: str, evidence_items: list):
        if self.db:
            doc_ref = self.db.collection("hypothesis_ledger").document(h_id)
            for item in evidence_items:
                doc_ref.update({"evidence_ledger": firestore.ArrayUnion([item])})
        else:
            if h_id in self.mock_store:
                self.mock_store[h_id]["evidence_ledger"].extend(evidence_items)

    def append_belief_state(self, h_id: str, status: str, confidence: float, reason: str):
        """Append to belief history, do not overwrite past epistemic states."""
        snapshot = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "confidence": confidence,
            "reason": reason
        }
        
        if self.db:
            doc_ref = self.db.collection("hypothesis_ledger").document(h_id)
            doc_ref.update({
                "current_status": status,
                "belief_history": firestore.ArrayUnion([snapshot])
            })
        else:
            if h_id in self.mock_store:
                self.mock_store[h_id]["current_status"] = status
                self.mock_store[h_id]["belief_history"].append(snapshot)
