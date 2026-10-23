import os
import base64 #把二进制数据音视频文件，转成由 64 个可打印字符（A-Z, a-z, 0-9, +, /）组成的文本字符串。
import traceback #当程序发生异常（报错）时，它能帮你打印出完整的“错误堆栈信息”
from openai import OpenAI #OpenAI 是一个客户端类（Client）。当你实例化它时，它就相当于在代码里打通了一条通往大模型服务器的“电话线”。

# 从配置文件中导入
from config.settings import DASHSCOPE_API_KEY, VISION_MODEL_NAME


class VisionAgent:
    def __init__(self):
        """
        初始化视觉分析 Agent
        """
        if not DASHSCOPE_API_KEY:
            raise ValueError("❌ 致命错误：未在 .env 文件中找到 DASHSCOPE_API_KEY！请先配置。")

        self.api_key = DASHSCOPE_API_KEY
        # 阿里云百炼的 OpenAI 兼容接口地址
        self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        self.model = VISION_MODEL_NAME

        # 初始化客户端
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def _encode_image(self, image_path):
        """将本地图片编码为 base64 字符串"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def analyze_image(self, image_path):
        """
        分析图片，提取关键营销信息
        """
        if not os.path.exists(image_path):
            return f"❌ 错误：找不到图片 {image_path}，请检查路径。"

        # 核心 Prompt
        system_prompt = "你是一名资深的实体店营销专家。你的任务是分析竞争对手的营销海报/图片，提取关键信息。"

        user_prompt = """
        请仔细分析这张营销图片，提取以下核心信息并以 Markdown 列表的格式输出：
        1. 【核心卖点】：产品/服务的核心功能与最大优势。
        2. 【目标人群】：定位了哪些具体的人群，抓住了什么痛点。
        3. 【营销策略】：使用了什么促销手段（如打折、赠送、限时等）。
        4. 【视觉风格】：图片的排版、主色调、情绪氛围。
        5. 【文案话术】：提取图片中最吸引人的一句广告语。

        注意：仅提取图里实际存在的信息，不要凭空捏造。如果某项信息缺失，请注明“未提及”。
        """

        try:
            print(f"📸 正在读取图片: {image_path}")
            base64_image = self._encode_image(image_path)

            print(f"🚀 正在调用 {self.model} 进行分析，请稍候...")
            # 调用接口，加 timeout 防止无限等待
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.2,
                max_tokens=1000,
                timeout=30  # 超过30秒没反应则报错，防止死机
            )

            result = response.choices[0].message.content
            return result

        except Exception as e:
            print("\n" + "=" * 50)
            print("❌ API 调用发生异常！详细错误信息如下：")
            traceback.print_exc()
            print("=" * 50 + "\n")
            return f"❌ 请求失败: {str(e)}"


# ==================== 测试代码 ====================
if __name__ == "__main__":
    print("=" * 50)
    print("🚀 视觉分析 Agent 测试启动")
    print("=" * 50)

    # 【关键修改】：这里改为让程序询问你路径，而不是写死
    # 这样你可以直接把图片拖进控制台，就不怕找不到了
    print("💡 请在下方控制台输入图片的完整路径，或者直接把图片拖拽到这里，然后按回车：")
    user_input_path = input("👉 图片路径: ").strip()

    # 去除可能自带的引号（拖拽文件时系统有时会自动加上）
    user_input_path = user_input_path.strip('"').strip("'")

    if not user_input_path:
        print("❌ 错误：没有输入路径，程序退出。")
    else:
        print(f"\n🔍 你输入的路径是: {user_input_path}")

        # 检查文件是否存在
        if not os.path.exists(user_input_path):
            print(f"❌ 致命错误：找不到该文件！请检查路径拼写是否正确。")
        else:
            print("✅ 图片文件存在，准备开始分析...\n")
            try:
                agent = VisionAgent()
                result = agent.analyze_image(user_input_path)

                print("\n================ 📋 提取结果 ================\n")
                print(result)

            except Exception as e:
                print(f"\n❌ 初始化或运行崩溃: {e}")