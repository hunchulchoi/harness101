import json
from anthropic.call import call_llm, print_response
from tools import TOOLS, excute_tool


def chat():
    messages = []

    while True:
        user_input = input("\nYou> ").strip()

        if not user_input or user_input.lower() in ["exit", "quit", "bye"]:
            print("\nBye!")
            break

        if user_input.lower() in ["/clear"]:
            messages = []
            continue

        messages.append({"role": "user", "content": user_input})

        try:
            response = call_llm(messages, tools=TOOLS)
        except RuntimeError as e:
            print(f"\nError: {e}")
            print("배열 깨졌으면 /clear")
            messages.pop()
            continue

        print_response("response", response)

        messages.append({"role": "assistant", "content": response["content"]})

        used_tool = False
        for block in response["content"]:
            if block["type"] == "text":
                print(f"\nAssistant> {block['text']}")
            elif block["type"] == "tool_use":
                used_tool = True
                print(f"\n[tool] {block['name']}({json.dumps(block['input'])})")
                result = excute_tool(block["name"], block["input"])

                print_response("\t tool result=>", result)

                messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": block["id"],
                                "content": result,
                            }
                        ],
                    }
                )

        if used_tool:
            try:
                response2 = call_llm(messages, tools=TOOLS)
            except RuntimeError as e:
                print(f"\nError: {e}")
                print("배열 깨졌으면 /clear")
                continue

            messages.append({"role": "assistant", "content": response2["content"]})

            print_response("response2", response2)

            for block in response2["content"]:
                if block["type"] == "text":
                    print(f"\nAssistant> {block['text']}")

        print_response("messages", messages)

        print(f"-->{len(json.dumps(messages))}")


if __name__ == "__main__":
    chat()
