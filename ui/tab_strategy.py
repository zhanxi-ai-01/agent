import streamlit as st
from core.strategy_agent import StrategyAgent

def render_tab_strategy():
    st.markdown(
        "<h3 style='font-size: 24px; font-weight: 600; margin-bottom: 0px; margin-top: 10px;'>🧠 生成专属营销方案</h3>",
        unsafe_allow_html=True)
    st.markdown("结合对手分析结果和知识库中《成交心理学》等文档，生成差异化反击方案。")

    # 尝试从 session_state 获取上一步的分析结果
    competitor_info = st.session_state.get('competitor_analysis', '')

    if not competitor_info:
        st.warning("⚠️ 请先在【图片分析】页面完成对手图片的分析，或者手动输入对手信息。")
        competitor_info = st.text_area("手动输入对手信息", height=200)
    else:
        st.success("✅ 已读取到上一步的对手分析结果！")
        with st.expander("查看对手分析详情"):
            st.markdown(competitor_info)

    if st.button("🚀 生成营销方案", type="primary"):
        if not competitor_info.strip():
            st.error("❌ 请先提供对手信息！")
            return

        with st.spinner("正在结合知识库生成方案，请稍候..."):
            try:
                agent = StrategyAgent()
                result = agent.generate_plan(competitor_info)

                # 保存到 session_state，供 H5 生成调用
                st.session_state['marketing_plan'] = result

                st.success("✅ 方案生成完成！")
                st.markdown("### 📋 营销方案：")
                st.markdown(result)

            except Exception as e:
                st.error(f"❌ 生成失败: {str(e)}")