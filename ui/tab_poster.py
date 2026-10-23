import streamlit as st
import os
from core.h5_builder import H5Builder


def render_tab_poster():
    st.markdown(
        "<h3 style='font-size: 24px; font-weight: 600; margin-bottom: 0px; margin-top: 10px;'>🖼️ AI智能设计营销海报</h3>",
        unsafe_allow_html=True)
    st.markdown("把刚才的营销方案变成一张可以在朋友圈/微信群直接转发的长图。")

    # 1. 读取上一步的营销方案
    marketing_plan = st.session_state.get('marketing_plan', '')

    if not marketing_plan:
        st.warning("⚠️ 请先在【生成方案】页面生成营销方案，或在此手动粘贴。")
        #marketing_plan = st.text_area("手动粘贴营销方案", height=200)
        marketing_plan = st.text_area("手动粘贴营销方案", height=200, key="poster_plan_input")
    else:
        st.success("✅ 已读取到上一步生成的营销方案！")
        with st.expander("查看方案详情"):
            st.markdown(marketing_plan)

    # 2. 门店配置
    col1, col2 = st.columns(2)
    with col1:
        phone = st.text_input("门店联系电话", value="400-123-4567",key="poster_phone_input")
    with col2:
        address = st.text_input("门店地址", value="北京市朝阳区xxx路xxx号",key="poster_address_input")

    # 3. 点击按钮生成海报
    if st.button("🚀 生成手机海报", type="primary"):
        if not marketing_plan.strip():
            st.error("❌ 请先提供营销方案！")
            return

        with st.spinner("正在生成海报，请稍候..."):
            try:
                builder = H5Builder()

                # 先复用 H5 生成逻辑，得到 HTML
                html_code = builder.generate_h5(marketing_plan, phone_number=phone, address=address)

                # 保存 HTML 到本地
                output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs")
                os.makedirs(output_dir, exist_ok=True)
                output_file = os.path.join(output_dir, "marketing_poster.html")
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(html_code)

                # 调用 Playwright 进行截图
                image_file = os.path.join(output_dir, "marketing_poster.jpg")
                success = builder.generate_poster_image(output_file, image_file)

                if success:
                    st.success("✅ 海报生成成功！")
                    st.markdown("### 🖼️ 手机海报预览：")
                    st.image(image_file, caption="长按或右键保存图片，直接发朋友圈/微信群")

                    with open(image_file, "rb") as file:
                        st.download_button(
                            label="⬇️ 下载海报 (.jpg)",
                            data=file,
                            file_name="marketing_poster.jpg",
                            mime="image/jpeg"
                        )
                else:
                    st.error("❌ 海报生成失败，请检查 Playwright 是否安装正确。")

            except Exception as e:
                st.error(f"❌ 生成失败: {str(e)}")