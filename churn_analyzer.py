import anthropic
import os

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

def analyze_customer(customer_info):
    prompt = f"""你是一位拥有7年经验的保险行业专家，擅长分析客户流失风险。

根据以下客户信息，请提供：
1. 流失风险评级：高风险 / 中风险 / 低风险
2. 风险原因分析（2-3条）
3. 跟进方式建议
4. 是否设置自动提醒（是/否，以及时间节点）
5. Bundle 折扣机会（有/无，列出可以捆绑的险种）

客户信息：
{customer_info}

请用以下格式输出：

【风险评级】高风险 / 中风险 / 低风险

【风险原因】
- 原因1
- 原因2

【跟进建议】
具体跟进方式和话术方向

【自动提醒】
是否设置 + 建议时间节点

【Bundle 机会】
有/无 + 可捆绑险种和预计节省金额
"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text


def get_customer_input():
    print("\n请输入客户信息（填完按 Enter，不知道可以填 '不详'）\n")

    policy_type = input("保单类型（如 Auto / Home / Life / Renters）：")
    years = input("购买时长（年）：")
    premium_change = input("保费变化（如 上涨15% / 持平 / 下降）：")
    premium_reason = input("保费上涨原因（如 at fault claim / 地区风险上升 / 无）：")
    claims = input("过去3年 at fault claims 次数：")
    bundle = input("是否有 Bundle 保险（如 Auto+Home / 仅 Auto）：")
    payment = input("付款记录（如 准时 / 偶尔延迟 / 多次延迟）：")
    last_contact = input("上次联系时间（如 3个月前 / 半年前）：")
    other = input("其他备注（可选）：")

    customer_info = f"""
- 保单类型：{policy_type}
- 购买时长：{years} 年
- 保费变化：{premium_change}
- 上涨原因：{premium_reason}
- At Fault Claims（3年）：{claims} 次
- Bundle 状态：{bundle}
- 付款记录：{payment}
- 上次联系：{last_contact}
- 备注：{other}
"""
    return customer_info


def main():
    print("=" * 50)
    print("  保险客户流失风险分析工具")
    print("  Insurance Customer Churn Analyzer")
    print("=" * 50)
    print("输入 'quit' 退出\n")

    while True:
        cmd = input("\n按 Enter 开始分析新客户，或输入 quit 退出：")
        if cmd.lower() == "quit":
            print("再见！")
            break

        customer_info = get_customer_input()

        print("\n正在分析中...\n")
        result = analyze_customer(customer_info)

        print("=" * 50)
        print(result)
        print("=" * 50)


if __name__ == "__main__":
    main()
