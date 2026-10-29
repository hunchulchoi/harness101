import subprocess
from typing import Any

from harness101.model.anthropic.response import ToolUseBlock
from harness101.model.anthropic.tool import InputSchema, Property, Tool, Type
from harness101.model.message import ToolResult


from harness101.logger import get_logger

logger = get_logger(__name__)


BASE_TOOLS = [
    Tool(
        name="read_file",
        description="Read a file and return its contents",
        input_schema=InputSchema(
            type=Type.OBJECT,
            properties={
                "path": Property(
                    type=Type.STRING,
                    description="The path of the file to read",
                ),
            },
            required=["path"],
        ),
    ),
    Tool(
        name="write_file",
        description="Write to a file",
        input_schema=InputSchema(
            type=Type.OBJECT,
            properties={
                "path": Property(
                    type=Type.STRING,
                    description="The path of the file to write to",
                ),
                "content": Property(
                    type=Type.STRING,
                    description="The content to write",
                ),
            },
            required=["path", "content"],
        ),
    ),
    Tool(
        name="run_command",
        description="Run a shell command and return stdout+stderr",
        input_schema=InputSchema(
            type=Type.OBJECT,
            properties={
                "command": Property(
                    type=Type.STRING,
                    description="The command to run",
                ),
            },
            required=["command"],
        ),
    ),
]

AGENT_TOOLS = [
    Tool(
        name="agent",
        description=(
            "Delegate a self-contained task to a subagent with its own fresh context."
            "It can read files and run commands, and returns only its final answer. "
            "Use it for searches and research whose details you don't need to keep. "
            "The subagent knows NOTHING about this conversation, so include all necessary background in the task."
        ),
        input_schema=InputSchema(
            type=Type.OBJECT,
            properties={
                "task": Property(
                    type=Type.STRING,
                    description="The task to delegate",
                ),
            },
            required=["task"],
        ),
    ),
]

TOOLS = BASE_TOOLS + AGENT_TOOLS


def get_tool_result(id: str, output: str, is_error: bool = False) -> ToolResult:
    """Extract the tool result from the model's JSON response"""

    return ToolResult(
        type="tool_result",
        tool_use_id=id,
        content=output,
        is_error=is_error,
    )


def excute_tool(name: str, block: ToolUseBlock) -> ToolResult:
    """Map the model's JSON request to a reald function call"""

    logger.info(f"[tool] executing tool {name} with args: {block.input}")

    try:
        if name == "read_file":

            return get_tool_result(block.id, open(block.input["path"], "r").read())

        if name == "write_file":
            with open(block.input["path"], "w") as f:
                f.write(block.input["content"])

            return get_tool_result(
                block.id,
                f"wrote to {len(block.input['content'])} bytes to {block.input['path']}",
            )

        if name == "run_command":
            out = subprocess.run(
                block.input["command"],
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
            )

            return get_tool_result(block.id, out.stdout + out.stderr)

        return get_tool_result(block.id, f"unknown tool: {name}", is_error=True)

    except Exception as e:

        logger.error("Error executing tool %s: %s", name, e)

        return get_tool_result(
            block.id, f"Error executing tool {name}: {e}", is_error=True
        )
