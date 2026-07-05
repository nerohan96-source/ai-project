import anthropic
import os

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

print("=== AI 简历优化工具 ===")
print("输入你的工作经历，AI 帮你改得更专业")
print("输入 'quit' 退出\n")

while True:
    user_input = input("你的原文：\n> ")

    if user_input.lower() == "quit":
        print("再见！")
        break

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""你是一位专业的简历顾问，擅长帮助求职者优化简历内容。
请将以下工作经历改写得更加专业、量化、有力，符合美国求职市场的标准。
要求：
- 用 action verb 开头
- 尽量加入数字和结果
- 保持简洁，一到两句话

原文：
{user_input}

优化后："""
            }
        ]
    )

    print(f"\nAI 优化版本：\n{message.content[0].text}\n")
    print("-" * 40 + "\n")
