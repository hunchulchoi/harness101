import asyncio
import json
from call import call_llm


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

        response = call_llm(messages)

        print(f"Response: {response}")

        text = "".join(b["text"] for b in response["content"] if b["type"] == "text")

        messages.append({"role": "assistant", "content": response["content"]})

        print(f"\nAssistant> {text} -->{len(json.dumps(response))}")


if __name__ == "__main__":
    chat()
