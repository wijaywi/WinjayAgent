class DeterministicBeliefEngine:
    """
    Winjay Core Concept: 'LLMs propose. Evidence decides.'
    LLMs no longer have the authority to output a final status or confidence.
    This deterministic engine evaluates the scored evidence to derive the belief state.
    """
    @staticmethod
    def evaluate(evidence_ledger: list) -> dict:
        if not evidence_ledger:
            return {"status": "INSUFFICIENT_EVIDENCE", "confidence": 0.0, "reason": "No evidence provided."}
            
        total_score = 0
        for item in evidence_ledger:
            # P0 INTEGRITY INVARIANT:
            provenance = item.get("provenance", {})
            if provenance.get("source") != "deterministic_adapter":
                raise RuntimeError("ARCHITECTURAL INVARIANT VIOLATION: Evidence Item lacks deterministic adapter provenance. LLM-generated evidence detected.")
            
            total_score += item.get("score", 0)
        
        # Map score to epistemic confidence (0.0 to 1.0)
        # 0 score = 0.5 (neutral/uncertain)
        # +3 score = 0.8 (high confidence)
        confidence = max(0.0, min(1.0, 0.5 + (total_score * 0.1)))
        
        if total_score >= 3:
            status = "CONFIRMED"
        elif total_score <= -3:
            status = "DISPROVEN"
        elif -2 <= total_score <= 2:
            status = "UNCERTAIN_HUMAN_REVIEW"
        else:
            status = "CONFLICTING_EVIDENCE"
            
        return {
            "status": status,
            "confidence": confidence,
            "reason": f"Deterministic evaluation based on net evidence score of {total_score}."
        }
