"""Data models for MinimalAgent."""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ToolData:
    """Data about a tool execution."""

    name: str
    inputs: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None


@dataclass
class ReasoningStep:
    """A single step in the agent's reasoning process."""

    step_number: int
    timestamp: int = field(default_factory=lambda: int(time.time()))
    thinking: Optional[str] = None
    tools: List[ToolData] = field(default_factory=list)


@dataclass
class Reasoning:
    """Complete reasoning data for an agent interaction."""

    session_id: Optional[str] = None
    query: Optional[str] = None
    steps: List[ReasoningStep] = field(default_factory=list)
    total_steps: int = 0
    final_thinking: Optional[str] = None
    final_response: Optional[str] = None
    truncated: bool = False
    exceeded_size_limit: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        # Basic fields
        result = {
            "session_id": self.session_id,
            "query": self.query,
            "total_steps": self.total_steps,
            "truncated": self.truncated,
            "exceeded_size_limit": self.exceeded_size_limit,
        }

        # Optional fields
        if self.final_thinking:
            result["final_thinking"] = self.final_thinking
        if self.final_response:
            result["final_response"] = self.final_response

        # Steps
        steps_data = []
        for step in self.steps:
            step_dict = {
                "step_number": step.step_number,
                "timestamp": step.timestamp,
            }

            if step.thinking:
                step_dict["thinking"] = step.thinking

            if step.tools:
                tool_data = []
                for tool in step.tools:
                    tool_dict = {
                        "name": tool.name,
                        "inputs": tool.inputs,
                    }
                    if tool.result:
                        tool_dict["result"] = tool.result
                    tool_data.append(tool_dict)
                step_dict["tools"] = tool_data

            steps_data.append(step_dict)

        result["steps"] = steps_data
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Reasoning":
        """Create from dictionary after deserialization."""
        if not data:
            return cls()

        steps = []
        for step_data in data.get("steps", []):
            tools = []
            for tool_data in step_data.get("tools", []):
                tools.append(
                    ToolData(
                        name=tool_data["name"],
                        inputs=tool_data["inputs"],
                        result=tool_data.get("result"),
                    )
                )

            steps.append(
                ReasoningStep(
                    step_number=step_data["step_number"],
                    timestamp=step_data.get("timestamp", int(time.time())),
                    thinking=step_data.get("thinking"),
                    tools=tools,
                )
            )

        return cls(
            session_id=data.get("session_id"),
            query=data.get("query"),
            steps=steps,
            total_steps=data.get("total_steps", len(steps)),
            final_thinking=data.get("final_thinking"),
            final_response=data.get("final_response"),
            truncated=data.get("truncated", False),
            exceeded_size_limit=data.get("exceeded_size_limit", False),
        )
