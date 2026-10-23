# import os
# from dotenv import load_dotenv
# if os.path.exists(env_path):
#     load_dotenv(dotenv_path=env_path)
# else:
#     print(f"⚠️ 警告: 没有找到 .env 文件，请检查路径: {env_path}")
#10月23号部署后修改 ===============================================
import os
from dotenv import load_dotenv

# 1. 优先尝试加载本地的 .env 文件（本地开发用）
# 在云端服务器上，因为没有 .env，这行代码会自动跳过，不报错
load_dotenv()
# 1. 加载根目录下的 .env 文件
# # 这里的路径计算是为了确保无论在哪个目录运行，都能找到根目录的 .env
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) #根目录zx_marketing_agent01
env_path = os.path.join(base_dir, '.env') #结果是类似的绝对路径C:\Users\你的用户名\Desktop\zx_marketing_agent01\.env

# 2. 从系统环境变量中读取（本地会自动读取刚刚加载的 .env，云端会读取 Streamlit Secrets）
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
VISION_MODEL_NAME = os.getenv("VISION_MODEL_NAME", "qwen-vl-plus") # 确保这里有你用的视觉模型名字

# 3. 如果云端 Secrets 没填，这里才报错
if not DASHSCOPE_API_KEY:
    raise ValueError("❌ 致命错误：未找到 DASHSCOPE_API_KEY！请在本地 .env 或云端 Streamlit Secrets 中配置。")


# 2. 读取 API 密钥 (这里列出我们前期需要的几个)
# 视觉分析模型 (例如 GPT-4o 或 Qwen-VL)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "") #如果忘记配置、拼写错误或者文件没加载成功，系统找不到这个变量，它就不
# 会报错崩溃，而是把空字符串 "" 赋值给变量。
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "") # 阿里云通义千问的 Key DASHSCOPE_API_KEY

# 策略生成模型 (例如 DeepSeek)
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

# 3. 模型名称配置 (方便以后随时更换模型)
VISION_MODEL_NAME = os.getenv("VISION_MODEL_NAME", "qwen3-vl-plus") # 默认用 qwen-vl
STRATEGY_MODEL_NAME = os.getenv("STRATEGY_MODEL_NAME", "deepseek-chat")

# 4. 项目路径配置
OUTPUT_DIR = os.path.join(base_dir, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True) # 如果 outputs 文件夹不存在，自动创建

# 2026年10月20号添加这两行
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY")
ZHIPU_BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"