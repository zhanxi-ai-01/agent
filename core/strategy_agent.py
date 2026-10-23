import sys
import os
# 👇 把项目根目录加入 Python 搜索路径，彻底解决找不到 rag/config 的问题
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import traceback
from openai import OpenAI

# 导入新版 Milvus 检索函数（替代旧版 get_vector_store）
from rag.vector_store import search_knowledge

# 导入配置项（根据你项目的实际配置文件名调整，如果名字不同请告诉我）
from config.settings import DEEPSEEK_API_KEY, STRATEGY_MODEL_NAME

class StrategyAgent:
    def __init__(self):
        if not DEEPSEEK_API_KEY:
            raise ValueError("❌ 致命错误：未配置 DEEPSEEK_API_KEY！请去 platform.deepseek.com 申请并填入 .env 文件。")

        # 初始化 DeepSeek 客户端
        self.client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com/v1"
        )
        self.model = STRATEGY_MODEL_NAME

        # 注意：新版 Milvus 方案不需要在初始化时加载 vector_store
        # 直接调用 search_knowledge 函数即可（它会自动处理连接和模型加载）
        print("📡 知识库连接已就绪（Milvus + 阿里云 Embedding）")

    def generate_plan(self, competitor_analysis):
        """
        根据对手分析结果 + 知识库，生成营销方案
        """
        print("🔍 正在《成交心理学》知识库中检索相关理论...")

        # 1. 检索（使用新的 Milvus 检索函数）
        query = competitor_analysis[:200]
        results = search_knowledge(query, limit=3)  # 新版返回的是 Milvus 结果列表

        # 从 Milvus 返回的字典结构中提取文本内容
        context = "\n\n".join([res['entity']['text'] for res in results])
        print(f"📖 已检索到 {len(results)} 段相关理论。")

        # 2. 构建 Prompt
        system_prompt = "你是一名精通《成交心理学》的实体店营销策划专家。你的任务是根据对手的营销策略，结合成交心理学知识，为我的店铺制定反击方案。"

        user_prompt = (
            "以下是对于营销图片的分析结果：\n"
            f"{competitor_analysis}\n\n"

            "以下是《成交心理学》和《嗅觉营销心理学》的相关理论参考：\n"
            f"{context}\n\n"

            "【特别指令】：请务必结合以上参考理论，特别是《嗅觉营销心理学》。在制定引流或体验环节时，尝试加入“嗅觉记忆锚点”（如独特的门店香氛），增强客户情感留存。\n\n"

            "请综合以上信息，为我的实体店生成一份完整的营销方案。要求：\n"
            "1. 【差异化定位】：指出对手的弱点，明确我们的差异化优势。\n"
            "2. 【核心话术】：设计3条针对目标人群的成交话术，必须运用成交心理学原理。\n"
            "3. 【促销活动】：设计一个具体的活动（包括活动形式、门槛、限时限量机制）。\n"
            "4. 【视觉建议】：给出我们自己的海报视觉设计建议（文字、配色、构图）。\n"
            "5. 【朋友圈/微信群文案】：写出可以直接复制发送的3条朋友圈营销文案。\n\n"

            "输出格式为 Markdown，语言需具备实战性、煽动性，避免空泛的理论。"
        )





        # user_prompt = f"""
        # 以下是对手营销图片的分析结果：
        # {competitor_analysis}
        #
        # 以下是《成交心理学》的相关理论参考：
        # {context}
        #
        # 请综合以上信息，为我的实体店生成一份完整的营销方案。要求：
        # 1. 【差异化定位】：指出对手的弱点，明确我们的差异化优势。
        # 2. 【核心话术】：设计3条针对目标人群的成交话术，必须运用成交心理学原理。
        # 3. 【促销活动】：设计一个具体的活动（包括活动形式、门槛、限时限量机制）。
        # 4. 【视觉建议】：给出我们自己的海报视觉设计建议（文字、配色、构图）。
        # 5. 【朋友圈/微信群文案】：写出可以直接复制发送的3条朋友圈营销文案。
        #
        # 输出格式为 Markdown，语言需具备实战性、煽动性，避免空泛的理论。
        # """

        print(f"🚀 正在调用 {self.model} 生成最终方案...")
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            # 修复了原来多出来的 f
            return response.choices[0].message.content

        except Exception as e:
            traceback.print_exc()
            return f"❌ 生成方案失败: {str(e)}"

# ==================== 测试代码 ====================
if __name__ == "__main__":
    test_competitor_info = """
    1. 【核心卖点】：越野能力强，具备全路况适应能力。
    2. 【目标人群】：追求个性表达、渴望突破城市束缚、向往自由驰骋的“行者”精神。
    3. 【营销策略】：2016年12月12日北京开售，前100名奖励1000元现金（早鸟奖励）。
    4. 【视觉风格】：明黄色车身+蓝灰天空背景+绿植点缀，高对比度，强调“故事感”与“生活方式”。
    5. 【文案话术】：“活出你的野性”。
    """

    try:
        agent = StrategyAgent()
        plan = agent.generate_plan(test_competitor_info)
        print("\n================ 📋 生成方案 ================\n")
        print(plan)
    except Exception as e:
        print(f"\n❌ 运行失败: {e}")