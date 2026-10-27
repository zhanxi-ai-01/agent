import streamlit as st
import os
from core.vision_agent import VisionAgent


def render_tab_vision():
    """渲染视觉分析标签页的 UI"""
    st.markdown(
        "<h3 style='font-size: 24px; font-weight: 600; margin-bottom: 0px; margin-top: 10px;'>📷 AI分析爆款营销海报</h3>",
        unsafe_allow_html=True)
    st.markdown("上传一张爆款营销海报，AI自动提取核心卖点、目标人群和营销策略。")

    # 1. 文件上传组件
    uploaded_file = st.file_uploader("请选择或拖拽一张图片", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        # 预览上传的图片
        st.image(uploaded_file, caption="已上传的对手图片", width=200)

        # 2. 分析按钮
        if st.button("🚀 开始分析图片", type="primary"):
            with st.spinner("AI 正在分析中，请稍候..."):
                # 保存上传的文件到临时目录
                temp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs")
                os.makedirs(temp_dir, exist_ok=True)

                temp_image_path = os.path.join(temp_dir, "uploaded_competitor.jpg")
                with open(temp_image_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                try:
                    # 调用我们的 VisionAgent
                    agent = VisionAgent()
                    result = agent.analyze_image(temp_image_path)

                    # 将结果保存到 session_state，方便其他 Tab 调用
                    st.session_state['competitor_analysis'] = result

                    # 展示结果
                    st.success("✅ 分析完成！")
                    st.markdown("### 📋 提取结果：")
                    st.markdown(result)

                except Exception as e:
                    st.error(f"❌ 分析失败: {str(e)}")