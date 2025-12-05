"""指挥官 Agent：负责将用户问题转化为具体的定位指令。

使用 LLM 进行逻辑推理，基于 Scout 提供的视觉摘要生成 Sniper 可执行的定位指令。
"""

import json
import os
from typing import Dict, Any, List

from ..interfaces import VisualSummary, LocatingInstructions, PlannerAgent
from ..config import get_planner_config
from ..logger import trace_step


class OpenAIPlannerAgent(PlannerAgent):
    """基于 OpenAI 兼容 LLM 的指挥官实现"""

    def __init__(self):
        """初始化指挥官"""
        # 使用配置管理器获取配置
        config = get_planner_config()

        # 导入 OpenAI 库（延迟导入，避免未安装时的错误）
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("需要安装 openai 库: uv add openai")

        self.client = OpenAI(api_key=config.api_key, base_url=config.base_url)
        self.model_name = config.model_name

        print(f"🧠 指挥官初始化完成，使用模型: {config.model_name}")

    @trace_step("Planner")
    def plan(self, question: str, summary: VisualSummary) -> LocatingInstructions:
        """
        基于问题和视觉摘要生成定位指令

        Args:
            question: 用户问题
            summary: 视觉摘要

        Returns:
            LocatingInstructions: 具体的定位指令
        """
        print(f"🎯 分析问题: {question}")
        print(f"📊 基于视觉摘要: {summary.table_title or '无标题'}")

        # 构建提示词
        messages = self._construct_messages(question, summary)

        try:
            # 调用 LLM
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.1,  # 低温度确保稳定性
                response_format={"type": "json_object"}  # 强制 JSON 输出
            )

            content = response.choices[0].message.content
            instructions_data = self._parse_json_response(content)

            # 创建 LocatingInstructions 对象
            instructions = LocatingInstructions(
                target_rows=instructions_data.get("target_rows", []),
                target_columns=instructions_data.get("target_columns", []),
                coordinate_hints=instructions_data.get("coordinate_hints", {}),
                extraction_type=instructions_data.get("extraction_type", "region_data"),
                reasoning_trace=instructions_data.get("reasoning_trace", "")
            )

            print(f"✅ 指挥分析完成")
            print(f"   目标行: {instructions.target_rows}")
            print(f"   目标列: {instructions.target_columns}")
            print(f"   提取类型: {instructions.extraction_type}")
            print(f"   推理过程: {instructions.reasoning_trace[:100]}...")

            return instructions

        except Exception as e:
            print(f"❌ 指挥分析失败: {e}")
            # 返回默认指令，避免完全失败
            return LocatingInstructions(
                target_rows=[],
                target_columns=[],
                coordinate_hints={},
                extraction_type="region_data",
                reasoning_trace=f"分析失败，使用默认指令: {str(e)}"
            )

    def _construct_messages(self, question: str, summary: VisualSummary) -> List[Dict[str, str]]:
        """
        构建发给 LLM 的消息

        Args:
            question: 用户问题
            summary: 视觉摘要

        Returns:
            List[Dict[str, str]]: 消息列表
        """
        system_prompt = """你是一个专业的表格数据定位专家（Table Locating Specialist）。

你的任务是基于用户的自然语言问题和表格结构摘要，生成精确的数据定位指令。

**重要约束**:
1. 只负责定位数据，**不要试图回答问题本身**
2. 专注于告诉狙击手（Sniper）**去哪里找数据**
3. 根据问题中的实体和条件，确定目标行和列
4. 提供清晰的推理过程，用于调试和验证

**支持的提取类型**:
- "single_cell": 单个单元格（问题指向明确的行和列）
- "row_data": 整行数据（问题要求某行的所有信息）
- "column_data": 整列数据（问题要求某列的所有信息）
- "region_data": 区域数据（问题涉及多行多列的交叉数据）

**输出格式**: 严格按照以下 JSON Schema 输出：
```json
{
  "target_rows": ["目标行描述列表"],
  "target_columns": ["目标列描述列表"],
  "coordinate_hints": {"row_index": "行范围", "col_index": "列范围"},
  "extraction_type": "提取类型",
  "reasoning_trace": "详细的推理过程说明"
}
```"""

        user_prompt = f"""请分析以下用户问题并生成定位指令：

**用户问题**:
{question}

**表格结构摘要**:
- 表格标题: {summary.table_title or '无标题'}
- 表头: {', '.join(summary.headers)}
- 行结构: {', '.join(summary.row_structure)}
- 列结构: {', '.join(summary.column_structure)}
- 布局描述: {summary.layout_description}
- 合并单元格: {len(summary.merge_cells)} 个

**分析要求**:
1. 识别问题中的关键实体（如行名、列名、数值等）
2. 在表格结构中找到对应的行和列
3. 确定需要提取的数据类型
4. 提供详细的推理过程

请根据上述信息生成精确的定位指令。"""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """
        解析 LLM 返回的 JSON 响应

        Args:
            content: LLM 返回的 JSON 字符串

        Returns:
            Dict[str, Any]: 解析后的字典
        """
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            # 尝试修复常见的 JSON 错误
            try:
                # 移除可能的 markdown 标记
                cleaned_content = content.strip()
                if cleaned_content.startswith('```json'):
                    cleaned_content = cleaned_content[7:]
                if cleaned_content.endswith('```'):
                    cleaned_content = cleaned_content[:-3]
                cleaned_content = cleaned_content.strip()

                return json.loads(cleaned_content)
            except:
                raise ValueError(f"无法解析 JSON 响应: {e}\n原始内容: {content}")


class MockPlannerAgent(PlannerAgent):
    """Mock 指挥官，用于测试和开发"""

    def plan(self, question: str, summary: VisualSummary) -> LocatingInstructions:
        """
        Mock 实现的定位指令生成

        Args:
            question: 用户问题
            summary: 视觉摘要

        Returns:
            LocatingInstructions: 模拟的定位指令
        """
        # 简单的关键词匹配逻辑
        question_lower = question.lower()

        # 检查单单元格请求
        if "row a" in question_lower and "col b" in question_lower:
            return LocatingInstructions(
                target_rows=["Row A"],
                target_columns=["Col B"],
                coordinate_hints={"row_index": "0", "col_index": "1"},
                extraction_type="single_cell",
                reasoning_trace="识别问题中的行标识'Row A'和列标识'Col B'，定位到单个单元格"
            )

        # 检查模糊财务请求
        if any(keyword in question_lower for keyword in ["financial", "finance", "money", "revenue", "profit"]):
            # 假设财务相关的行和列
            financial_rows = [row for row in summary.row_structure if any(
                keyword in row.lower() for keyword in ["revenue", "profit", "income", "expense"]
            )]
            if not financial_rows:
                financial_rows = summary.row_structure[:3]  # 默认前3行

            return LocatingInstructions(
                target_rows=financial_rows,
                target_columns=summary.column_structure[1:4] if len(summary.column_structure) > 4 else summary.column_structure[1:],
                coordinate_hints={"row_index": "1-3", "col_index": "1-4"},
                extraction_type="region_data",
                reasoning_trace="识别关键词'financial'，确定需要提取财务相关的行和列数据"
            )

        # 默认情况：返回通用区域提取
        return LocatingInstructions(
            target_rows=summary.row_structure,
            target_columns=summary.column_structure,
            coordinate_hints={"row_index": "1-" + str(len(summary.row_structure)), "col_index": "1-" + str(len(summary.column_structure))},
            extraction_type="region_data",
            reasoning_trace="无法识别明确的定位条件，返回全表区域提取指令"
        )