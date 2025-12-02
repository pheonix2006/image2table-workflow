"""工作流编排器：协调各个智能体的执行流程。"""

from typing import Any, Dict
from .interfaces import (
    ScoutAgent, PlannerAgent, SniperAgent, CoderAgent,
    VisualSummary, LocatingInstructions, DataPacket, Answer
)


class Table2ImageOrchestrator:
    """编排器：串联四个智能体的工作流"""

    def __init__(self, scout: ScoutAgent, planner: PlannerAgent,
                 sniper: SniperAgent, coder: CoderAgent):
        """
        初始化编排器

        Args:
            scout: 侦察兵智能体
            planner: 指挥官智能体
            sniper: 狙击手智能体
            coder: 执行者智能体
        """
        self.scout = scout
        self.planner = planner
        self.sniper = sniper
        self.coder = coder

    def process(self, image_path: str, question: str) -> Answer:
        """
        执行完整的工作流

        Args:
            image_path: 图像路径
            question: 用户问题

        Returns:
            Answer: 最终答案

        Raises:
            ValueError: 当输入参数无效时
            RuntimeError: 当处理过程中出现错误时
        """
        if not image_path:
            raise ValueError("图像路径不能为空")
        if not question:
            raise ValueError("问题不能为空")

        try:
            # Step 1: 侦察兵扫描表格结构
            print("🔍 步骤 1: 侦察兵扫描表格结构...")
            summary = self.scout.scan(image_path)
            print(f"   ✅ 扫描完成：{summary.table_title}")

            # Step 2: 指挥官分析并生成定位指令
            print("🧠 步骤 2: 指挥官分析问题并生成定位指令...")
            instructions = self.planner.plan(question, summary)
            print(f"   ✅ 规划完成：提取 {instructions.target_rows} 的 {instructions.target_columns} 数据")

            # Step 3: 狙击手精确提取数据
            print("🎯 步骤 3: 狙击手精确提取数据...")
            packet = self.sniper.extract(image_path, instructions)
            print(f"   ✅ 提取完成：获得包含 {len(packet.rough_markdown)} 字符的数据包")

            # Step 4: 执行者计算最终答案
            print("💻 步骤 4: 执行者计算最终答案...")
            answer = self.coder.execute(packet, question)
            print(f"   ✅ 计算完成：答案是 {answer.result}")

            return answer

        except Exception as e:
            print(f"❌ 工作流执行失败: {e}")
            raise RuntimeError(f"处理失败: {e}")

    def get_workflow_info(self) -> Dict[str, Any]:
        """
        获取工作流信息

        Returns:
            Dict[str, Any]: 各个组件的信息
        """
        return {
            "components": {
                "scout": self.scout.__class__.__name__,
                "planner": self.planner.__class__.__name__,
                "sniper": self.sniper.__class__.__name__,
                "coder": self.coder.__class__.__name__
            },
            "workflow_stages": [
                "Scout: 扫描表格结构",
                "Planner: 生成定位指令",
                "Sniper: 精确数据提取",
                "Coder: 执行计算任务"
            ],
            "description": "Table2Image Multi-Agent System 工作流编排器"
        }