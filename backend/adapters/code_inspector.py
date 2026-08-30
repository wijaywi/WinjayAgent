import re

class CodeInspectorAdapter:
    """
    P1: Real Deterministic Evidence Adapter.
    This replaces LLM hallucinated evidence with actual deterministic code inspection.
    """
    @staticmethod
    def inspect(changes: str, search_terms: list[str]) -> dict:
        found = any(re.search(term, changes, re.IGNORECASE) for term in search_terms)
        
        if found:
            return {
                "source": "static_analyzer:regex_inspector",
                "independence_group": "static_analysis",
                "claim": f"Found matching terms {search_terms} in code changes.",
                "verified": True,
                "score": 2  # Deterministic score
            }
        else:
            return {
                "source": "static_analyzer:regex_inspector",
                "independence_group": "static_analysis",
                "claim": f"Terms {search_terms} NOT found in code changes.",
                "verified": True,
                "score": -2  # Deterministic score
            }
