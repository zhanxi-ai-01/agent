# ui/tab_script.py
import streamlit as st
from rag.vector_store import search_knowledge
from langchain_community.chat_models import ChatTongyi
from config.settings import DASHSCOPE_API_KEY


from langchain_core.messages import HumanMessage

# 初始化大模型 (这里使用通义千问，请根据你项目实际情况调整)
# 如果用的是其他模型，请替换对应的库
try:
    llm = ChatTongyi(dashscope_api_key=DASHSCOPE_API_KEY, model="qwen-max")
except Exception as e:
    st.error(f"大模型初始化失败，请检查 API Key: {e}")


def render_tab_script():
    st.markdown(
        "<h3 style='font-size: 24px; font-weight: 600; margin-bottom: 0px; margin-top: 10px;'>👑️ 销冠成交话术 (异议处理)</h3>",
        unsafe_allow_html=True)
    st.write("专治“太贵了”、“再考虑下”、“家里还有”等成交难题，AI 结合《成交心理学》与《医美话术》知识库一键生成应对策略。")

    # 使用 form 表单，方便一键提交
    with st.form(key='closing_script_form'):
        # 这就是你红框里的输入框
        user_input = st.text_input(
            "**请输入你的成交难题：**",
            placeholder="例如：客户说你们家太贵了，隔壁才卖一半的价钱...",
            help="输入客户拒绝的具体原话，越详细AI分析越准"
        )

        # 快捷提示标签
        st.write("👉 *描述成交失败的场景细节，客户说了什么拒绝的话？对商品的体验什么态度等……*")
        col1, col2, col3, col4 = st.columns(4)
        # 注意：在 form 里的 button 需要 type="primary" 或默认，但点击会触发整个 form 提交
        # 为了不触发提交，我们这里仅做文字展示，让用户自己手打，或者用下方按钮

        # 这就是你红框里的提交按钮
        submit_button = st.form_submit_button(label='✨ 生成高情商应对话术', type="primary")

    # 处理提交逻辑
    if submit_button:
        if not user_input:
            st.warning("⚠️ 请先输入客户的拒绝原话！")
        else:
            with st.spinner("AI 销冠正在翻阅知识库并思考策略..."):
                try:
                    # 1. 检索 Milvus 知识库 (提取 3 条最相关的)
                    search_results = search_knowledge(user_input, limit=3)
                    context = "\n\n".join([res['entity']['text'] for res in search_results])

                    # 2. 组装 Prompt
                    prompt = f"""
                    你是一位拥有10年经验的实体店金牌销售总监。请根据以下【内部知识库内容】回答客户的拒绝。
                    **非常重要：如果知识库中包含具体的话术步骤（如：第一步、第二步），请直接提取并优先使用这些具体步骤，不要自己编造通用理论。**

                    【内部知识库内容】：
                    {context}

                    【客户拒绝场景】：
                    {user_input}

                    请严格按照以下格式输出（直接输出内容，无需寒暄）：
                    1. 💡 客户心理分析（分析客户说这句话的真实意图，不超过50字）
                    2. 🗣️ 黄金应对话术（提供3种不同角度的话术，要求口语化、接地气，可直接背诵）
                    3. 🚀 下一步动作（店员说完后该做什么动作来促单）
                    """

                    # 3. 调用大模型
                    response = llm.invoke([HumanMessage(content=prompt)])

                    # 4. 展示结果
                    st.success("✅ 策略生成完毕！")
                    st.markdown(response.content)

                    # 5. 展示引用来源 (增强专业感)
                    with st.expander("📚 点击查看 AI 参考的知识库原文"):
                        for i, res in enumerate(search_results):
                            st.info(
                                f"**参考片段 {i + 1}** (来源: {res['entity']['source']}):\n\n{res['entity']['text'][:200]}...")

                except Exception as e:
                    st.error(f"生成失败，请检查后端服务。错误信息：{e}")
