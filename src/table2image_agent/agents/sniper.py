"""Sniper Agent Implementation - 视觉导演逻辑

 Sniper Agent 从直接数据提取升级为"视觉导演"：
 - 分析图像和 Planner 指令
 - 决定渲染策略 (HARD_CROP vs SOFT_FOCUS)
 - 输出结构化的 RenderPlan
"""

import json
import os
from typing import Dict, Any, List
from pathlib import Path

from openai import OpenAI
from dotenv import load_dotenv

from ..interfaces import (
    SniperAgent, RenderPlan, RenderStrategy,
    LocatingInstructions, DataPacket
)

# 加载环境变量
load_dotenv()


class OpenAISniperAgent(SniperAgent):
    """基于 OpenAI 兼容 API 的视觉导演 Sniper Agent"""

    def __init__(self):
        """初始化 Sniper Agent"""
        self.model_name = os.getenv("SNIPER_MODEL", "qwen3-vl-flash")
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")

        if not self.api_key:
            raise ValueError("SNIPER_API_KEY not found in environment variables")

        # 初始化 OpenAI 客户端
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

        print(f"🎯 视觉导演初始化完成，使用模型: {self.model_name}")

    def direct(self, image_path: str, instructions: LocatingInstructions) -> RenderPlan:
        """
        视觉导演：分析图像和指令，生成渲染计划

        Args:
            image_path: 原始图像路径
            instructions: 定位指令

        Returns:
            RenderPlan: 渲染计划，包含策略和目标区域
        """
        print(f"🎯 分析图像: {image_path}")
        print(f"📋 定位指令: {instructions.target_rows} x {instructions.target_columns}")

        try:
            # 构建视觉导演的提示词
            messages = self._construct_vision_director_messages(image_path, instructions)

            # 调用 VLM 分析
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            # 解析响应
            plan_data = self._parse_json_response(response.choices[0].message.content)

            # 创建 RenderPlan
            plan = RenderPlan(
                strategy=RenderStrategy(plan_data["strategy"]),
                target_rows=plan_data["target_rows"],
                target_columns=plan_data["target_columns"],
                reasoning=plan_data["reasoning"]
            )

            print(f"✅ 视觉导演完成: {plan.strategy.value}")
            print(f"   目标行: {plan.target_rows}")
            print(f"   目标列: {plan.target_columns}")
            print(f"   推理: {plan.reasoning[:100]}...")

            return plan

        except Exception as e:
            print(f"❌ 视觉导演分析失败: {str(e)}")
            # 兜底策略：默认使用 SOFT_FOCUS
            return self._get_fallback_plan(instructions, str(e))

    def extract(self, image_path: str, instructions: LocatingInstructions) -> DataPacket:
        """
        保留原有的数据提取接口兼容性

        Args:
            image_path: 原始图像路径
            instructions: 定位指令

        Returns:
            DataPacket: 包含提取数据的包
        """
        # 获取渲染计划
        plan = self.direct(image_path, instructions)

        # 基于计划执行实际提取（这里简化为 Mock 实现）
        # 真实实现需要根据 plan.strategy 执行不同的图像处理
        return DataPacket(
            raw_image_path=image_path,
            cropped_region=None,  # 根据 plan.strategy 计算裁剪区域
            rough_markdown=self._mock_ocr_extraction(plan),
            structure_info={"render_plan": plan.to_dict()},
            extraction_metadata={
                "strategy": plan.strategy.value,
                "target_rows": plan.target_rows,
                "target_columns": plan.target_columns
            }
        )

    def _construct_vision_director_messages(self, image_path: str, instructions: LocatingInstructions) -> List[Dict[str, Any]]:
        """构建视觉导演的提示词"""

        # 读取图像为 base64
        with open(image_path, "rb") as image_file:
            import base64
            image_base64 = base64.b64encode(image_file.read()).decode('utf-8')

        messages = [
            {
                "role": "system",
                "content": """你是专业的视觉注意力导演（Visual Attention Director）。你的任务是分析表格图像，确定最佳的数据区域渲染策略。

你需要：
1. 仔细观察表格图像的结构
2. 根据定位指令确定目标数据的行、列位置（从0开始索引）
3. 选择最合适的渲染策略：

- HARD_CROP: 目标数据极其分散（如第1行和第100行），中间包含大量无关数据，适合裁剪后拼接
- SOFT_FOCUS: 目标数据相对集中，需要保留周边上下文（如表头），将背景虚化/缩小

输出严格的JSON格式：
{
    "strategy": "HARD_CROP 或 SOFT_FOCUS",
    "target_rows": [目标行索引列表],
    "target_columns": [目标列索引列表],
    "reasoning": "选择此策略的详细推理过程"
}"""
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""请分析这个表格图像，根据以下定位指令生成渲染计划：

定位指令：
- 目标行: {instructions.target_rows}
- 目标列: {instructions.target_columns}
- 提取类型: {instructions.extraction_type}
- 推理过程: {instructions.reasoning_trace}

请确定具体的行列索引（从0开始）和最佳渲染策略。"""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base64}"
                        }
                    }
                ]
            }
        ]

        return messages

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """解析 VLM 的 JSON 响应"""
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"❌ JSON 解析失败: {e}")
            print(f"原始内容: {content}")
            raise ValueError(f"Invalid JSON response: {e}")

    def _get_fallback_plan(self, instructions: LocatingInstructions, error_msg: str) -> RenderPlan:
        """获取兜底渲染计划"""
        return RenderPlan(
            strategy=RenderStrategy.SOFT_FOCUS,
            target_rows=[0, 1, 2],  # 默认前3行
            target_columns=[0, 1, 2],  # 默认前3列
            reasoning=f"分析失败，使用默认策略: {error_msg}"
        )

    def _mock_ocr_extraction(self, plan: RenderPlan) -> str:
        """Mock OCR 提取（真实实现需要集成 OCR）"""
        # 这里返回示例 Markdown 格式
        target_info = f"行{plan.target_rows} x 列{plan.target_columns}"
        return f"""
## 提取区域 ({target_info})

| 列1 | 列2 | 列3 |
|-----|-----|-----|
| 数据1 | 数据2 | 数据3 |
| 数据4 | 数据5 | 数据6 |

*渲染策略: {plan.strategy.value}*
*推理: {plan.reasoning}*
        """.strip()


class MockSniperAgent(SniperAgent):
    """Mock Sniper Agent 用于测试"""

    def direct(self, image_path: str, instructions: LocatingInstructions) -> RenderPlan:
        """Mock 视觉导演逻辑"""
        # 简单的启发式决策
        if "100" in str(instructions.target_rows) or "50" in str(instructions.target_rows):
            # 如果行号很大，认为数据分散
            strategy = RenderStrategy.HARD_CROP
            reasoning = "检测到大行号，数据分散，使用裁剪拼接策略"
        else:
            # 默认使用软焦点
            strategy = RenderStrategy.SOFT_FOCUS
            reasoning = "数据相对集中，保留上下文，使用软焦点策略"

        return RenderPlan(
            strategy=strategy,
            target_rows=[0, 1, 2],  # Mock 前3行
            target_columns=[0, 1],   # Mock 前2列
            reasoning=reasoning
        )

    def extract(self, image_path: str, instructions: LocatingInstructions) -> DataPacket:
        """Mock 数据提取"""
        plan = self.direct(image_path, instructions)

        return DataPacket(
            raw_image_path=image_path,
            cropped_region=(0, 0, 100, 100),
            rough_markdown="Mock OCR 提取结果",
            structure_info={"mock": True, "plan": plan.to_dict()},
            extraction_metadata={"mock": True}
        )