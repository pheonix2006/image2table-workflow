"""数据渲染器测试。

测试表格渲染功能，包括 CSV 解析、图片生成和 Markdown 转换。
"""

import json
import os
import tempfile
from pathlib import Path
import pytest

# 需要先测试渲染器是否存在，如果不存在先跳过
try:
    from src.table2image_agent.utils.renderer import TableRenderer
    RENDERER_AVAILABLE = True
except ImportError:
    RENDERER_AVAILABLE = False


@pytest.mark.skipif(not RENDERER_AVAILABLE, reason="渲染器尚未实现")
def test_render_table_image():
    """测试表格图片渲染功能"""
    # 创建渲染器
    renderer = TableRenderer()

    # 测试数据：简单表格
    test_data = [
        ["Header1", "Header2"],
        ["Val1", "Val2"],
        ["Val3", "Val4"]
    ]

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
        output_path = temp_file.name

        # 渲染图片
        renderer.render_image(test_data, output_path)

        # 验证文件生成
        assert Path(output_path).exists(), "图片文件应该已生成"

        # 验证文件大小（非空）
        assert Path(output_path).stat().st_size > 0, "图片文件应该有内容"

        # 验证文件格式（PNG）
        assert output_path.endswith('.png'), "应该是 PNG 格式"

        print(f"✅ 图片渲染成功: {output_path}")
        print(f"   文件大小: {Path(output_path).stat().st_size} 字节")


@pytest.mark.skipif(not RENDERER_AVAILABLE, reason="渲染器尚未实现")
def test_csv_parsing():
    """测试 CSV 数据解析功能"""
    # 测试 CSV 中的字符串数据
    test_csv_data = "[['Hand', '1 credit'], ['Royal flush', '250']]"
    expected_data = [
        ["Hand", "1 credit"],
        ["Royal flush", "250"]
    ]

    # 模拟解析逻辑（后续在渲染器中实现）
    import ast
    parsed_data = ast.literal_eval(test_csv_data)

    # 验证解析结果
    assert parsed_data == expected_data, f"解析结果应该为 {expected_data}"
    assert isinstance(parsed_data, list), "解析结果应该是列表"
    assert len(parsed_data) == 2, "应该有 2 行数据"

    print(f"✅ CSV 解析成功: {parsed_data}")


@pytest.mark.skipif(not RENDERER_AVAILABLE, reason="渲染器尚未实现")
def test_markdown_conversion():
    """测试 Markdown 表格转换功能"""
    # 创建渲染器
    renderer = TableRenderer()

    # 测试数据
    test_data = [
        ["Name", "Score", "Rank"],
        ["Alice", "95", "1"],
        ["Bob", "87", "2"],
        ["Charlie", "92", "3"]
    ]

    # 转换为 Markdown
    markdown_content = renderer.to_markdown(test_data)

    # 验证 Markdown 格式
    assert isinstance(markdown_content, str), "输出应该是字符串"
    assert "Name" in markdown_content, "应该包含表头"
    assert "Alice" in markdown_content, "应该包含数据行"
    assert "|" in markdown_content, "应该包含表格分隔符"

    # 验证 Markdown 结构
    lines = markdown_content.strip().split('\n')
    assert len(lines) >= 4, "应该至少有 4 行（表头 + 3行数据）"

    print(f"✅ Markdown 转换成功:")
    print(f"   内容预览:\n{markdown_content}")


@pytest.mark.skipif(not RENDERER_AVAILABLE, reason="渲染器尚未实现")
def test_full_rendering_workflow():
    """测试完整的渲染工作流"""
    renderer = TableRenderer()

    # 模拟完整的 CSV 行数据
    csv_row = "[['Hand', '1 credit'], ['Royal flush', '250']]"
    question = "what is payout?"
    answer = "250"

    # 解析表格数据
    import ast
    table_data = ast.literal_eval(csv_row)

    with tempfile.TemporaryDirectory() as temp_dir:
        # 生成图片
        image_path = os.path.join(temp_dir, "test_table.png")
        renderer.render_image(table_data, image_path)

        # 生成 Markdown
        markdown_content = renderer.to_markdown(table_data)

        # 生成元数据
        metadata = {
            "question": question,
            "answer": answer,
            "markdown_content": markdown_content
        }

        metadata_path = os.path.join(temp_dir, "test_metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        # 验证文件生成
        assert Path(image_path).exists(), "图片应该生成"
        assert Path(metadata_path).exists(), "元数据应该生成"
        assert Path(image_path).stat().st_size > 0, "图片应该有内容"

        # 验证元数据内容
        with open(metadata_path, 'r', encoding='utf-8') as f:
            loaded_metadata = json.load(f)
            assert loaded_metadata["question"] == question, "问题应该保存"
            assert loaded_metadata["answer"] == answer, "答案应该保存"
            assert "markdown_content" in loaded_metadata, "Markdown 应该保存"

        print(f"✅ 完整工作流测试通过")
        print(f"   图片: {image_path}")
        print(f"   元数据: {metadata_path}")


if __name__ == "__main__":
    # 手动运行测试的主函数
    print("🧪 开始数据渲染器测试...")

    try:
        if RENDERER_AVAILABLE:
            test_render_table_image()
            print("✅ 图片渲染测试通过")
        else:
            print("⏭️ 跳过图片渲染测试（渲染器未实现）")
    except Exception as e:
        print(f"❌ 图片渲染测试失败: {e}")

    try:
        test_csv_parsing()
        print("✅ CSV 解析测试通过")
    except Exception as e:
        print(f"❌ CSV 解析测试失败: {e}")

    try:
        if RENDERER_AVAILABLE:
            test_markdown_conversion()
            print("✅ Markdown 转换测试通过")
        else:
            print("⏭️ 跳过 Markdown 转换测试（渲染器未实现）")
    except Exception as e:
        print(f"❌ Markdown 转换测试失败: {e}")

    try:
        if RENDERER_AVAILABLE:
            test_full_rendering_workflow()
            print("✅ 完整工作流测试通过")
        else:
            print("⏭️ 跳过完整工作流测试（渲染器未实现）")
    except Exception as e:
        print(f"❌ 完整工作流测试失败: {e}")

    print("\n🎉 渲染器测试完成！")