"""
测试 Auto-Fit 渲染器功能
验证固定字号、固定内边距、内容自适应尺寸等特性
"""

import pytest
import os
import json
from pathlib import Path
from typing import List, Dict, Any
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt

# 导入待测试的模块
from src.table2image_agent.utils.renderer import TableRenderer


class TestAutoFitRenderer:
    """测试 Auto-Fit 渲染器的核心功能"""

    def setup_method(self):
        """每个测试方法执行前的设置"""
        self.renderer = TableRenderer()
        self.test_output_dir = Path("data/test_autofit_output")
        self.test_output_dir.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """每个测试方法执行后的清理"""
        # 清理测试生成的文件
        import shutil
        if self.test_output_dir.exists():
            shutil.rmtree(self.test_output_dir)

    def test_autofit_basic_parameters_exist(self):
        """测试：Auto-Fit 基础参数存在性"""
        # 验证固定字号参数
        assert hasattr(self.renderer, 'AUTOFIT_FONT_SIZE'), "缺少 AUTOFIT_FONT_SIZE 参数"
        assert self.renderer.AUTOFIT_FONT_SIZE == 12, f"字号应为12pt，实际为{self.renderer.AUTOFIT_FONT_SIZE}"

        # 验证固定内边距参数
        assert hasattr(self.renderer, 'AUTOFIT_CELL_PADDING'), "缺少 AUTOFIT_CELL_PADDING 参数"
        assert self.renderer.AUTOFIT_CELL_PADDING == 0.05, f"内边距应为0.05inch，实际为{self.renderer.AUTOFIT_CELL_PADDING}"

        # 验证最大列宽限制参数
        assert hasattr(self.renderer, 'AUTOFIT_MAX_COLUMN_CHARS'), "缺少 AUTOFIT_MAX_COLUMN_CHARS 参数"
        assert self.renderer.AUTOFIT_MAX_COLUMN_CHARS == 50, f"最大列字符数应为50，实际为{self.renderer.AUTOFIT_MAX_COLUMN_CHARS}"

    def test_autofit_calculate_column_widths_bottom_up(self):
        """测试：Bottom-Up 列宽计算逻辑"""
        # 测试数据：不同长度的列
        test_data = [
            ["短", "中等长度", "这是一个非常长的列内容用于测试最大宽度限制"],
            ["A", "Medium", "This is a very long column content to test max width limit"],
            ["B", "测试", "另一行测试数据"]
        ]

        # 调用列宽计算方法
        col_widths = self.renderer._autofit_calculate_column_widths(test_data)

        # 验证返回值类型和数量
        assert isinstance(col_widths, list), "列宽应返回列表"
        assert len(col_widths) == 3, f"应有3列，实际为{len(col_widths)}列"

        # 验证列宽逻辑：第1列最短，第2列中等，第3列最长但受限
        assert col_widths[0] < col_widths[1], "第1列应比第2列窄"
        assert col_widths[1] < col_widths[2], "第2列应比第3列窄"

        # 验证最大宽度限制
        max_char_width = max(len(str(row[2])) for row in test_data)  # 第3列最大字符数
        expected_max_width = min(50, max_char_width)  # 应被限制在50字符
        assert col_widths[2] <= expected_max_width * 0.1, f"第3列宽度超过限制，实际为{col_widths[2]}"

    def test_autofit_calculate_canvas_size(self):
        """测试：画布尺寸的自适应计算"""
        # 小表格数据
        small_data = [["A", "B"], ["1", "2"]]
        small_width, small_height = self.renderer._autofit_calculate_canvas_size(small_data)

        # 大表格数据
        large_data = [
            ["Col" + str(i) for i in range(10)] for _ in range(20)
        ]
        large_data.append(["这是很长的内容用于测试自适应"] * 10)
        large_width, large_height = self.renderer._autofit_calculate_canvas_size(large_data)

        # 验证尺寸关系：大表格应该生成更大的画布
        assert large_width > small_width, f"大表格宽度应更大: 大={large_width}, 小={small_width}"
        assert large_height > small_height, f"大表格高度应更大: 大={large_height}, 小={small_height}"

        # 验证最小尺寸限制
        assert small_width >= 2.0, "小表格宽度不应小于2英寸"
        assert small_height >= 1.0, "小表格高度不应小于1英寸"

    def test_autofit_render_image_consistency(self):
        """测试：不同数据量的图片渲染一致性（字号和间距恒定）"""
        # 小表格
        small_data = [["Name", "Score"], ["Alice", "95"]]
        small_path = self.test_output_dir / "small_table.png"

        # 大表格
        large_data = [
            ["姓名", "部门", "职位", "邮箱地址", "电话号码", "入职日期", "薪资等级", "绩效评级"],
            ["张三", "技术部", "高级工程师", "zhangsan@company.com", "13800138001", "2020-01-15", "L7", "A"],
            ["李四", "产品部", "产品经理", "lisi@company.com", "13800138002", "2019-06-20", "L8", "A+"],
            ["王五", "设计部", "UI设计师", "wangwu@company.com", "13800138003", "2021-03-10", "L6", "B+"],
            ["赵六", "市场部", "市场专员", "zhaoliu@company.com", "13800138004", "2020-11-25", "L5", "A"],
            ["钱七", "技术部", "前端工程师", "qianqi@company.com", "13800138005", "2022-02-28", "L6", "B"],
            ["孙八", "财务部", "财务主管", "sunba@company.com", "13800138006", "2018-09-15", "L9", "A+"],
            ["周九", "人力资源部", "HR专员", "zhoujiu@company.com", "13800138007", "2021-07-08", "L5", "B+"],
            ["吴十", "技术部", "后端工程师", "wushi@company.com", "13800138008", "2020-05-12", "L7", "A"]
        ]
        large_path = self.test_output_dir / "large_table.png"

        # 渲染两个表格
        self.renderer.render_image_autofit(small_data, str(small_path))
        self.renderer.render_image_autofit(large_data, str(large_path))

        # 验证文件生成
        assert small_path.exists(), "小表格图片未生成"
        assert large_path.exists(), "大表格图片未生成"

        # 验证大表格图片尺寸显著大于小表格
        small_size = small_path.stat().st_size
        large_size = large_path.stat().st_size
        assert large_size > small_size * 2, f"大表格文件应显著大于小表格: 大={large_size}, 小={small_size}"

    def test_autofit_text_wrapping(self):
        """测试：长文本自动换行功能"""
        # 包含超长文本的测试数据
        test_data = [
            ["字段名", "描述"],
            ["姓名", "张三"],
            ["备注", "这是一个非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常长的备注文本，应该被自动换行显示"]
        ]

        output_path = self.test_output_dir / "wrap_test.png"
        self.renderer.render_image_autofit(test_data, str(output_path))

        # 验证图片生成
        assert output_path.exists(), "换行测试图片未生成"

        # 验证图片尺寸合理（应该因换行而更高）
        img_size = output_path.stat().st_size
        assert img_size > 1000, f"图片文件过小，可能未正确换行: {img_size} bytes"

    def test_autofit_layout_generation_compatibility(self):
        """测试：Auto-Fit 模式与 FIX-001 布局生成的兼容性"""
        test_data = [
            ["项目名称", "负责人", "开始日期", "结束日期", "状态"],
            ["项目A", "张三", "2024-01-01", "2024-03-31", "已完成"],
            ["项目B", "李四", "2024-02-15", "2024-05-30", "进行中"],
            ["这是一个非常长的项目名称用于测试换行", "王五", "2024-03-01", "2024-08-31", "规划中"]
        ]

        # 渲染图片并生成布局
        output_path = self.test_output_dir / "layout_test.png"
        layout_path = self.test_output_dir / "layout_test_layout.json"

        self.renderer.render_image_autofit(test_data, str(output_path))

        # 生成布局信息
        layout = self.renderer._generate_table_layout(test_data)

        # 验证布局结构
        assert isinstance(layout, dict), "布局应为字典类型"
        assert "rows" in layout, "布局应包含行信息"
        assert "columns" in layout, "布局应包含列信息"
        assert "image_size" in layout, "布局应包含图片尺寸"

        # 验证行数和列数
        assert len(layout["rows"]) == 4, f"应有4行，实际为{len(layout['rows'])}行"
        assert len(layout["columns"]) == 5, f"应有5列，实际为{len(layout['columns'])}列"

        # 验证坐标递增性（Y坐标应从上到下递增）
        row_y_positions = [row["y"] for row in layout["rows"]]
        for i in range(1, len(row_y_positions)):
            assert row_y_positions[i] > row_y_positions[i-1], f"行坐标应递增: 行{i-1}={row_y_positions[i-1]}, 行{i}={row_y_positions[i]}"

        # 保存布局文件用于验证
        with open(layout_path, 'w', encoding='utf-8') as f:
            json.dump(layout, f, ensure_ascii=False, indent=2)

    def test_autofit_font_size_consistency(self):
        """测试：字号恒定性验证"""
        # 不同大小的表格数据
        small_data = [["A", "B"], ["1", "2"]]
        medium_data = [["Name", "Age", "City"], ["Alice", "25", "Beijing"], ["Bob", "30", "Shanghai"]]
        large_data = [["Col" + str(i) for i in range(10)] for _ in range(15)]

        # 获取各自渲染时的字体大小
        small_font = self.renderer._get_autofit_font_size(small_data)
        medium_font = self.renderer._get_autofit_font_size(medium_data)
        large_font = self.renderer._get_autofit_font_size(large_data)

        # 验证字号恒定为12pt
        assert small_font == 12, f"小表格字号应为12pt，实际为{small_font}"
        assert medium_font == 12, f"中等表格字号应为12pt，实际为{medium_font}"
        assert large_font == 12, f"大表格字号应为12pt，实际为{large_font}"

    def test_autofit_edge_cases(self):
        """测试：边界情况处理"""
        # 空数据
        with pytest.raises(ValueError, match="表格数据不能为空"):
            self.renderer.render_image_autofit([], "test.png")

        # 单行单列
        single_cell = [["测试"]]
        output1 = self.test_output_dir / "single_cell.png"
        self.renderer.render_image_autofit(single_cell, str(output1))
        assert output1.exists(), "单单元格图片未生成"

        # 单行多列
        single_row = [["A", "B", "C", "D", "E"]]
        output2 = self.test_output_dir / "single_row.png"
        self.renderer.render_image_autofit(single_row, str(output2))
        assert output2.exists(), "单行多列图片未生成"

        # 多行单列
        single_col = [["Row1"], ["Row2"], ["Row3"]]
        output3 = self.test_output_dir / "single_col.png"
        self.renderer.render_image_autofit(single_col, str(output3))
        assert output3.exists(), "多行单列图片未生成"