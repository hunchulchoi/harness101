from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class Role(str, Enum):
    """The role of a message"""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """A message in a chat"""

    role: Role = Field(description="The role of the message")
    content: str | list[Any] = Field(description="The content of the message")


class ToolMessage(Message):
    """A message that contains a tool call"""

    tool_use_id: UUID = Field(description="The ID of the tool call", nullable=False)
    tool_name: str = Field(description="The name of the tool", nullable=False)
    tool_args: dict = Field(
        description="The arguments of the tool call", nullable=False
    )


class ToolResult(BaseModel):
    """A message that contains the result of a tool call"""

    tool_use_id: UUID = Field(description="The ID of the tool call", nullable=False)
    content: str = Field(description="The content of the tool result", min_length=2)
