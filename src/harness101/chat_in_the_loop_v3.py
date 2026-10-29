from harness101.logger import get_logger, get_response_panel, console
from harness101.anthropic.call import call_llm, view_response
from harness101.model.anthropic.message import Message, Role
from harness101.model.anthropic.response import Response, ToolUseBlock
from harness101.model.message import ToolResult
from harness101.settings import settings
from harness101.tools import TOOLS, excute_tool

from harness101.store import store

from rich.prompt import Confirm, Prompt


logger = get_logger(__name__)
messages: list[Message] = []
session_id: str | None = None
turn: int | None = None


def remember(
    message: Message,
    *,
    type: str | None = None,
    conversation_id: str | None = None,
    usage: object | None = None,
    stop_reason: str | None = None,
) -> None:
    """Keep RAM list and SQLite in lockstep."""
    messages.append(message)
    if session_id is None:
        raise RuntimeError("session_id missing")
    store.append(
        session_id,
        message,
        type=type,
        conversation_id=conversation_id,
        usage=usage,
        turn=turn,
        stop_reason=stop_reason,
    )

    logger.debug(f"remember: {len(messages)} messages")


def run_turn(messages: list[Message]):
    """One user turn = as many model/tool rounds as the task needs"""

    for _ in range(settings.max_rounds):
        reply: Response = call_llm(messages, tools=TOOLS)

        logger.debug("%s/%s=>", _, settings.max_rounds)
        logger.debug(get_response_panel("reply", reply))

        remember(
            Message(role=Role.ASSISTANT, content=reply.content),
            type="assistant",
            conversation_id=reply.id,
            usage=reply.usage,
            stop_reason=reply.stop_reason,
        )

        if reply.text.strip():
            view_response(reply, messages[0], session_id)

        if reply.stop_reason != "tool_use":
            return

        results: list[ToolResult] = []

        for block in reply.content:
            if isinstance(block, ToolUseBlock):

                # print_response("block", block)

                output = excute_tool(block.name, block)
                logger.debug(get_response_panel("output", output))
                results.append(output.to_block())

                # logger.warning(f"results")

        remember(
            Message(role=Role.USER, content=results),
            type="tool_result",
            conversation_id=reply.id,
        )




def open_session() -> str:
    latest = store.latest_session_id()
    if latest and Confirm.ask("이전 대화 이어갈까?", default=False):
        messages.extend(store.load(latest))
        logger.info("resumed session %s (%s msgs)", latest, len(messages))
        return latest
    new_id = store.create_session(settings.llm_model)
    logger.info("new session %s", new_id)
    return new_id


def main():
    global session_id, turn
    session_id = open_session()
    while True:
        user_input = Prompt.ask("[yellow bold]무엇을 도와 드릴까요?[/]\n[green]User>[/]")

        if not user_input or user_input.lower() in ["exit", "quit", "bye"]:
            if Confirm.ask("종료 할깝쇼?", default=True):
                break
            else:
                continue
        turn = store.next_turn(session_id)
        remember(
            Message(role=Role.USER, content=user_input),
            type="user",
        )
        
        with console.status("Thinking...", spinner="dots"):
            run_turn(messages)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception("An error occurred: %s", e)
    finally:
        logger.info("[bold red]Exiting...[/]")
