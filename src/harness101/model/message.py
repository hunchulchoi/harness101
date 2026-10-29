from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class Role(str, Enum):
    """The role of a message"""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """A message in a chat"""

    role: Role = Field(description="The role of the message", nullable=False)
    content: str = Field(description="The content of the message", min_length=2)


class ToolMessage(Message):
    """A message that contains a tool call"""

    tool_use_id: str = Field(description="The ID of the tool call", nullable=False)
    tool_name: str = Field(description="The name of the tool", nullable=False)
    tool_args: dict = Field(
        description="The arguments of the tool call", nullable=False
    )


class ToolResult(BaseModel):
    """Anthropic tool_result content block."""

    type: str = "tool_result"
    tool_use_id: str = Field(description="The ID of the tool call")
    content: str = Field(description="The content of the tool result", default="")
    is_error: bool | None = None

    @field_validator("is_error")
    @classmethod
    def only_true(cls, v: bool | None) -> bool | None:
        # True만 남기고, False나 None은 None으로 두어서 직렬화 때 빠지게 함
        return True if v else None

    def to_block(self) -> dict:
        return self.model_dump(exclude_none=True)


class Response(BaseModel):
    """A response from the LLM"""

    model: str = Field(description="The model of the response", nullable=False)
    id: UUID = Field(description="The ID of the response", nullable=False)
    role: Role = Field(description="The role of the response", nullable=False)
    content: str = Field(description="The content of the response", min_length=2)
