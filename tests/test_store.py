import json
import tempfile
import unittest
from pathlib import Path

from harness101.model.anthropic.message import Message, Role
from harness101.model.anthropic.response import ToolUseBlock, Usage
from harness101.store import ConversationStore


class ConversationStoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "chat.db"
        self.store = ConversationStore(self.path)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_new_session_loads_empty(self) -> None:
        session_id = self.store.create_session(model="claude-haiku-5-5")
        self.assertTrue(session_id)
        self.assertEqual(self.store.load(session_id), [])

    def test_append_roundtrip_preserves_order_and_content(self) -> None:
        session_id = self.store.create_session(model="claude-haiku-5-5")
        user = Message(role=Role.USER, content="여기 파일은 뭐가 있어?")
        assistant = Message(
            role=Role.ASSISTANT,
            content=[
                ToolUseBlock(
                    id="toolu_1",
                    name="run_command",
                    input={"command": "ls -la"},
                )
            ],
        )
        tool = Message(
            role=Role.USER,
            content=[
                {
                    "type": "tool_result",
                    "tool_use_id": "toolu_1",
                    "content": "a.txt\n",
                }
            ],
        )
        self.store.append(session_id, user)
        self.store.append(session_id, assistant)
        self.store.append(session_id, tool)

        loaded = self.store.load(session_id)
        self.assertEqual(len(loaded), 3)
        self.assertEqual(loaded[0].role, Role.USER)
        self.assertEqual(loaded[0].content, "여기 파일은 뭐가 있어?")
        self.assertEqual(loaded[1].role, Role.ASSISTANT)
        self.assertEqual(loaded[1].content[0]["name"], "run_command")
        self.assertEqual(loaded[2].content[0]["tool_use_id"], "toolu_1")

    def test_sessions_are_isolated(self) -> None:
        a = self.store.create_session(model="a")
        b = self.store.create_session(model="b")
        self.store.append(a, Message(role=Role.USER, content="from a"))
        self.store.append(b, Message(role=Role.USER, content="from b"))
        self.assertEqual(self.store.load(a)[0].content, "from a")
        self.assertEqual(self.store.load(b)[0].content, "from b")

    def test_latest_session_is_most_recently_appended(self) -> None:
        older = self.store.create_session(model="a")
        newer = self.store.create_session(model="b")
        self.store.append(older, Message(role=Role.USER, content="old"))
        self.assertEqual(self.store.latest_session_id(), older)
        self.store.append(newer, Message(role=Role.USER, content="new"))
        self.assertEqual(self.store.latest_session_id(), newer)

    def test_append_stores_type_conversation_id_and_usage(self) -> None:
        session_id = self.store.create_session(model="a")
        usage = Usage(input_tokens=12, output_tokens=34)
        self.store.append(
            session_id,
            Message(role=Role.ASSISTANT, content="ok"),
            type="assistant",
            conversation_id="msg_abc",
            usage=usage,
            stop_reason="tool_use",
        )
        import sqlite3

        with sqlite3.connect(self.path) as conn:
            row = conn.execute(
                "SELECT type, conversation_id, usage, stop_reason FROM messages"
            ).fetchone()
        self.assertEqual(row[0], "assistant")
        self.assertEqual(row[1], "msg_abc")
        self.assertEqual(json.loads(row[2])["input_tokens"], 12)
        self.assertEqual(json.loads(row[2])["output_tokens"], 34)
        self.assertEqual(row[3], "tool_use")

    def test_messages_in_same_user_prompt_share_turn(self) -> None:
        session_id = self.store.create_session(model="a")
        turn_1 = self.store.next_turn(session_id)
        self.assertEqual(turn_1, 1)
        self.store.append(
            session_id, Message(role=Role.USER, content="q1"), type="user", turn=turn_1
        )
        self.store.append(
            session_id,
            Message(role=Role.ASSISTANT, content="a1"),
            type="assistant",
            turn=turn_1,
        )
        self.store.append(
            session_id,
            Message(
                role=Role.USER,
                content=[{"type": "tool_result", "tool_use_id": "t1", "content": "ok"}],
            ),
            type="tool_result",
            turn=turn_1,
        )
        turn_2 = self.store.next_turn(session_id)
        self.assertEqual(turn_2, 2)
        self.store.append(
            session_id, Message(role=Role.USER, content="q2"), type="user", turn=turn_2
        )
        import sqlite3

        with sqlite3.connect(self.path) as conn:
            turns = [
                row[0] for row in conn.execute("SELECT turn FROM messages ORDER BY seq")
            ]
        self.assertEqual(turns, [1, 1, 1, 2])

    def test_content_json_is_valid_json(self) -> None:
        session_id = self.store.create_session(model="a")
        self.store.append(session_id, Message(role=Role.USER, content="hi"))
        import sqlite3

        with sqlite3.connect(self.path) as conn:
            raw = conn.execute("SELECT content_json FROM messages").fetchone()[0]
        self.assertEqual(json.loads(raw), "hi")


if __name__ == "__main__":
    unittest.main()
