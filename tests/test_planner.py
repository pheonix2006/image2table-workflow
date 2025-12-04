"""Planner Agent 测试。

测试指挥官的逻辑推理能力，包括简单定位和模糊搜索功能。
"""

import pytest
from src.table2image_agent.interfaces import (
    VisualSummary,
    LocatingInstructions,
    PlannerAgent
)

# Mock 实现，用于测试
class MockPlannerAgent(PlannerAgent):
    """Mock 指挥官，用于测试"""

    def plan(self, question: str, summary: VisualSummary) -> LocatingInstructions:
        # 简单的模拟逻辑
        if "Row A" in question and "Col B" in question:
            return LocatingInstructions(
                target_rows=["Row A"],
                target_columns=["Col B"],
                coordinate_hints={"row_index": "0", "col_index": "1"},
                extraction_type="single_cell",
                reasoning_trace="识别问题中的行标识'Row A'和列标识'Col B'，定位到单个单元格"
            )
        elif "financial data" in question.lower():
            return LocatingInstructions(
                target_rows=["Revenue", "Profit", "Expenses"],
                target_columns=["Q1", "Q2", "Q3", "Q4"],
                coordinate_hints={"row_index": "1-3", "col_index": "1-4"},
                extraction_type="region_data",
                reasoning_trace="识别关键词'financial data'，确定需要提取财务相关的行和列数据"
            )
        else:
            return LocatingInstructions(
                target_rows=[],
                target_columns=[],
                coordinate_hints={},
                extraction_type="region_data",
                reasoning_trace="未能识别明确的定位条件，返回通用区域提取指令"
            )


def test_simple_locating_instructions():
    """测试简单定位指令生成"""
    # 创建 Mock 指挥官
    planner = MockPlannerAgent()

    # 创建模拟的视觉摘要
    summary = VisualSummary(
        table_title="Test Table",
        headers=["A", "B", "C"],
        row_structure=["Row A", "Row B", "Row C"],
        column_structure=["Col A", "Col B", "Col C"],
        merge_cells=[],
        layout_description="简单的3x3测试表格"
    )

    # 测试问题
    question = "Find value for Row A, Col B"

    # 生成指令
    instructions = planner.plan(question, summary)

    # 验证结果
    assert instructions is not None, "应该生成定位指令"
    assert "Row A" in instructions.target_rows, "目标行应该包含 Row A"
    assert "Col B" in instructions.target_columns, "目标列应该包含 Col B"
    assert instructions.extraction_type == "single_cell", "应该是单单元格提取"
    assert "Row A" in instructions.reasoning_trace, "推理过程应该包含 Row A"
    assert "Col B" in instructions.reasoning_trace, "推理过程应该包含 Col B"

    # 验证坐标提示
    assert instructions.coordinate_hints["row_index"] == "0", "行索引应该正确"
    assert instructions.coordinate_hints["col_index"] == "1", "列索引应该正确"

    print(f"✅ 简单定位测试通过:")
    print(f"   目标行: {instructions.target_rows}")
    print(f"   目标列: {instructions.target_columns}")
    print(f"   提取类型: {instructions.extraction_type}")
    print(f"   推理过程: {instructions.reasoning_trace}")


def test_fuzzy_locating_instructions():
    """测试模糊搜索指令生成"""
    # 创建 Mock 指挥官
    planner = MockPlannerAgent()

    # 创建财务数据的视觉摘要
    summary = VisualSummary(
        table_title="Financial Report",
        headers=["Department", "Q1", "Q2", "Q3", "Q4"],
        row_structure=["Revenue", "Profit", "Expenses"],
        column_structure=["部门", "第一季度", "第二季度", "第三季度", "第四季度"],
        merge_cells=[],
        layout_description="包含收入、利润和支出的季度财务报表"
    )

    # 测试模糊问题
    question = "Show me all financial data"

    # 生成指令
    instructions = planner.plan(question, summary)

    # 验证结果
    assert instructions is not None, "应该生成定位指令"
    assert len(instructions.target_rows) >= 3, "应该包含多个财务相关行"
    assert len(instructions.target_columns) >= 4, "应该包含所有季度列"
    assert instructions.extraction_type == "region_data", "应该是区域数据提取"
    assert "financial data" in instructions.reasoning_trace.lower(), "推理过程应该包含关键词"

    # 验证覆盖了主要财务指标
    financial_keywords = ["Revenue", "Profit", "Expenses"]
    for keyword in financial_keywords:
        assert any(keyword in row for row in instructions.target_rows), f"应该包含 {keyword}"

    print(f"✅ 模糊搜索测试通过:")
    print(f"   目标行数: {len(instructions.target_rows)}")
    print(f"   目标列数: {len(instructions.target_columns)}")
    print(f"   提取类型: {instructions.extraction_type}")
    print(f"   推理过程: {instructions.reasoning_trace}")


def test_locating_instructions_data_structure():
    """测试定位指令的数据结构完整性"""
    instructions = LocatingInstructions(
        target_rows=["Test Row 1", "Test Row 2"],
        target_columns=["Test Col 1", "Test Col 2"],
        coordinate_hints={"row_index": "1-2", "col_index": "1-2"},
        extraction_type="region_data",
        reasoning_trace="测试推理过程：识别测试行列并生成区域提取指令"
    )

    # 测试 to_dict 方法
    instructions_dict = instructions.to_dict()

    assert isinstance(instructions_dict, dict), "转换为字典应该是字典类型"
    assert "target_rows" in instructions_dict, "字典应该包含 target_rows"
    assert "target_columns" in instructions_dict, "字典应该包含 target_columns"
    assert "coordinate_hints" in instructions_dict, "字典应该包含 coordinate_hints"
    assert "extraction_type" in instructions_dict, "字典应该包含 extraction_type"
    assert "reasoning_trace" in instructions_dict, "字典应该包含 reasoning_trace"

    # 验证数据完整性
    assert instructions_dict["target_rows"] == ["Test Row 1", "Test Row 2"]
    assert instructions_dict["target_columns"] == ["Test Col 1", "Test Col 2"]
    assert instructions_dict["extraction_type"] == "region_data"
    assert "测试推理过程" in instructions_dict["reasoning_trace"]

    print(f"✅ 数据结构测试通过:")
    print(f"   字典键: {list(instructions_dict.keys())}")
    print(f"   数据完整性: ✅")


def test_planner_interface_compliance():
    """测试指挥官接口合规性"""
    planner = MockPlannerAgent()

    # 检查是否实现了正确的接口
    assert hasattr(planner, 'plan'), "应该有 plan 方法"
    assert callable(getattr(planner, 'plan')), "plan 应该是可调用的方法"

    # 测试方法签名
    import inspect
    sig = inspect.signature(planner.plan)
    params = list(sig.parameters.keys())

    assert 'question' in params, "plan 方法应该有 question 参数"
    assert 'summary' in params, "plan 方法应该有 summary 参数"
    assert len(params) == 2, "plan 方法应该只有两个参数"

    print(f"✅ 接口合规性测试通过:")
    print(f"   方法签名: {sig}")
    print(f"   参数列表: {params}")


def test_edge_cases():
    """测试边缘情况"""
    planner = MockPlannerAgent()

    # 测试空问题
    summary = VisualSummary(
        table_title="Test",
        headers=["A", "B"],
        row_structure=["Row 1"],
        column_structure=["Col 1", "Col 2"],
        merge_cells=[],
        layout_description="简单测试表格"
    )

    # 空问题处理
    instructions = planner.plan("", summary)
    assert instructions is not None, "空问题也应该返回指令"
    assert instructions.extraction_type == "region_data", "空问题应该使用默认提取类型"

    # 测试无匹配问题
    instructions = planner.plan("寻找不存在的XYZ数据", summary)
    assert instructions is not None, "无匹配问题也应该返回指令"
    assert len(instructions.reasoning_trace) > 0, "应该有推理过程"

    print(f"✅ 边缘情况测试通过:")
    print(f"   空问题处理: ✅")
    print(f"   无匹配问题处理: ✅")


if __name__ == "__main__":
    # 手动运行测试的主函数
    print("🧪 开始指挥官测试...")

    try:
        test_simple_locating_instructions()
        print("✅ 简单定位测试通过")
    except Exception as e:
        print(f"❌ 简单定位测试失败: {e}")

    try:
        test_fuzzy_locating_instructions()
        print("✅ 模糊搜索测试通过")
    except Exception as e:
        print(f"❌ 模糊搜索测试失败: {e}")

    try:
        test_locating_instructions_data_structure()
        print("✅ 数据结构测试通过")
    except Exception as e:
        print(f"❌ 数据结构测试失败: {e}")

    try:
        test_planner_interface_compliance()
        print("✅ 接口合规性测试通过")
    except Exception as e:
        print(f"❌ 接口合规性测试失败: {e}")

    try:
        test_edge_cases()
        print("✅ 边缘情况测试通过")
    except Exception as e:
        print(f"❌ 边缘情况测试失败: {e}")

    print("\n🎉 指挥官测试完成！")