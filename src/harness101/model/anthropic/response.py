from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from harness101.model.anthropic.message import Role


class TextBlock(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: Literal["text"] = "text"
    text: str


class ThinkingBlock(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: Literal["thinking"] = "thinking"
    thinking: str = ""
    signature: str | None = None


class ToolUseBlock(BaseModel):
    """Anthropic tool_use block. is_error belongs on tool_result, not here."""

    model_config = ConfigDict(extra="ignore")

    type: Literal["tool_use"] = "tool_use"
    id: str
    name: str
    input: dict[str, Any] = Field(default_factory=dict)


ContentBlock = Annotated[
    TextBlock | ThinkingBlock | ToolUseBlock,
    Field(discriminator="type"),
]

StopReason = Literal[
    "end_turn", "tool_use", "max_tokens", "stop_sequence", "pause_turn"
]


class Usage(BaseModel):
    model_config = ConfigDict(extra="allow")

    input_tokens: int = 0
    output_tokens: int = 0


class Response(BaseModel):
    """Anthropic Messages API response."""

    model_config = ConfigDict(extra="allow")

    id: str
    type: str = "message"
    role: Role = Role.ASSISTANT
    model: str
    content: list[ContentBlock]
    stop_reason: StopReason | None = None
    stop_sequence: str | None = None
    usage: Usage | None = None

    @property
    def text(self) -> str:
        return "".join(
            block.text for block in self.content if isinstance(block, TextBlock)
        )
