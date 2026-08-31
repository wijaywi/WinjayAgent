import re
import hashlib
from datetime import datetime, timezone

class CodeInspectorAdapter:
    """
    P1: Real Deterministic Evidence Adapter.
    This replaces LLM hallucinated evidence with actual deterministic code inspection.
    """
    @staticmethod
    def inspect(changes: str, proposals: list) -> list:
        real_evidence = []
        for inv in proposals:
            inv_type = getattr(inv, 'investigation_type', '').lower()
            target = getattr(inv, 'target', 'unknown')
            params = getattr(inv, 'parameters', {})
            
            # Provenance wrapper
            provenance = {
                "source": "deterministic_adapter",
                "adapter_name": "CodeInspectorAdapter",
                "investigation_type": inv_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "input_hash": hashlib.sha256(changes.encode('utf-8')).hexdigest()
            }
            
            if target.lower() not in changes.lower() and target != "unknown":
                real_evidence.append({
                    "type": "error",
                    "claim": f"TARGET_NOT_FOUND: The target '{target}' is not present in the current environment delta.",
                    "score": 0,
                    "verified": False,
                    "provenance": provenance
                })
                continue
                
            if inv_type == "keyword_search":
                search_term = params.get("search_term", "")
                
                # Limit length to prevent memory exhaustion
                if len(search_term) > 200:
                    search_term = search_term[:200]
                
                if not search_term:
                    real_evidence.append({
                        "type": "error",
                        "claim": f"UNSUPPORTED_INVESTIGATION: Missing search_term for {target}",
                        "score": 0,
                        "verified": False,
                        "provenance": provenance
                    })
                    continue
                
                # Escape search_term to prevent ReDoS (Catastrophic Backtracking)
                safe_pattern = re.escape(search_term)
                found = bool(re.search(safe_pattern, changes, re.IGNORECASE))
                
                if found:
                    real_evidence.append({
                        "type": "static_analysis",
                        "claim": f"Found exact keyword '{search_term}' in target {target}.",
                        "score": 2,
                        "verified": True,
                        "provenance": provenance
                    })
                else:
                    real_evidence.append({
                        "type": "static_analysis",
                        "claim": f"Keyword '{search_term}' NOT found in target {target}.",
                        "score": -2,
                        "verified": True,
                        "provenance": provenance
                    })
            else:
                real_evidence.append({
                    "type": "error",
                    "claim": f"UNSUPPORTED_INVESTIGATION: {inv_type}",
                    "score": 0,
                    "verified": False,
                    "provenance": provenance
                })
                
        return real_evidence
