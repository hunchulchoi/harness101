# harness101

[Isuru Wijesiri, *Harness Engineering 101*](https://isuruwijesiri.com/harness-engineering-101/)을 읽고 따라 만든 학습용 하니스입니다.

LLM은 뇌고, 하니스는 몸입니다. API는 상태가 없습니다. 매 턴 대화 배열 전체를 보내고 텍스트를 받습니다. 하니스는 그 배열을 만들고, 돌리고, 지키는 프로그램입니다.

원문에서 배운 내용을 바탕으로 직접 짜 봤습니다. 저자 Isuru Wijesiri 님께 감사드립니다.

원문 코드·라이선스와는 별개의 학습 구현입니다. 공식 토이 하니스는 원문 GitHub의 `src/harness/`를 보세요.

## 이 저장소가 다루는 것

원문 Part I(The Wire)을 중심으로 구현했습니다.

| 원문 | 여기 |
|------|------|
| Ch.1 JSON 배열로 말하기 | `urllib`로 Anthropic Messages API 호출, SDK 없음 |
| Ch.3 도구 = JSON → 함수 | `read_file`, `write_file`, `run_command`, `agent` |
| Ch.4 에이전트 루프 | `tool_use`가 끝날 때까지 호출·실행·`tool_result` 반복 |
| (학습 확장) | SQLite에 세션·턴·usage·stop_reason 저장 |

아직 없는 것: 캐시, 컨텍스트 압축, 서브에이전트 실제 분기, MCP.

## 구조

```
src/harness101/
  anthropic/call.py      # Messages API
  chat_in_the_loop_v3.py # 에이전트 루프
  tools.py               # 도구 실행
  store.py               # SQLite 대화 기록
  logger.py              # rich 로그
  settings.py
  model/
tests/
```

## 준비

Python 3.12+, [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/hunchulchoi/harness101.git
cd harness101
uv sync
```

프로젝트 루트에 `.env`를 둡니다. 이 파일은 git에 올리지 마세요.

```
ANTHROPIC_BASE_URL=https://api.anthropic.com/v1
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-haiku-5-5
ANTHROPIC_VERSION=2026-10-21
LLM_PROVIDER=anthropic
MAX_ROUNDS=50
LOG_LEVEL=DEBUG
```

## 실행

```bash
uv run python -m harness101.chat_in_the_loop_v3
```

대화는 `.data/conversations.db`에 쌓입니다. 다시 실행하면 이전 세션을 이어갈 수 있습니다.

테스트:

```bash
uv run python -m unittest tests.test_store -v
```

## 참고

- 원문: [Harness Engineering 101](https://isuruwijesiri.com/harness-engineering-101/) — Isuru Wijesiri, Version 1.1, October 2026
- 원문 한 줄: *The LLM is the brain. The harness is the body.*
