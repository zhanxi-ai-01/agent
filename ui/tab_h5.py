import streamlit as st
import os
import streamlit.components.v1 as components
from core.h5_builder import H5Builder


def render_tab_h5():
    st.markdown(
        "<h3 style='font-size: 24px; font-weight: 600; margin-bottom: 0px; margin-top: 10px;'>📱 生成 H5 营销页</h3>",
        unsafe_allow_html=True)
    st.markdown("一键生成可在微信中传播的移动端网页。")

    marketing_plan = st.session_state.get('marketing_plan', '')

    if not marketing_plan:
        st.warning("⚠️ 请先在【生成方案】页面生成营销方案，或在此手动粘贴。")
        #marketing_plan = st.text_area("手动粘贴营销方案", height=200)
        marketing_plan = st.text_area("手动粘贴营销方案", height=200, key="h5_plan_input")
    else:
        st.success("✅ 已读取到上一步生成的营销方案！")
        with st.expander("查看方案详情"):
            st.markdown(marketing_plan)

    col1, col2 = st.columns(2)
    with col1:
        phone = st.text_input("门店联系电话", value="400-123-4567", key="h5_phone_input")
    with col2:
        address = st.text_input("门店地址", value="北京市朝阳区xxx路xxx号", key="h5_address_input")

    if st.button("🚀 生成 H5 页面", type="primary"):
        if not marketing_plan.strip():
            st.error("❌ 请先提供营销方案！")
            return

        with st.spinner("正在生成 H5 代码，这可能需要 30 秒..."):
            try:
                builder = H5Builder()
                html_code = builder.generate_h5(
                    marketing_plan,
                    phone_number=phone,
                    address=address
                )

                st.success("✅ H5 生成成功！")

                output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs")
                os.makedirs(output_dir, exist_ok=True)
                output_file = os.path.join(output_dir, "generated_h5.html")
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(html_code)

                st.markdown("### 📱 手机端效果预览")
                components.html(html_code, height=600, scrolling=True)

                with open(output_file, "rb") as file:
                    st.download_button(
                        label="⬇️ 下载 H5 源码 (.html)",
                        data=file,
                        file_name="marketing_h5.html",
                        mime="text/html"
                    )

            except Exception as e:
                st.error(f"❌ H5 生成失败: {str(e)}")