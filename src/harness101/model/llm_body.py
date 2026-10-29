from pydantic import BaseModel, Field

from harness101.model.message import Role
from harness101.model.tool import Tool
from harness101.model.message import Message


class LLMBody(BaseModel):
    """A body for the LLM"""

    model: str = Field(description="The model to use", nullable=False)
    max_tokens: int = Field(
        description="The maximum number of tokens to generate", default=4096
    )
    messages: list[Message] = Field(
        description="The messages in the conversation", nullable=False
    )
    system: str = Field(description="The system prompt", nullable=True)
    tools: list[Tool] = Field(description="The tools to use", nullable=True)
