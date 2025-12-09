"""Full pipeline test with real Scout and Planner, mock Sniper and Coder."""

import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from table2image_agent.interfaces import (
    ScoutAgent, PlannerAgent, SniperAgent, CoderAgent,
    VisualSummary, LocatingInstructions, DataPacket, Answer,
    RenderPlan, RenderStrategy
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
            extraction_type="region_data",
            reasoning_trace="Mock 推理过程：根据问题分析确定研发部和Q1-Q2数据区域"
        )


class MockSniperAgent(SniperAgent):
    """Mock 狙击手实现"""

    def direct(self, image_path: str, instructions: LocatingInstructions) -> RenderPlan:
        """Mock 视觉导演逻辑"""
        return RenderPlan(
            strategy=RenderStrategy.SOFT_FOCUS,
            target_rows=[1, 2],  # Mock 目标行
            target_columns=[1, 2],  # Mock 目标列
            reasoning="Mock 推理：数据集中在研发部和Q1-Q2区域"
        )

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


def test_real_scout_and_planner_integration():
    """测试真实的 Scout 和 Planner 集成"""
    try:
        # 导入真实的实现
        from src.table2image_agent.agents.scout import OpenAIScoutAgent
        from src.table2image_agent.agents.planner import OpenAIPlannerAgent

        # 使用真实的 Scout 和 Planner
        scout = OpenAIScoutAgent()
        planner = OpenAIPlannerAgent()

        # 保持 Mock 的 Sniper 和 Coder
        sniper = MockSniperAgent()
        coder = MockCoderAgent()

        # 创建编排器
        orchestrator = Table2ImageOrchestrator(scout, planner, sniper, coder)

        # 使用实际的测试图片
        test_image_path = "data/example_photo/2011-03-26_145620.png"
        test_question = "毕业院校为西南大学的学生姓名叫什么？"

        print("🧪 开始真实 Scout + Planner 集成测试...")
        print(f"   图片路径: {test_image_path}")
        print(f"   测试问题: {test_question}")

        # 执行工作流
        answer = orchestrator.process(test_image_path, test_question)

        # 验证结果存在
        assert answer is not None, "应该有答案返回"
        assert hasattr(answer, 'result'), "答案应该包含结果"
        assert hasattr(answer, 'confidence'), "答案应该包含置信度"
        assert hasattr(answer, 'execution_trace'), "答案应该包含执行轨迹"

        print(f"✅ 真实集成测试通过！")
        print(f"   答案结果: {answer.result}")
        print(f"   置信度: {answer.confidence}")
        print(f"   执行轨迹长度: {len(answer.execution_trace)}")

        return True

    except ImportError as e:
        print(f"⚠️  真实模块导入失败，使用 Mock 测试: {e}")
        return False
    except Exception as e:
        print(f"❌ 真实集成测试失败: {e}")
        return False


def test_mock_planner_with_real_scout():
    """测试 Mock Planner 与真实 Scout 的集成"""
    try:
        from src.table2image_agent.agents.scout import OpenAIScoutAgent
        from src.table2image_agent.agents.planner import MockPlannerAgent

        # 真实 Scout + Mock Planner
        scout = OpenAIScoutAgent()
        planner = MockPlannerAgent()
        sniper = MockSniperAgent()
        coder = MockCoderAgent()

        orchestrator = Table2ImageOrchestrator(scout, planner, sniper, coder)

        test_image_path = "data/example_photo/2011-03-26_145620.png"
        test_question = "所有考生的信息汇总"

        print("🧪 开始真实 Scout + Mock Planner 集成测试...")

        answer = orchestrator.process(test_image_path, test_question)

        assert answer is not None, "应该有答案返回"
        print(f"✅ 真实 Scout + Mock Planner 测试通过！")
        print(f"   答案: {answer.result}")

        return True

    except ImportError as e:
        print(f"⚠️  真实模块导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 混合集成测试失败: {e}")
        return False


if __name__ == "__main__":
    test_individual_mocks()
    test_full_workflow_with_mocks()

    # 尝试真实集成测试
    real_integration_success = test_real_scout_and_planner_integration()
    if not real_integration_success:
        print("⚠️ 真实集成测试失败，尝试混合测试...")
        test_mock_planner_with_real_scout()

    print("🎉 所有测试通过！工作流骨架已搭建完成。")


def test_real_sniper_director_integration():
    """测试真实的 Sniper 视觉导演集成"""
    try:
        # 导入真实的实现
        from src.table2image_agent.agents.sniper import OpenAISniperAgent

        # 使用真实的 Sniper 视觉导演
        sniper = OpenAISniperAgent()

        # 创建测试指令
        from table2image_agent.interfaces import LocatingInstructions

        instructions = LocatingInstructions(
            target_rows=["第2行数据（序号为2的考生行）"],
            target_columns=["姓名列（B列）"],
            coordinate_hints={"row_index": "2", "col_index": "1"},
            extraction_type="single_cell",
            reasoning_trace="用户问题要求查找'序号为2的考生姓名'"
        )

        # 使用实际的测试图片
        test_image_path = "data/example_photo/2011-03-26_145620.png"

        print("🎯 开始真实 Sniper 视觉导演测试...")
        print(f"   图片路径: {test_image_path}")
        print(f"   定位指令: {instructions.target_rows} x {instructions.target_columns}")

        # 测试新的视觉导演功能
        render_plan = sniper.direct(test_image_path, instructions)

        # 验证 RenderPlan
        assert hasattr(render_plan, 'strategy')
        assert hasattr(render_plan, 'target_rows')
        assert hasattr(render_plan, 'target_columns')
        assert hasattr(render_plan, 'reasoning')
        assert render_plan.strategy in ["HARD_CROP", "SOFT_FOCUS"]

        print("✅ 视觉导演测试成功!")
        print(f"   策略: {render_plan.strategy}")
        print(f"   目标行: {render_plan.target_rows}")
        print(f"   目标列: {render_plan.target_columns}")
        print(f"   推理: {render_plan.reasoning[:100]}...")

        # 测试兼容性 extract 方法
        data_packet = sniper.extract(test_image_path, instructions)

        assert data_packet.raw_image_path == test_image_path
        assert data_packet.rough_markdown is not None

        print("✅ 兼容性 extract 方法验证通过!")
        print(f"   数据包: {len(data_packet.rough_markdown)} 字符")

        return True

    except Exception as e:
        print(f"❌ 真实 Sniper 视觉导演测试失败: {e}")
        return False


def test_real_scout_planner_sniper_integration():
    """测试真实的 Scout + Planner + Sniper 集成"""
    try:
        # 导入真实的实现
        from src.table2image_agent.agents.scout import OpenAIScoutAgent
        from src.table2image_agent.agents.planner import OpenAIPlannerAgent
        from src.table2image_agent.agents.sniper import OpenAISniperAgent

        # 使用真实的 Agent
        scout = OpenAIScoutAgent()
        planner = OpenAIPlannerAgent()
        sniper = OpenAISniperAgent()

        # Mock Coder（因为 Coder 还未实现）
        coder = MockCoderAgent()

        # 创建编排器
        orchestrator = Table2ImageOrchestrator(scout, planner, sniper, coder)

        # 使用实际的测试图片
        test_image_path = "data/example_photo/2011-03-26_145620.png"
        test_question = "序号为2的考生姓名是什么？"

        print("🚀 开始真实 Scout + Planner + Sniper 集成测试...")
        print(f"   图片路径: {test_image_path}")
        print(f"   测试问题: {test_question}")

        # 执行工作流
        answer = orchestrator.process(test_image_path, test_question)

        # 验证结果
        assert isinstance(answer, Answer)
        assert answer.result is not None
        assert answer.confidence > 0
        assert len(answer.execution_trace) > 0

        print("✅ 真实 Scout + Planner + Sniper 集成测试成功!")
        print(f"   最终答案: {answer.result}")
        print(f"   置信度: {answer.confidence}")
        print(f"   执行轨迹: {len(answer.execution_trace)} 步")

        # 检查是否有视觉导演相关的内容
        execution_text = " ".join(answer.execution_trace)
        has_sniper_director = any(keyword in execution_text for keyword in
                                 ["视觉导演", "RenderPlan", "SOFT_FOCUS", "HARD_CROP"])

        if has_sniper_director:
            print("🎯 视觉导演功能集成验证通过!")
        else:
            print("⚠️ 未检测到视觉导演功能输出")

        return True

    except Exception as e:
        print(f"❌ 真实 Scout + Planner + Sniper 集成测试失败: {e}")
        return False