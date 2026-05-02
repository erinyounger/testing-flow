from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class AgentResult:
    """Result from agent execution"""
    success: bool
    output: str = ""
    error: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseAgent(ABC):
    """Base class for all agents"""

    @abstractmethod
    def run(self, prompt: str, **kwargs) -> AgentResult:
        """Execute the agent with a prompt"""
        pass

    def parse_output(self, output: str) -> Any:
        """Parse output (can be overridden)"""
        return output