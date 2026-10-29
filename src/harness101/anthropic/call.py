import json
import urllib.error
import urllib.request
import uuid

from rich.markdown import Markdown
from rich.panel import Panel

from harness101.logger import get_logger

from harness101.model.anthropic.message import Message, Role
from harness101.model.anthropic.response import Response, TextBlock
from harness101.model.tool import Tool
from harness101.settings import settings

logger = get_logger(__name__)


MAIN_SYSTEM = (
    "당신은 로컬 머신에서 작업하는 유능한 엔지니어링 에이전트입니다. "
    "도구를 사용해 사용자의 작업을 완료하세요. "
    "독립적인 검색이나 조사는 agent 도구에 위임해서 "
    "자신의 컨텍스트를 작게 유지하세요."
)

SUB_SYSTEM = (
    "당신은 집중하는 서브에이전트입니다. 주어진 작업을 도구로 완료한 뒤, "
    "발견한 내용을 명확하고 그 자체로 완결된 보고서로 마무리하세요. "
    "파일 경로를 인용하세요."
)


def view_response(response: Response, message: Message | None = None, session_id: str | None = None):
    """Pretty-print a response as markdown"""

    logger.info(
        Panel(
            Markdown(response.text),
            title=f"[dim]{message.role.value.capitalize()}: [/] {message.content} [dim]({session_id})[/]" if message else None,
            subtitle=f"{response.role.value.capitalize()}",
            border_style="yellow",
            padding=(1, 2),
            expand=False,
        )
    )


def get_request_body(
    messages: Message, system: str = "", tools: list[Tool] | None = None
):
    """Get the request body for the LLM"""

    # logger.debug(f"messages: {messages}")

    if not isinstance(messages, list):
        messages = [messages]
    messages = [
        (
            message.model_dump(mode="json", exclude_none=True)
            if hasattr(message, "model_dump")
            else message
        )
        for message in messages
    ]
    body = {
        "model": settings.llm_model,
        "max_tokens": settings.llm_max_tokens,
        "messages": messages,
    }
    if system:
        body["system"] = system
    if tools:
        body["tools"] = [
            tool.model_dump(mode="json", exclude_none=True) for tool in tools
        ]
    return body


def get_request_headers() -> dict[str, str]:
    """Get the request headers for the LLM"""
    return {
        "content-type": "application/json",
        "x-api-key": settings.llm_api_key.get_secret_value(),
        "anthropic-version": settings.anthropic_version,
    }


def call_llm(
    messages: Message, system: str = "", tools: list[Tool] | None = None
) -> Response:
    body = get_request_body(messages, system, tools)

    req = urllib.request.Request(
        f"{settings.llm_base_url}/messages",
        data=json.dumps(body).encode(),
        headers=get_request_headers(),
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            return Response.model_validate(json.loads(resp.read()))
    except urllib.error.HTTPError as e:
        detail = e.read().decode()
        logger.exception("LLM HTTP error: %s", detail)
        return Response(
            model=settings.llm_model,
            id=str(uuid.uuid4()),
            role=Role.ASSISTANT,
            content=[TextBlock(text=f"Error calling LLM: {e.code} {detail}")],
            stop_reason="end_turn",
        )
