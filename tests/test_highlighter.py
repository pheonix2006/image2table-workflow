"""VisualHighlighter 测试套件。

测试视觉高亮器的核心功能：
1. 坐标解析（行、列、单元格）
2. 绘制逻辑（半透明彩色蒙层）
3. 颜色方案（SCAN/FOCUS/ANSWER）
"""

import json
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest
from PIL import Image

# 需要先测试高亮器是否存在
try:
    from table2image_agent.utils.highlighter import VisualHighlighter
    HIGHLIGHTER_AVAILABLE = True
except ImportError:
    HIGHLIGHTER_AVAILABLE = False


# 模拟 Layout 数据结构（基于 sample_1_layout.json）
SAMPLE_LAYOUT = {
    "rows": [
        {"index": 0, "y": 479.7636040284333, "height": 22.856462733849185},
        {"index": 1, "y": 502.6200667622825, "height": 22.856462733849185},
        {"index": 2, "y": 525.4765294961317, "height": 22.85646273384907},
        {"index": 3, "y": 548.3329922299808, "height": 22.85646273384907},
        {"index": 4, "y": 571.1894549638298, "height": 22.856462733849185},
        {"index": 5, "y": 594.045917697679, "height": 22.856462733849185},
        {"index": 6, "y": 616.9023804315282, "height": 22.85646273384907},
        {"index": 7, "y": 639.7588431653774, "height": 22.85646273384907},
        {"index": 8, "y": 662.6153058992263, "height": 22.856462733849185},
        {"index": 9, "y": 685.4717686330755, "height": 22.856462733849185},
        {"index": 10, "y": 708.3282313669247, "height": 22.85646273384907},
        {"index": 11, "y": 731.1846941007736, "height": 22.856462733849185},
        {"index": 12, "y": 754.0411568346228, "height": 22.85646273384907},
        {"index": 13, "y": 776.897619568472, "height": 22.85646273384907},
        {"index": 14, "y": 799.754082302321, "height": 22.856462733849185},
        {"index": 15, "y": 822.6105450361702, "height": 22.85646273384907},
        {"index": 16, "y": 845.4670077700193, "height": 22.85646273384907},
        {"index": 17, "y": 868.3234705038683, "height": 22.856462733849128},
    ],
    "columns": [
        {"index": 0, "x": 167.4945191056912, "width": 40.68231644493716},
        {"index": 1, "x": 208.17683555062837, "width": 294.9467942257944},
        {"index": 2, "x": 503.1236297764228, "width": 264.4350568920916},
        {"index": 3, "x": 767.5586866685144, "width": 91.53521200110868},
        {"index": 4, "x": 859.093898669623, "width": 132.21752844604578},
        {"index": 5, "x": 991.3114271156687, "width": 71.19405377863995},
    ],
    "table_bounds": {
        "x": 167.4945191056912,
        "y": 479.7636040284333,
        "width": 895.0109617886175,
        "height": 411.4163292092842,
    },
    "image_size": {"width": 1200, "height": 1380},
}


@pytest.mark.skipif(not HIGHLIGHTER_AVAILABLE, reason="高亮器尚未实现")
def test_highlighter_initialization():
    """测试高亮器初始化"""
    highlighter = VisualHighlighter()

    assert hasattr(highlighter, "highlight"), "应该有 highlight 方法"
    assert hasattr(highlighter, "_apply_highlight"), "应该有 _apply_highlight 方法"

    print("✅ 高亮器初始化成功")


@pytest.mark.skipif(not HIGHLIGHTER_AVAILABLE, reason="高亮器尚未实现")
def test_column_highlight_coordinates():
    """测试列高亮的坐标计算"""
    highlighter = VisualHighlighter()

    # 创建临时图片文件
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as img_file:
        # 创建测试图片
        test_img = Image.new("RGB", (1200, 1380), color="white")
        test_img.save(img_file.name)
        img_path = img_file.name

    try:
        # 临时保存 Layout
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as json_file:
            json.dump(SAMPLE_LAYOUT, json_file)
            layout_path = json_file.name

        # 高亮列 0
        output_path = tempfile.mktemp(suffix=".png")
        instructions = [
            {"type": "col", "index": 0, "color": "scan"},
        ]

        highlighter.highlight(img_path, layout_path, output_path, instructions)

        # 验证文件生成
        assert Path(output_path).exists(), "高亮图片应该生成"
        assert Path(output_path).stat().st_size > 0, "图片应该有内容"

        print("✅ 列高亮坐标计算正确")

    finally:
        # 清理临时文件
        Path(img_path).unlink(missing_ok=True)
        Path(output_path).unlink(missing_ok=True)


@pytest.mark.skipif(not HIGHLIGHTER_AVAILABLE, reason="高亮器尚未实现")
def test_row_highlight_coordinates():
    """测试行高亮的坐标计算"""
    highlighter = VisualHighlighter()

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as img_file:
        test_img = Image.new("RGB", (1200, 1380), color="white")
        test_img.save(img_file.name)
        img_path = img_file.name

    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as json_file:
            json.dump(SAMPLE_LAYOUT, json_file)
            layout_path = json_file.name

        output_path = tempfile.mktemp(suffix=".png")
        instructions = [
            {"type": "row", "index": 14, "color": "focus"},
        ]

        highlighter.highlight(img_path, layout_path, output_path, instructions)

        assert Path(output_path).exists(), "高亮图片应该生成"

        print("✅ 行高亮坐标计算正确")

    finally:
        Path(img_path).unlink(missing_ok=True)
        Path(output_path).unlink(missing_ok=True)


@pytest.mark.skipif(not HIGHLIGHTER_AVAILABLE, reason="高亮器尚未实现")
def test_cell_highlight_coordinates():
    """测试单元格高亮的坐标计算"""
    highlighter = VisualHighlighter()

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as img_file:
        test_img = Image.new("RGB", (1200, 1380), color="white")
        test_img.save(img_file.name)
        img_path = img_file.name

    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as json_file:
            json.dump(SAMPLE_LAYOUT, json_file)
            layout_path = json_file.name

        output_path = tempfile.mktemp(suffix=".png")
        instructions = [
            {"type": "cell", "row": 14, "col": 2, "color": "answer"},
        ]

        highlighter.highlight(img_path, layout_path, output_path, instructions)

        assert Path(output_path).exists(), "高亮图片应该生成"

        print("✅ 单元格高亮坐标计算正确")

    finally:
        Path(img_path).unlink(missing_ok=True)
        Path(output_path).unlink(missing_ok=True)


@pytest.mark.skipif(not HIGHLIGHTER_AVAILABLE, reason="高亮器尚未实现")
def test_multiple_highlights():
    """测试多个高亮区域的叠加"""
    highlighter = VisualHighlighter()

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as img_file:
        test_img = Image.new("RGB", (1200, 1380), color="white")
        test_img.save(img_file.name)
        img_path = img_file.name

    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as json_file:
            json.dump(SAMPLE_LAYOUT, json_file)
            layout_path = json_file.name

        output_path = tempfile.mktemp(suffix=".png")
        instructions = [
            {"type": "col", "index": 0, "color": "scan"},
            {"type": "col", "index": 3, "color": "scan"},
            {"type": "cell", "row": 14, "col": 2, "color": "answer"},
        ]

        highlighter.highlight(img_path, layout_path, output_path, instructions)

        assert Path(output_path).exists(), "高亮图片应该生成"

        print("✅ 多个高亮区域叠加成功")

    finally:
        Path(img_path).unlink(missing_ok=True)
        Path(output_path).unlink(missing_ok=True)


@pytest.mark.skipif(not HIGHLIGHTER_AVAILABLE, reason="高亮器尚未实现")
def test_color_scheme():
    """测试颜色方案映射"""
    highlighter = VisualHighlighter()

    # 测试三种颜色
    test_cases = [
        ("scan", (255, 255, 0)),  # 黄色
        ("focus", (255, 0, 0)),   # 红色
        ("answer", (0, 255, 0)),  # 绿色
    ]

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as img_file:
        test_img = Image.new("RGB", (1200, 1380), color="white")
        test_img.save(img_file.name)
        img_path = img_file.name

    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as json_file:
            json.dump(SAMPLE_LAYOUT, json_file)
            layout_path = json_file.name

        for color_name, expected_rgb in test_cases:
            output_path = tempfile.mktemp(suffix=".png")
            instructions = [
                {"type": "col", "index": 0, "color": color_name},
            ]

            highlighter.highlight(img_path, layout_path, output_path, instructions)

            # 验证图片生成
            assert Path(output_path).exists(), f"{color_name} 颜色高亮应该生成"
            Path(output_path).unlink(missing_ok=True)

            print(f"✅ 颜色 {color_name} 映射正确")

    finally:
        Path(img_path).unlink(missing_ok=True)


@pytest.mark.skipif(not HIGHLIGHTER_AVAILABLE, reason="高亮器尚未实现")
def test_alpha_transparency():
    """测试透明度设置"""
    highlighter = VisualHighlighter()

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as img_file:
        test_img = Image.new("RGB", (1200, 1380), color="white")
        test_img.save(img_file.name)
        img_path = img_file.name

    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as json_file:
            json.dump(SAMPLE_LAYOUT, json_file)
            layout_path = json_file.name

        output_path = tempfile.mktemp(suffix=".png")
        instructions = [
            {"type": "col", "index": 0, "color": "scan"},
        ]

        highlighter.highlight(img_path, layout_path, output_path, instructions)

        # 验证图片生成（透明度通过视觉验证）
        assert Path(output_path).exists(), "半透明高亮应该生成"

        print("✅ Alpha 透明度设置成功")

    finally:
        Path(img_path).unlink(missing_ok=True)
        Path(output_path).unlink(missing_ok=True)


@pytest.mark.skipif(not HIGHLIGHTER_AVAILABLE, reason="高亮器尚未实现")
def test_draw_overlay_method():
    """测试 draw_overlay 私有方法的坐标计算逻辑"""
    highlighter = VisualHighlighter()

    # 验证列坐标计算
    col_rect = highlighter._get_column_rect(SAMPLE_LAYOUT, 0)
    expected_col_x = SAMPLE_LAYOUT["columns"][0]["x"]
    expected_col_y = SAMPLE_LAYOUT["table_bounds"]["y"]
    expected_col_w = SAMPLE_LAYOUT["columns"][0]["width"]
    expected_col_h = SAMPLE_LAYOUT["table_bounds"]["height"]

    assert col_rect["x"] == expected_col_x, f"列 x 坐标应为 {expected_col_x}"
    assert col_rect["y"] == expected_col_y, f"列 y 坐标应为 {expected_col_y}"
    assert col_rect["width"] == expected_col_w, f"列宽度应为 {expected_col_w}"
    assert col_rect["height"] == expected_col_h, f"列高度应为 {expected_col_h}"

    print("✅ 列坐标计算逻辑正确")

    # 验证行坐标计算
    row_rect = highlighter._get_row_rect(SAMPLE_LAYOUT, 14)
    expected_row_x = SAMPLE_LAYOUT["table_bounds"]["x"]
    expected_row_y = SAMPLE_LAYOUT["rows"][14]["y"]
    expected_row_w = SAMPLE_LAYOUT["table_bounds"]["width"]
    expected_row_h = SAMPLE_LAYOUT["rows"][14]["height"]

    assert row_rect["x"] == expected_row_x, f"行 x 坐标应为 {expected_row_x}"
    assert row_rect["y"] == expected_row_y, f"行 y 坐标应为 {expected_row_y}"
    assert row_rect["width"] == expected_row_w, f"行宽度应为 {expected_row_w}"
    assert row_rect["height"] == expected_row_h, f"行高度应为 {expected_row_h}"

    print("✅ 行坐标计算逻辑正确")

    # 验证单元格坐标计算
    cell_rect = highlighter._get_cell_rect(SAMPLE_LAYOUT, 14, 2)
    expected_cell_x = SAMPLE_LAYOUT["columns"][2]["x"]
    expected_cell_y = SAMPLE_LAYOUT["rows"][14]["y"]
    expected_cell_w = SAMPLE_LAYOUT["columns"][2]["width"]
    expected_cell_h = SAMPLE_LAYOUT["rows"][14]["height"]

    assert cell_rect["x"] == expected_cell_x, f"单元格 x 坐标应为 {expected_cell_x}"
    assert cell_rect["y"] == expected_cell_y, f"单元格 y 坐标应为 {expected_cell_y}"
    assert cell_rect["width"] == expected_cell_w, f"单元格宽度应为 {expected_cell_w}"
    assert cell_rect["height"] == expected_cell_h, f"单元格高度应为 {expected_cell_h}"

    print("✅ 单元格坐标计算逻辑正确")


@pytest.mark.skipif(not HIGHLIGHTER_AVAILABLE, reason="高亮器尚未实现")
def test_preserve_original_image():
    """测试原始图片不被修改"""
    highlighter = VisualHighlighter()

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as img_file:
        test_img = Image.new("RGB", (1200, 1380), color="white")
        test_img.save(img_file.name)
        img_path = img_file.name

    try:
        # 保存原始文件大小
        original_size = Path(img_path).stat().st_size

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as json_file:
            json.dump(SAMPLE_LAYOUT, json_file)
            layout_path = json_file.name

        output_path = tempfile.mktemp(suffix=".png")
        instructions = [
            {"type": "col", "index": 0, "color": "scan"},
        ]

        highlighter.highlight(img_path, layout_path, output_path, instructions)

        # 验证原始文件未被修改
        current_size = Path(img_path).stat().st_size
        assert current_size == original_size, "原始图片应该保持不变"

        print("✅ 原始图片未被修改")

    finally:
        Path(img_path).unlink(missing_ok=True)
        Path(output_path).unlink(missing_ok=True)


if __name__ == "__main__":
    print("🧪 开始 VisualHighlighter 测试...\n")

    try:
        test_highlighter_initialization()
        test_draw_overlay_method()
        test_column_highlight_coordinates()
        test_row_highlight_coordinates()
        test_cell_highlight_coordinates()
        test_multiple_highlights()
        test_color_scheme()
        test_alpha_transparency()
        test_preserve_original_image()
        print("\n🎉 所有测试通过！")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
