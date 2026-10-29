from enum import Enum

from pydantic import BaseModel, Field


class Type(str, Enum):
    """A type of a property"""

    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    FUNCTION = "function"
    NULL = "null"


class Property(BaseModel):
    """A property of a tool"""

    type: Type = Field(description="The type of the property")
    description: str | None = Field(
        default=None, description="The description of the property"
    )
    enum: list[str] | None = Field(
        default=None, description="The enum values of the property"
    )
    default: str | None = Field(
        default=None, description="The default value of the property"
    )


class InputSchema(BaseModel):
    """A schema for the input of a tool"""

    type: Type = Field(description="The type of the input", default=Type.OBJECT)
    properties: dict[str, Property] = Field(description="The properties of the input")
    required: list[str] = Field(
        default_factory=list, description="The required properties of the input"
    )


class OutputSchema(BaseModel):
    """A schema for the output of a tool"""

    type: Type = Field(description="The type of the output")
    properties: dict = Field(
        default_factory=dict, description="The properties of the output"
    )
    required: list[str] = Field(
        default_factory=list, description="The required properties of the output"
    )


class Tool(BaseModel):
    """A tool for the LLM"""

    name: str = Field(description="The name of the tool")
    description: str = Field(description="The description of the tool")
    input_schema: InputSchema = Field(description="The input schema of the tool")
    output_schema: OutputSchema | None = Field(
        default=None,
        exclude=True,
        description="The output schema of the tool",
    )
