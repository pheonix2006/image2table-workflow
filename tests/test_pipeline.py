"""Full pipeline test with mock implementations."""

from table2image_agent.interfaces import (
    ScoutAgent, PlannerAgent, SniperAgent, CoderAgent,
    VisualSummary, LocatingInstructions, DataPacket, Answer
)
from table2image_agent.orchestrator import Table2ImageOrchestrator


class MockScoutAgent(ScoutAgent):
    """Mock 侦察兵实现"""

    def scan(self, image_path: str) -> VisualSummary:
        """返回预定义的视觉摘要"""
        return VisualSummary(
            table_title="2023年研发部门财务报表",
            headers=["部门", "Q1", "Q2", "Q3", "Q4"],
            row_structure=["部门名", "季度数据"],
            column_structure=["部门", "第一季度", "第二季度", "第三季度", "第四季度"],
            merge_cells=[],
            layout_description="标准的财务报表布局，包含部门列和四个季度的数据列"
        )


class MockPlannerAgent(PlannerAgent):
    """Mock 指挥官实现"""

    def plan(self, question: str, summary: VisualSummary) -> LocatingInstructions:
        """返回预定义的定位指令"""
        return LocatingInstructions(
            target_rows=["研发部"],
            target_columns=["Q1", "Q2"],
            coordinate_hints={"row_index": "1", "col_index": "1-2"},
            extraction_type="region_data"
        )


class MockSniperAgent(SniperAgent):
    """Mock 狙击手实现"""

    def extract(self, image_path: str, instructions: LocatingInstructions) -> DataPacket:
        """返回预定义的数据包"""
        return DataPacket(
            raw_image_path=image_path,
            cropped_region=(100, 50, 300, 150),
            rough_markdown="""
| 部门 | Q1 | Q2 |
|------|----|----|
| 研发部 | 350 | 400 |
            """.strip(),
            structure_info={"format": "markdown_table", "rows": 1, "columns": 2},
            extraction_metadata={
                "method": "ocr",
                "confidence": 0.95,
                "target_region": "研发部 Q1-Q2 数据"
            }
        )


class MockCoderAgent(CoderAgent):
    """Mock 执行者实现"""

    def execute(self, packet: DataPacket, question: str) -> Answer:
        """返回预定义的答案"""
        # 模拟计算：Q1(350) + Q2(400) = 750
        result = "750"
        return Answer(
            result=result,
            calculation_method="加法计算：Q1(350) + Q2(400) = 750",
            confidence=0.98,
            execution_trace=[
                "解析 Markdown 表格数据",
                "提取研发部 Q1 和 Q2 数值：350, 400",
                "执行加法计算：350 + 400 = 750"
            ]
        )




def test_full_workflow_with_mocks():
    """测试完整的工作流"""
    # 创建 Mock 智能体
    scout = MockScoutAgent()
    planner = MockPlannerAgent()
    sniper = MockSniperAgent()
    coder = MockCoderAgent()

    # 创建编排器
    orchestrator = Table2ImageOrchestrator(scout, planner, sniper, coder)

    # 执行工作流
    test_image_path = "test_financial_report.png"
    test_question = "研发部2023年前两个季度的总支出是多少？"

    answer = orchestrator.process(test_image_path, test_question)

    # 验证结果
    assert answer.result == "750"
    assert answer.confidence > 0.95
    assert "750" in answer.calculation_method
    assert len(answer.execution_trace) > 0
    assert answer.error_message is None

    # 验证数据流
    assert isinstance(answer, Answer)
    assert "加法计算" in answer.calculation_method

    print("✅ 全链路测试通过！")


def test_individual_mocks():
    """测试各个 Mock 单独工作"""
    scout = MockScoutAgent()
    summary = scout.scan("test.png")

    assert summary.table_title == "2023年研发部门财务报表"
    assert "研发部门" in summary.table_title
    assert len(summary.headers) == 5  # 部门 + 4个季度

    planner = MockPlannerAgent()
    instructions = planner.plan("测试问题", summary)

    assert "研发部" in instructions.target_rows
    assert "Q1" in instructions.target_columns
    assert instructions.extraction_type == "region_data"

    sniper = MockSniperAgent()
    packet = sniper.extract("test.png", instructions)

    assert "研发部" in packet.rough_markdown
    assert "350" in packet.rough_markdown
    assert packet.cropped_region == (100, 50, 300, 150)

    coder = MockCoderAgent()
    answer = coder.execute(packet, "测试问题")

    assert answer.result == "750"
    assert answer.confidence > 0.95

    print("✅ Mock 单元测试通过！")


if __name__ == "__main__":
    test_individual_mocks()
    test_full_workflow_with_mocks()
    print("🎉 所有测试通过！工作流骨架已搭建完成。")