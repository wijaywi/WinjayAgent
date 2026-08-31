import pytest
import os
from engine.policy import DeterministicBeliefEngine
from adapters.code_inspector import CodeInspectorAdapter

def test_policy_engine_rejects_llm_evidence():
    llm_evidence = [
        {
            "type": "static_analysis",
            "claim": "LLM says this is safe.",
            "score": 3,
            "verified": True,
            # Missing or incorrect provenance
            "provenance": {"source": "gemini_agent"}
        }
    ]
    with pytest.raises(RuntimeError, match="ARCHITECTURAL INVARIANT VIOLATION"):
        DeterministicBeliefEngine.evaluate(llm_evidence)

def test_policy_engine_accepts_adapter_evidence():
    class DummyInv:
        def __init__(self):
            self.target = "auth.py"
            self.investigation_type = "keyword_search"
            self.parameters = {"search_term": "JWT"}
            
    real_evidence = CodeInspectorAdapter.inspect("added JWT validation", [DummyInv()])
    
    result = DeterministicBeliefEngine.evaluate(real_evidence)
    assert result["status"] == "UNCERTAIN_HUMAN_REVIEW"

def test_webhook_secret_missing_in_production():
    import os
    os.environ["ENVIRONMENT"] = "production"
    if "WEBHOOK_SECRET" in os.environ:
        del os.environ["WEBHOOK_SECRET"]
        
    from main import verify_signature
    from fastapi import HTTPException
    
    with pytest.raises(HTTPException) as exc:
        verify_signature(b"payload", "signature")
    assert "WEBHOOK_SECRET missing in production" in str(exc.value)

def test_firestore_missing_in_production():
    import os
    os.environ["ENVIRONMENT"] = "production"
    
    from memory.firestore_client import EpistemicMemoryBank
    with pytest.raises(RuntimeError, match="Firestore is required in production"):
        # We assume project_id="INVALID_PROJECT_THAT_DOESNT_EXIST_123" forces failure
        # For this test we will just mock the error
        try:
            from unittest.mock import patch
            with patch('google.cloud.firestore.Client', side_effect=Exception("Mocked Error")):
                EpistemicMemoryBank(project_id="INVALID")
        except RuntimeError as e:
            raise e
