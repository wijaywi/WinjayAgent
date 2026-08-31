import os
import json
import hashlib
from google.cloud import firestore
from datetime import datetime, timezone
import uuid

class EpistemicMemoryBank:
    """
    Winjay Architecture: Tamper-Evident Epistemic Ledger & Atomic Idempotency.
    """
    def __init__(self, project_id=None):
        environment = os.getenv("ENVIRONMENT", "development")
        try:
            self.db = firestore.Client(project=project_id)
            self.mock_store = {}
            self.mock_events = set()
        except Exception as e:
            if environment == "production":
                raise RuntimeError(f"CRITICAL: Firestore is required in production but failed to initialize. Error: {e}")
            else:
                print(f"Warning: Firestore initialization failed. Running volatile memory fallback for DEV mode. Error: {e}")
                self.db = None 
                self.mock_store = {}
                self.mock_events = set()

    def check_and_mark_event(self, event_id: str) -> bool:
        """P2: Atomic Idempotency using Firestore Transactions"""
        if self.db:
            transaction = self.db.transaction()
            event_ref = self.db.collection("events").document(event_id)
            
            @firestore.transactional
            def atomic_check(transaction, ref):
                snapshot = ref.get(transaction=transaction)
                if snapshot.exists:
                    return False
                transaction.set(ref, {"received_at": datetime.now(timezone.utc).isoformat()})
                return True
                
            return atomic_check(transaction, event_ref)
        else:
            if event_id in self.mock_events:
                return False
            self.mock_events.add(event_id)
            return True

    def clear_event(self, event_id: str):
        """Allows retry of failed events."""
        if self.db:
            self.db.collection("events").document(event_id).delete()
        else:
            if event_id in self.mock_events:
                self.mock_events.remove(event_id)

    def log_hypothesis(self, event_id: str, hypothesis_data) -> str:
        h_id = f"H-{uuid.uuid4().hex[:8]}"
        initial_hash = hashlib.sha256(b"INIT").hexdigest()
        data = {
            "hypothesis_id": h_id,
            "event_id": event_id,
            "hypothesis": hypothesis_data.hypothesis,
            "falsification_contract": hypothesis_data.falsification_contract.model_dump(),
            "current_status": "RESEARCHING",
            "belief_history": [],
            "latest_hash": initial_hash,
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
        """P4: Tamper-Evident Append-Only History (Hash Chain)"""
        snapshot = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "confidence": confidence,
            "reason": reason
        }
        
        if self.db:
            doc_ref = self.db.collection("hypothesis_ledger").document(h_id)
            doc = doc_ref.get().to_dict()
            previous_hash = doc.get("latest_hash", hashlib.sha256(b"INIT").hexdigest())
            
            # Incorporate evidence ledger into hash chain to prevent undetected evidence tampering
            evidence_str = json.dumps(doc.get("evidence_ledger", []), sort_keys=True)
            payload = previous_hash + json.dumps(snapshot, sort_keys=True) + evidence_str
            new_hash = hashlib.sha256(payload.encode()).hexdigest()
            
            snapshot["previous_hash"] = previous_hash
            snapshot["hash"] = new_hash
            
            doc_ref.update({
                "current_status": status,
                "latest_hash": new_hash,
                "belief_history": firestore.ArrayUnion([snapshot])
            })
        else:
            if h_id in self.mock_store:
                doc = self.mock_store[h_id]
                previous_hash = doc.get("latest_hash", hashlib.sha256(b"INIT").hexdigest())
                
                evidence_str = json.dumps(doc.get("evidence_ledger", []), sort_keys=True)
                payload = previous_hash + json.dumps(snapshot, sort_keys=True) + evidence_str
                new_hash = hashlib.sha256(payload.encode()).hexdigest()
                
                snapshot["previous_hash"] = previous_hash
                snapshot["hash"] = new_hash
                
                self.mock_store[h_id]["current_status"] = status
                self.mock_store[h_id]["latest_hash"] = new_hash
                self.mock_store[h_id]["belief_history"].append(snapshot)
