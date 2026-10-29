from harness101.anthropic.call import view_response, print_response
from harness101.model.message import Message, Role
from harness101.anthropic.call import call_llm, view_response

messages = Message(role=Role.USER, content="후쿠오카 여행에 대해서 설명해줘")


response = call_llm(messages)
print_response("messages", messages)
print_response("ch01test", response)

view_response(response)
