import os
import asyncio
import traceback
from openai import OpenAI
from config.settings import DEEPSEEK_API_KEY, STRATEGY_MODEL_NAME


class H5Builder:
    def __init__(self):
        if not DEEPSEEK_API_KEY:
            raise ValueError("❌ 致命错误：未配置 DEEPSEEK_API_KEY！")

        self.client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com/v1"
        )
        self.model = STRATEGY_MODEL_NAME

    # ==================== 生成 H5 代码 ====================
    def generate_h5(self, marketing_plan, image_url="", phone_number="", address=""):
        print("🚀 正在调用 DeepSeek 生成 H5 代码...")
        system_prompt = """
        你是一名精通前端开发和微信营销的专家。
        你的任务是根据给定的营销方案，编写一个单文件的 HTML 页面（内含 CSS 和 JS）。
        要求：
        1. 必须是【单文件 HTML】。
        2. 必须是【移动端优先】设计，适配手机屏幕。
        3. 页面结构必须包含：顶部大标题、核心话术区、限时限量促销活动区（带倒计时效果）、底部行动按钮（一键拨号、地图导航）。
        4. 配色要符合“高转化率”风格（例如红金、黑金）。
        5. 必须包含一段简单的 JavaScript 倒计时逻辑（默认 24 小时）。
        6. 不要包含任何外部的图片链接。
        7. 直接输出 HTML 代码，不要使用 Markdown 代码块包裹。
        """
        user_prompt = f"""
        请根据以下营销方案，生成 H5 页面代码：
        【营销方案内容】：{marketing_plan}
        【自定义配置】：联系电话：{phone_number if phone_number else '400-123-4567'}；门店地址：{address if address else '请在后台配置'}
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=4000
            )
            html_code = response.choices[0].message.content.strip()
            if html_code.startswith("```html"): html_code = html_code[7:]
            if html_code.endswith("```"): html_code = html_code[:-3]
            return html_code
        except Exception as e:
            traceback.print_exc()
            return f"❌ 生成 H5 失败: {str(e)}"

    # ==================== 截图功能 (新增) ====================
    async def _capture_async(self, html_file_path, output_image_path):
        """内部异步截图方法"""
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            # 模拟 iPhone 12
            context = await browser.new_context(
                viewport={'width': 390, 'height': 844},
                device_scale_factor=2,
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
            )
            page = await context.new_page()
            await page.goto(f"file:///{html_file_path}")
            await page.wait_for_timeout(1500)  # 等待倒计时 JS 运行
            await page.screenshot(path=output_image_path, full_page=True)
            await browser.close()

    def generate_poster_image(self, html_file_path, output_image_path):
        """将 HTML 生成长图 (供 UI 调用)"""
        print(f"📸 正在把 H5 页面截成长图: {output_image_path} ...")
        try:
            # 检测 playwright 是否安装
            import playwright
        except ImportError:
            print("❌ 错误：未安装 playwright，无法截图。请运行 pip install playwright && playwright install chromium")
            return False

        try:
            asyncio.run(self._capture_async(html_file_path, output_image_path))
            print("✅ 长图生成成功！")
            return True
        except Exception as e:
            print(f"❌ 长图生成失败: {e}")
            traceback.print_exc()
            return False

