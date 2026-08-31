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
            
            if inv_type in ["keyword_search", "regex_match", "regex_search"]:
                search_term = params.get("search_term", "")
                
                if not search_term:
                    real_evidence.append({
                        "type": "error",
                        "claim": f"UNSUPPORTED_INVESTIGATION: Missing search_term for {target}",
                        "score": 0,
                        "verified": False,
                        "provenance": provenance
                    })
                    continue
                
                found = bool(re.search(search_term, changes, re.IGNORECASE))
                
                if found:
                    real_evidence.append({
                        "type": "static_analysis",
                        "claim": f"Found matching term '{search_term}' in code changes.",
                        "score": 2,
                        "verified": True,
                        "provenance": provenance
                    })
                else:
                    real_evidence.append({
                        "type": "static_analysis",
                        "claim": f"Term '{search_term}' NOT found in code changes.",
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
