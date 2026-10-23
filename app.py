import streamlit as st
import sys
import os
from dotenv import load_dotenv
base_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv()

# 再下载浏览器
os.system("playwright install chromium")
# 把当前脚本所在目录加入模块搜索路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入 5 个核心组件 (⭐⭐⭐ 修改点 1：新增了 tab_script 的导入)
from ui.tab_vision import render_tab_vision
from ui.tab_strategy import render_tab_strategy
from ui.tab_h5 import render_tab_h5
from ui.tab_poster import render_tab_poster
from ui.tab_script import render_tab_script  # ⭐️ 新增的话术模块



# ==================== 页面配置 ====================
st.set_page_config(
    page_title="实体店 AI 营销智能体",
    page_icon="🚀",
    layout="wide"
)

# 👇 👇 👇 把密码拦截代码粘贴在这里 👇 👇 👇
# ==================== 登录拦截页面 ====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    # 增加顶部留白，让页面重心下移
    st.markdown("<br><br>", unsafe_allow_html=True)

    # 分成左右两列，比例大概是 1 比 1.5（右边宽一点，放图）
    col_left, col_right = st.columns([1, 1.5])

    with col_left:
        # 左侧：欢迎语和输入框
        st.markdown("<h1 style='color: #1f77b4;'>🔐 欢迎使用</h1>", unsafe_allow_html=True)
        st.markdown("<h2 style='font-size: 24px;'>实体店一站式 AI 营销智能体</h2>", unsafe_allow_html=True)
        st.markdown("---")

        st.markdown("**请使用内部邀请码登录体验：**")
        pwd = st.text_input("演示邀请码", type="password", label_visibility="collapsed")

        if st.button("🚀 进入系统", use_container_width=True, type="primary"):
            # ⭐️ 从 .env 环境变量中读取密码列表，如果没设置，默认就是 zhanxi888
            valid_codes = os.getenv("VIP_CODES", "zhanxi888").split(",")

            # ⭐️ 判断用户输入的密码是否在列表中
            if pwd in valid_codes:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("❌ 邀请码错误，请重试。")

    with col_right:
        # 右侧：放你的产品预览图
        preview_path = os.path.join(base_dir, "preview.png")  # 假设你的图叫 preview.png
        if os.path.exists(preview_path):
            st.image(preview_path, use_container_width=True, caption="系统全功能预览")
        else:
            # 如果你还没放图，给个占位提示
            st.info("💡 请将系统截图保存为 `preview.png` 放在根目录，即可在此处展示。")

    st.stop()  # 拦截，不让它往下跑


# 🌟 关键修复：初始化 Session State，防止切换页面时数据丢失
if "marketing_plan" not in st.session_state:
    st.session_state.marketing_plan = None
if "design_image_path" not in st.session_state:
    st.session_state.design_image_path = None

# ==================== 左侧侧边栏 ====================
with st.sidebar:
    st.header("⚙️ 知识库管理")
    st.markdown("如，更新新版《成交心理学》知识库和贵店用户画像、营销等数据，请点击按钮刷新。平时勿动，API会扣钱")

    # ⭐️ 新增：文件上传组件
    uploaded_files = st.file_uploader(
        "📂 上传新的知识资料 (支持多选 Word)",
        type=["docx"],
        accept_multiple_files=True
    )

    # ⭐️ 新增：处理上传的文件并保存到本地
    if uploaded_files:
        # 找到你项目的 data/source_documents 目录
        # 注意：这里的 base_dir 在你的 app.py 顶部应该已经定义过了
        save_dir = os.path.join(base_dir, "data", "source_documents")
        os.makedirs(save_dir, exist_ok=True)  # 确保文件夹存在

        saved_count = 0
        for uploaded_file in uploaded_files:
            file_path = os.path.join(save_dir, uploaded_file.name)

            # 如果文件不存在，才写入（防止每次刷新页面重复写入）
            if not os.path.exists(file_path):
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                saved_count += 1

        if saved_count > 0:
            st.success(f"✅ 已成功保存 {saved_count} 个新文件！请点击下方按钮重建知识库。")
        else:
            st.info("💡 这些文件已存在于知识库文件夹中。")

    # 原有的刷新按钮（保持原样）
    if st.button("🔄 刷新/重建知识库", type="primary", use_container_width=True):
        with st.spinner("正在读取文档、切分、调用阿里云向量化并写入 Milvus，请耐心等待..."):
            try:
                from rag.vector_store import build_knowledge_base

                build_knowledge_base(force_rebuild=True)
                st.success("✅ 知识库重建成功！可以开始使用最新数据了。")
            except Exception as e:
                st.error(f"❌ 重建失败: {str(e)}")
                st.exception(e)


# ==================== 顶部布局优化 ====================
col_logo, col_title = st.columns([1, 7])

with col_logo:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(base_dir, "zhanxi.png")
    if os.path.exists(image_path):
        st.image(image_path, use_container_width=True)
    else:
        st.warning("📖 请将书籍封面图片命名为 `zhanxi.png`，并放入项目根目录。")

with col_title:
    st.markdown(
        "<h1 style='color: #1f77b4; font-size: 34px; margin-bottom: 0; padding-top: 10px; margin-left: 10px; '>詹老师实体店AI一站式营销智能体</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='font-size: 22px; color: #555; margin-top: 5px; margin-left: 10px; '>竞品分析 ⇨ AI智能生成营销策略 ⇨ 海报设计 ▌ 销冠话术</p>",
        unsafe_allow_html=True
    )
st.markdown("---")

# ==================== 自定义大字号导航栏 ====================
# ⭐⭐⭐ 修改点 2：在导航菜单选项中，增加第五个按钮
nav_options = [
    "📸 AI分析爆款海报",
    "🧠 AI生成营销方案",
    "📱 H5 宣传页面生成",
    "🖼️ AI智能设计海报",
    "👑️ 销冠成交话术"  # ⭐️ 新增导航
]

st.markdown("""
<style>
    /* 1. 导航菜单文字大小与粗细 */
    div[role="radiogroup"] label p {
        font-size: 15px !important;
        font-weight: bold !important;
        padding-right: 0px !important;
    }
    
    /* 2. 单选框外层容器：用负数强制消灭它底部的自带留白 */
    div[data-testid="stRadio"] {
        margin-top: -15px !important;    
        margin-bottom: -25px !important; /* ⭐️ 核心大招：把下方的元素死死吸上来 */
        padding-top: 0px !important;
        padding-bottom: 0px !important;
    }

    /* 3. 强制压缩单选框内部的包裹层 */
    div[data-testid="stRadio"] > div {
        margin-bottom: 0px !important;
        padding-bottom: 0px !important;
    }
    
    /* 4. 修复 label 的间距 */
    div[data-testid="stRadio"] label {
        margin-bottom: 0px !important; 
    }
    
    /* 5. 精准控制横线 (hr) 的间距 */
    hr {
        margin-top: 10px !important;    
        margin-bottom: 0px !important; 
    }

    /* 6. 图片与整体布局 */
    div[data-testid="stImage"] {
        width: 140px !important; 
        max-width: 160px !important;
    }
    div[data-testid="stHorizontalBlock"] {
        gap: 0px !important; 
    }
    div[data-testid="stVerticalBlock"] {
        align-items: flex-start !important; 
        text-align: left !important;        
    }
</style>
""", unsafe_allow_html=True)

selected_tab = st.radio(
    "导航菜单",
    nav_options,
    horizontal=True,
    label_visibility="collapsed"
)
st.markdown("---")

# ==================== 根据选中的导航，渲染对应的页面 ====================
# ⭐⭐⭐ 修改点 3：增加最后一个 elif 判断，渲染新模块
if selected_tab == "📸 AI分析爆款海报":
    render_tab_vision()
elif selected_tab == "🧠 AI生成营销方案":
    render_tab_strategy()
elif selected_tab == "📱 H5 宣传页面生成":
    render_tab_h5()
elif selected_tab == "🖼️ AI智能设计海报":
    render_tab_poster()
elif selected_tab == "👑️ 销冠成交话术":  # ⭐️ 新增路由
    render_tab_script()


