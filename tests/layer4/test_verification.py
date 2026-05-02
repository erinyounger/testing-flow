import pytest
import json
from pathlib import Path
from tflow.artifacts.verification import VerificationArtifact, VerificationResult


class TestVerificationArtifact:
    """VerificationArtifact TDD tests"""

    def test_create_initializes_verification_json(self, tmp_path):
        """RED: Create verification file"""
        va = VerificationArtifact(str(tmp_path))
        result = va.create("plan_001")

        verification_file = tmp_path / "verification.json"
        assert verification_file.exists()

        with open(verification_file) as f:
            data = json.load(f)
        assert data["plan_id"] == "plan_001"
        assert "existence" in data["layers"]
        assert "substance" in data["layers"]
        assert "connection" in data["layers"]

    def test_update_layer_updates_correct_layer(self, tmp_path):
        """GREEN: Update specified layer"""
        va = VerificationArtifact(str(tmp_path))
        va.create("plan_001")

        va.update_layer("existence", True, [{"file": "login.py", "found": True}])

        with open(tmp_path / "verification.json") as f:
            data = json.load(f)
        assert data["layers"]["existence"]["passed"] == True
        assert len(data["layers"]["existence"]["evidence"]) == 1