from enum import Enum
from pydantic import BaseModel, Field


class Type(Enum):
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

    type: Type = Field(description="The type of the property", nullable=False)
    description: str = Field(
        description="The description of the property", nullable=False
    )
    enum: list[str] = Field(
        description="The enum values of the property", nullable=True
    )
    default: str = Field(description="The default value of the property", nullable=True)
    nullable: bool = Field(description="Whether the property is nullable", default=True)
    required: bool = Field(
        description="Whether the property is required", default=False
    )


class InputSchema(BaseModel):
    """A schema for the input of a tool"""

    type: Type = Field(description="The type of the input", nullable=False)
    properties: Property = Field(
        description="The properties of the input", nullable=False
    )
    required: bool = Field(
        description="The required properties of the input", default=[]
    )


class OutputSchema(BaseModel):
    """A schema for the output of a tool"""

    type: Type = Field(description="The type of the output", nullable=False)
    properties: dict = Field(description="The properties of the output", nullable=False)
    required: list[str] = Field(
        description="The required properties of the output", nullable=False
    )


class Tool(BaseModel):
    """A tool for the LLM"""

    name: str = Field(description="The name of the tool", nullable=False)
    description: str = Field(description="The description of the tool", nullable=False)
    input_schema: InputSchema = Field(
        description="The input schema of the tool", nullable=False
    )
    output_schema: OutputSchema = Field(
        description="The output schema of the tool", nullable=False
    )
