"""视觉侦察兵：使用 VLM 分析表格结构。

负责对输入的表格图片进行结构分析，生成 VisualSummary。
专注于表格的结构信息，不提取具体数值数据。
"""

import base64
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Tuple

from dotenv import load_dotenv
from openai import OpenAI

from ..interfaces import ScoutAgent, VisualSummary

# 加载环境变量
load_dotenv()


class OpenAIScoutAgent(ScoutAgent):
    """基于 OpenAI VLM 的视觉侦察兵实现"""

    def __init__(self):
        """初始化 OpenAI 客户端"""
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o")  # 新增模型名称配置

        if not api_key:
            raise ValueError("未找到 OPENAI_API_KEY 环境变量")

        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )

        # 保存模型名称用于后续 API 调用
        self.model_name = model_name

        # 系统提示词：专注于结构分析
        self.system_prompt = """你是一名专业的表格结构分析师（Structural Analyst）。

你的任务是分析提供的表格图片，输出一个 JSON 对象来描述表格的结构信息。

**重要约束：**
1. 只关注表格的结构（Structure）和层级（Hierarchy），不要提取具体的数值数据
2. 识别表格的标题、表头、行列结构
3. 注意合并单元格的情况
4. 提供整体布局的描述

**输出格式：**
请严格按照以下 JSON Schema 输出：
{
    "table_title": "表格的标题",
    "headers": ["表头1", "表头2", "表头3"],
    "row_structure": ["行结构描述1", "行结构描述2"],
    "column_structure": ["列结构描述1", "列结构描述2"],
    "merge_cells": [[row_start, col_start, row_end, col_end]],
    "layout_description": "表格布局的整体描述"
}

**字段说明：**
- table_title: 表格的标题
- headers: 完整的表头列表
- row_structure: 行的结构描述，如 ["部门名", "季度数据"]
- column_structure: 列的结构描述，如 ["部门", "Q1", "Q2", "Q3", "Q4"]
- merge_cells: 合并单元格的坐标列表 (row_start, col_start, row_end, col_end)
- layout_description: 表格布局的整体描述

请确保输出是有效的 JSON 格式，不要包含任何解释性文本。"""

    def _encode_image_to_base64(self, image_path: str) -> str:
        """将图片编码为 base64"""
        image_path = Path(image_path)

        if not image_path.exists():
            raise FileNotFoundError(f"图片文件不存在: {image_path}")

        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def _construct_messages(self, image_base64: str) -> List[Dict[str, Any]]:
        """构造 OpenAI ChatCompletion 消息"""
        return [
            {
                "role": "system",
                "content": self.system_prompt
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请分析这个表格图片的结构信息。"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base64}",
                            "detail": "high"
                        }
                    }
                ]
            }
        ]

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """解析 JSON 响应"""
        try:
            # 清理可能的 markdown 代码块
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 解析失败: {e}\n原始内容: {content}")

    def scan(self, image_path: str) -> VisualSummary:
        """
        扫描图像，生成视觉摘要

        Args:
            image_path: 图像文件路径

        Returns:
            VisualSummary: 表格结构的视觉摘要
        """
        if not image_path:
            raise ValueError("图像路径不能为空")

        try:
            # 编码图片
            print("🔍 正在编码图片...")
            image_base64 = self._encode_image_to_base64(image_path)

            # 构造消息
            messages = self._construct_messages(image_base64)

            # 调用 OpenAI API
            print(f"🧠 正在调用 {self.model_name} VLM 分析表格结构...")
            response = self.client.chat.completions.create(
                model=self.model_name,  # 使用配置的模型进行视觉分析
                messages=messages,
                max_tokens=1500,
                temperature=0.1,  # 低温度确保输出稳定
                response_format={"type": "json_object"}
            )

            # 解析响应
            content = response.choices[0].message.content
            result_dict = self._parse_json_response(content)

            print("✅ 表格结构分析完成")
            print(f"   检测到标题: {result_dict.get('table_title', 'N/A')}")
            print(f"   检测到 {len(result_dict.get('headers', []))} 个表头")
            print(f"   合并单元格: {len(result_dict.get('merge_cells', []))} 个")

            # 构建 VisualSummary 对象
            return VisualSummary(
                table_title=result_dict.get("table_title", ""),
                headers=result_dict.get("headers", []),
                row_structure=result_dict.get("row_structure", []),
                column_structure=result_dict.get("column_structure", []),
                merge_cells=result_dict.get("merge_cells", []),
                layout_description=result_dict.get("layout_description", "")
            )

        except Exception as e:
            error_msg = f"Scout Agent 扫描失败: {e}"
            print(f"❌ {error_msg}")
            raise RuntimeError(error_msg) from e