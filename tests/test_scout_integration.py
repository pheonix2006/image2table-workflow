"""集成测试：真实的 Scout Agent API 调用测试。

注意：此测试需要真实的 API Key 才能运行。
请先创建 .env 文件并配置 OPENAI_API_KEY。
"""

import os
import pytest
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from table2image_agent.interfaces import VisualSummary
from table2image_agent.agents.scout import OpenAIScoutAgent


@pytest.mark.integration
def test_scout_real_api_call():
    """测试 Scout Agent 真实 API 调用"""
    # 检查环境变量
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_api_key_here":
        pytest.skip("需要真实的 OPENAI_API_KEY 环境变量才能运行集成测试")

    # 测试图片路径
    test_image_path = "data/example_photo/2011-03-26_145620.png"

    # 检查测试图片是否存在
    if not Path(test_image_path).exists():
        pytest.skip(f"测试图片不存在: {test_image_path}")

    # 创建 Scout Agent
    scout = OpenAIScoutAgent()

    # 验证模型配置
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o")
    print(f"📋 使用模型: {scout.model_name}")

    # 执行扫描
    summary = scout.scan(test_image_path)

    # 验证返回结果
    assert isinstance(summary, VisualSummary), "返回结果应该是 VisualSummary 类型"
    assert summary.table_title, "表格标题不能为空"
    assert len(summary.headers) > 0, "表头列表不能为空"
    assert len(summary.row_structure) > 0, "行结构不能为空"
    assert len(summary.column_structure) > 0, "列结构不能为空"

    # 验证 headers 包含预期的列（基于财务报表的常见列）
    expected_headers = ["部门", "Q1", "Q2", "Q3", "Q4", "季度", "年"]
    found_headers = [h for h in expected_headers if any(h in header for header in summary.headers)]

    print(f"\n📊 扫描结果预览:")
    print(f"   表格标题: {summary.table_title}")
    print(f"   表头: {summary.headers}")
    print(f"   行结构: {summary.row_structure}")
    print(f"   列结构: {summary.column_structure}")
    print(f"   合并单元格: {summary.merge_cells}")
    print(f"   布局描述: {summary.layout_description}")
    print(f"   找到预期列: {found_headers}")


@pytest.mark.integration
def test_scout_json_output_format():
    """测试 Scout Agent JSON 输出格式正确性"""
    # 检查环境变量
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_api_key_here":
        pytest.skip("需要真实的 OPENAI_API_KEY 环境变量才能运行集成测试")

    test_image_path = "data/example_photo/2011-03-26_145620.png"

    if not Path(test_image_path).exists():
        pytest.skip(f"测试图片不存在: {test_image_path}")

    scout = OpenAIScoutAgent()
    summary = scout.scan(test_image_path)

    # 验证数据类型和格式
    assert isinstance(summary.table_title, str), "表格标题应该是字符串"
    assert isinstance(summary.headers, list), "表头应该是列表"
    assert isinstance(summary.row_structure, list), "行结构应该是列表"
    assert isinstance(summary.column_structure, list), "列结构应该是列表"
    assert isinstance(summary.merge_cells, list), "合并单元格应该是列表"
    assert isinstance(summary.layout_description, str), "布局描述应该是字符串"

    # 验证列表元素都是字符串
    assert all(isinstance(h, str) for h in summary.headers), "所有表头都应该是字符串"
    assert all(isinstance(r, str) for r in summary.row_structure), "所有行结构都应该是字符串"
    assert all(isinstance(c, str) for c in summary.column_structure), "所有列结构都应该是字符串"

    # 验证 to_dict 方法
    summary_dict = summary.to_dict()
    assert isinstance(summary_dict, dict), "to_dict 应该返回字典"
    assert "table_title" in summary_dict, "字典应包含 table_title"
    assert "headers" in summary_dict, "字典应包含 headers"
    assert "row_structure" in summary_dict, "字典应包含 row_structure"
    assert "column_structure" in summary_dict, "字典应包含 column_structure"
    assert "merge_cells" in summary_dict, "字典应包含 merge_cells"
    assert "layout_description" in summary_dict, "字典应包含 layout_description"


if __name__ == "__main__":
    # 手动运行测试的主函数
    print("🧪 开始 Scout Agent 集成测试...")

    try:
        test_scout_real_api_call()
        print("✅ API 调用测试通过")
    except Exception as e:
        print(f"❌ API 调用测试失败: {e}")

    try:
        test_scout_json_output_format()
        print("✅ JSON 格式测试通过")
    except Exception as e:
        print(f"❌ JSON 格式测试失败: {e}")

    print("\n🎉 集成测试完成！")