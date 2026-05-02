import json
import uuid
import subprocess
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional


@dataclass
class ConvergenceCriteria:
    """Convergence criteria for verification"""
    type: str  # grep, file_exists, command
    pattern: str = ""  # for grep and command
    path: str = ""  # file/directory path
    expected: str = ""  # expected value
    negate: bool = False  # True = check does NOT match

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConvergenceCriteria":
        return cls(
            type=data.get("type", ""),
            pattern=data.get("pattern", ""),
            path=data.get("path", ""),
            expected=data.get("expected", ""),
            negate=data.get("negate", False)
        )


@dataclass
class ConvergenceResult:
    """Result of a convergence check"""
    criteria: ConvergenceCriteria
    passed: bool
    evidence: str = ""
    error: Optional[str] = None


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

    def check_convergence(self, criteria_list: List[Dict[str, Any]]) -> List[ConvergenceResult]:
        """Check convergence criteria and return results"""
        results = []

        for criteria_data in criteria_list:
            criteria = ConvergenceCriteria.from_dict(criteria_data)
            result = self._check_single_convergence(criteria)
            results.append(result)

        return results

    def _check_single_convergence(self, criteria: ConvergenceCriteria) -> ConvergenceResult:
        """Check a single convergence criteria"""
        if criteria.type == "file_exists":
            return self._check_file_exists(criteria)
        elif criteria.type == "grep":
            return self._check_grep(criteria)
        elif criteria.type == "command":
            return self._check_command(criteria)
        else:
            return ConvergenceResult(
                criteria=criteria,
                passed=False,
                error=f"Unknown convergence type: {criteria.type}"
            )

    def _check_file_exists(self, criteria: ConvergenceCriteria) -> ConvergenceResult:
        """Check if a file exists"""
        path = Path(criteria.path) if criteria.path else Path(criteria.pattern)

        if criteria.negate:
            passed = not path.exists()
            evidence = f"{path} does not exist" if passed else f"{path} exists"
        else:
            passed = path.exists()
            evidence = f"{path} exists" if passed else f"{path} does not exist"

        return ConvergenceResult(criteria=criteria, passed=passed, evidence=evidence)

    def _check_grep(self, criteria: ConvergenceCriteria) -> ConvergenceResult:
        """Check if a pattern matches in a file"""
        path = Path(criteria.path)

        if not path.exists():
            return ConvergenceResult(
                criteria=criteria,
                passed=False,
                error=f"File not found: {path}"
            )

        try:
            content = path.read_text()
            matches = list(re.finditer(criteria.pattern, content, re.MULTILINE))

            if criteria.negate:
                passed = len(matches) == 0
                evidence = f"Pattern '{criteria.pattern}' not found" if passed else f"Found {len(matches)} match(es)"
            else:
                passed = len(matches) > 0
                evidence = f"Found {len(matches)} match(es)" if passed else f"Pattern '{criteria.pattern}' not found"

            return ConvergenceResult(criteria=criteria, passed=passed, evidence=evidence)
        except Exception as e:
            return ConvergenceResult(criteria=criteria, passed=False, error=str(e))

    def _check_command(self, criteria: ConvergenceCriteria) -> ConvergenceResult:
        """Check if a command succeeds or matches output"""
        try:
            result = subprocess.run(
                criteria.pattern,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )

            if criteria.negate:
                passed = result.returncode != 0
                evidence = f"Command failed as expected" if passed else f"Command succeeded unexpectedly"
            else:
                passed = result.returncode == 0
                evidence = f"Command succeeded" if passed else f"Command failed: {result.stderr}"

            return ConvergenceResult(criteria=criteria, passed=passed, evidence=evidence)
        except subprocess.TimeoutExpired:
            return ConvergenceResult(criteria=criteria, passed=False, error="Command timeout")
        except Exception as e:
            return ConvergenceResult(criteria=criteria, passed=False, error=str(e))