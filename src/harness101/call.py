import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

from rich.console import Console
from rich.markdown import Markdown

from harness101.logger import get_logger

logger = get_logger(__name__)

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

API_KEY = os.environ["ANTHROPIC_API_KEY"]
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")
BASE_URL = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1").rstrip(
    "/"
)

MAX_ROUNDS = int(os.environ.get("MAX_ROUNDS", "3"))

console = Console()


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


def log_decorator(func):
    """Log the function call and response"""

    def wrapper(*args, **kwargs):
        logger.debug(f"================== {func.__name__} call: ==================")
        logger.debug(f"args: {args}")
        logger.debug(f"kwargs: {kwargs}")
        return func(*args, **kwargs)

    return wrapper


@log_decorator
def view_response(role, response):
    """Pretty-print a response as markdown"""
    logger.debug(Markdown(response))


@log_decorator
def print_response(name: str, response: dict):
    """Pretty-print a model response"""
    if hasattr(response, "model_dump"):
        response = response.model_dump(mode="json")
    payload = json.dumps(response, indent=2, ensure_ascii=False, default=str)
    logger.debug(payload)
    print(f"================== {name} ==================")
    print(payload)


def call_llm(messages: list[dict], system: str = "", tools: list[dict] | None = None):
    """Call the LLM"""
    body = {
        "model": MODEL,
        "max_tokens": 4096,
        "messages": messages,
    }
    if system:
        body["system"] = system
    if tools:
        body["tools"] = tools

    req = urllib.request.Request(
        f"{BASE_URL}/messages",
        data=json.dumps(body).encode(),
        headers={
            "content-type": "application/json",
            "x-api-key": API_KEY,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        detail = e.read().decode()
        raise RuntimeError(f"LLM HTTP {e.code}: {detail}") from e
