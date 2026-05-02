import json
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional


@dataclass
class VerificationResult:
    """Verification result data structure"""
    plan_id: str
    layers: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        "existence": {"passed": False, "evidence": []},
        "substance": {"passed": False, "evidence": []},
        "connection": {"passed": False, "evidence": []}
    })
    convergence_check: Dict[str, Any] = field(default_factory=dict)
    gaps: List[str] = field(default_factory=list)
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VerificationResult":
        return cls(
            plan_id=data.get("plan_id", ""),
            layers=data.get("layers", {}),
            convergence_check=data.get("convergence_check", {}),
            gaps=data.get("gaps", []),
            timestamp=data.get("timestamp", "")
        )


class VerificationArtifact:
    """Verification artifact manager"""

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.verification_file = self.base_dir / "verification.json"

    def create(self, plan_id: str) -> VerificationResult:
        """Create a new verification artifact"""
        import datetime

        result = VerificationResult(
            plan_id=plan_id,
            timestamp=datetime.datetime.now().isoformat()
        )

        with open(self.verification_file, "w") as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)

        return result

    def update_layer(self, layer_name: str, passed: bool, evidence: List[Dict[str, Any]]) -> None:
        """Update a specific verification layer"""
        if self.verification_file.exists():
            with open(self.verification_file) as f:
                data = json.load(f)
        else:
            data = {"layers": {}}

        if "layers" not in data:
            data["layers"] = {}

        data["layers"][layer_name] = {
            "passed": passed,
            "evidence": evidence
        }

        with open(self.verification_file, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_result(self) -> Optional[VerificationResult]:
        """Get verification result"""
        if not self.verification_file.exists():
            return None

        with open(self.verification_file) as f:
            data = json.load(f)

        return VerificationResult.from_dict(data)