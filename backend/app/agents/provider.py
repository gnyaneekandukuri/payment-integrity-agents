"""LLM providers: OpenAI (live) and Replay (plays back a saved run, no network)."""
import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[3]  # repository root
load_dotenv(ROOT / ".env")


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: str  # JSON string as produced by the model


@dataclass
class Turn:
    content: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0

    def to_dict(self):
        return {"content": self.content, "tool_calls": [tc.__dict__ for tc in self.tool_calls],
                "input_tokens": self.input_tokens, "output_tokens": self.output_tokens}

    @staticmethod
    def from_dict(d):
        return Turn(d["content"], [ToolCall(**tc) for tc in d["tool_calls"]], d.get("input_tokens", 0), d.get("output_tokens", 0))


class OpenAIProvider:
    def __init__(self, model: str | None = None):
        from openai import OpenAI
        self.model = model or os.environ.get("OPENAI_MODEL") or "gpt-4o-mini"
        if not os.environ.get("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is not set in .env at the repository root")
        self.client = OpenAI()

    def complete(self, messages: list[dict], tools: list[dict]) -> Turn:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=[{"type": "function", "function": t} for t in tools],
            tool_choice="auto",
        )
        msg = resp.choices[0].message
        calls = [ToolCall(tc.id, tc.function.name, tc.function.arguments or "{}") for tc in (msg.tool_calls or [])]
        usage = resp.usage
        return Turn(msg.content, calls, getattr(usage, "prompt_tokens", 0) or 0, getattr(usage, "completion_tokens", 0) or 0)


class ReplayProvider:
    """Returns the model turns recorded in a saved run, in order. Tools still run for real."""

    def __init__(self, run_file: Path):
        data = json.loads(Path(run_file).read_text(encoding="utf-8"))
        self.model = f"replay of {data['model']}"
        self.turns = [Turn.from_dict(t) for t in data["turns"]]
        self.i = 0

    def complete(self, messages, tools) -> Turn:
        if self.i >= len(self.turns):
            return Turn("Replay finished.", [])
        turn = self.turns[self.i]
        self.i += 1
        return turn
