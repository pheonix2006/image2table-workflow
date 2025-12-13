"""表格渲染器：将文本表格数据转换为图片和 Markdown 格式。"""

import json
import os
from pathlib import Path
from typing import List
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import numpy as np


class TableRenderer:
    """表格渲染器：负责将表格数据可视化"""

    def __init__(self):
        """初始化渲染器"""
        # 设置 matplotlib 使用非交互式后端
        matplotlib.use('Agg')

        # 设置字体支持（使用系统默认字体）
        plt.rcParams['font.family'] = 'sans-serif'

        # 设置基础参数
        self.dpi = 150  # 分辨率

        # 动态图片尺寸参数（将根据数据量调整）
        self.min_width = 8   # 最小宽度（英寸）
        self.min_height = 6   # 最小高度（英寸）
        self.max_width = 20  # 最大宽度（英寸）
        self.max_height = 16  # 最大高度（英寸）
        self.cell_padding = 0.1  # 单元格内边距（英寸）

    def render_image(self, data: List[List[str]], output_path: str) -> None:
        """
        将表格数据渲染为图片（动态调整尺寸）

        Args:
            data: 二维列表形式的表格数据
            output_path: 输出图片路径
        """
        if not data:
            raise ValueError("表格数据不能为空")

        # 确保输出目录存在
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        # 创建 DataFrame
        df = pd.DataFrame(data)

        # 动态计算合适的图片尺寸
        optimal_size = self._calculate_optimal_size(data)

        # 创建图表
        fig, ax = plt.subplots(figsize=optimal_size, dpi=self.dpi)
        ax.axis('off')  # 隐藏坐标轴

        # 动态计算列宽
        num_columns = len(df.columns)
        num_rows = len(data)

        # 根据内容长度调整列宽
        col_widths = self._calculate_column_widths(data, optimal_size[0])

        # 创建表格
        table = ax.table(
            cellText=df.values,
            colLabels=df.columns,
            cellLoc='center',
            loc='center',
            colWidths=col_widths
        )

        # 设置表格样式
        table.auto_set_font_size(True)

        # 动态调整字体大小
        font_size = self._calculate_font_size(data, optimal_size)
        table.set_fontsize(font_size)

        # 动态调整表格缩放
        scale_factor = self._calculate_scale_factor(data, optimal_size)
        table.scale(scale_factor[0], scale_factor[1])

        # 设置标题
        title = "Generated Table Data"
        title_font_size = max(font_size + 2, 12)  # 标题字体稍大
        ax.set_title(title, fontsize=title_font_size, pad=20, fontweight='bold')

        # 调整布局
        plt.tight_layout()

        # 保存图片
        plt.savefig(
            output_path,
            format='png',
            bbox_inches='tight',
            facecolor='white',
            edgecolor='none'
        )
        plt.close()

        print(f"🖼️ 表格图片已生成: {output_path}")
        print(f"   📐 动态尺寸: {optimal_size[0]:.1f} x {optimal_size[1]:.1f} 英寸")
        print(f"   📏 列数: {num_columns}, 行数: {num_rows}")
        print(f"   🔤 字体大小: {font_size}pt")

    def _calculate_optimal_size(self, data: List[List[str]]) -> tuple[float, float]:
        """
        根据数据量动态计算最佳图片尺寸

        Args:
            data: 表格数据

        Returns:
            tuple: (宽度, 高度) 英寸
        """
        if not data:
            return (self.min_width, self.min_height)

        num_rows = len(data)
        num_cols = len(data[0]) if data[0] else 1

        # 计算所需的最小宽度（基于列数和内容长度）
        avg_content_length = sum(len(str(cell)) for row in data for cell in row) / (num_rows * num_cols)
        min_width_needed = max(
            self.min_width,
            min(self.max_width, num_cols * (0.8 + avg_content_length * 0.05))
        )

        # 计算所需的最小高度（基于行数）
        min_height_needed = max(
            self.min_height,
            min(self.max_height, num_rows * 0.4 + 2)
        )

        return (min_width_needed, min_height_needed)

    def _calculate_column_widths(self, data: List[List[str]], total_width: float) -> List[float]:
        """
        根据内容动态计算列宽

        Args:
            data: 表格数据
            total_width: 总宽度（英寸）

        Returns:
            List[float]: 每列的宽度比例
        """
        if not data or not data[0]:
            return [1.0]

        num_cols = len(data[0])

        # 计算每列的最大内容长度
        col_max_lengths = []
        for col_idx in range(num_cols):
            max_length = max(len(str(row[col_idx])) if col_idx < len(row) else 0 for row in data)
            col_max_lengths.append(max_length)

        # 将长度转换为宽度比例
        total_length = sum(col_max_lengths)
        if total_length == 0:
            return [1.0 / num_cols] * num_cols

        col_widths = [length / total_length for length in col_max_lengths]

        # 确保总和为 1.0
        total_width_ratio = sum(col_widths)
        if total_width_ratio > 0:
            col_widths = [w / total_width_ratio for w in col_widths]

        return col_widths

    def _calculate_font_size(self, data: List[List[str]], size: tuple[float, float]) -> int:
        """
        根据图片尺寸和数据量动态计算字体大小

        Args:
            data: 表格数据
            size: 图片尺寸 (宽度, 高度)

        Returns:
            int: 字体大小（磅）
        """
        if not data:
            return 10

        num_rows = len(data)
        num_cols = len(data[0]) if data[0] else 1

        # 基于图片面积和数据密度计算字体大小
        area = size[0] * size[1]
        data_density = (num_rows * num_cols) / area

        # 动态调整：数据越多，字体相对越大；数据越少，字体相对适中
        if data_density > 2:  # 高密度
            base_font = max(8, min(14, int(12 / (data_density ** 0.3))))
        elif data_density > 0.5:  # 中等密度
            base_font = max(10, min(16, int(14 / (data_density ** 0.2))))
        else:  # 低密度
            base_font = max(11, min(18, int(16 / (data_density ** 0.1))))

        # 根据内容长度微调
        avg_content_length = sum(len(str(cell)) for row in data for cell in row) / (num_rows * num_cols)
        if avg_content_length > 15:  # 内容较长时适当减小字体
            base_font = max(7, base_font - 2)

        return base_font

    def _calculate_scale_factor(self, data: List[List[str]], size: tuple[float, float]) -> tuple[float, float]:
        """
        计算表格缩放因子以确保内容适配

        Args:
            data: 表格数据
            size: 图片尺寸

        Returns:
            tuple: (x缩放, y缩放)
        """
        if not data:
            return (1.0, 1.0)

        num_rows = len(data)
        num_cols = len(data[0]) if data[0] else 1

        # 基于数据密度调整缩放
        area = size[0] * size[1]
        data_density = (num_rows * num_cols) / area

        # 动态缩放：高密度时适度压缩，低密度时适当拉伸
        if data_density > 1.5:  # 高密度：需要适度压缩
            scale_x = max(0.8, min(1.0, 1.0 / (data_density ** 0.15)))
            scale_y = max(0.7, min(0.9, 0.9 / (data_density ** 0.2)))
        elif data_density > 0.3:  # 中等密度：保持接近原比例
            scale_x = max(0.9, min(1.1, 1.0 / (data_density ** 0.1)))
            scale_y = max(0.9, min(1.1, 0.95 / (data_density ** 0.1)))
        else:  # 低密度：可以适当拉伸
            scale_x = min(1.3, 1.0 + (0.3 - data_density) * 0.3)
            scale_y = min(1.2, 1.0 + (0.3 - data_density) * 0.2)

        return (scale_x, scale_y)

    def to_markdown(self, data: List[List[str]]) -> str:
        """
        将表格数据转换为 Markdown 格式

        Args:
            data: 二维列表形式的表格数据

        Returns:
            str: Markdown 格式的表格字符串
        """
        if not data:
            raise ValueError("表格数据不能为空")

        markdown_lines = []

        # 处理每一行
        for i, row in enumerate(data):
            # 转换每个单元格为字符串，处理特殊字符
            markdown_row = [str(cell) for cell in row]

            # 构建 Markdown 行
            if i == 0:
                # 表头行
                header_row = " | ".join([f"**{cell}**" for cell in markdown_row])
                separator_row = "| " + " | ".join(["---"] * len(markdown_row)) + " |"
                markdown_lines.append(header_row)
                markdown_lines.append(separator_row)
            else:
                # 数据行
                data_row = " | ".join(markdown_row)
                markdown_lines.append(data_row)

        return "\n".join(markdown_lines)

    def parse_csv_table_array(self, csv_string: str) -> List[List[str]]:
        """
        解析 CSV 中的 table_array 字段

        Args:
            csv_string: CSV 中的表格数组字符串，如 "[['Header1', 'Header2'], ['Val1', 'Val2']]"

        Returns:
            List[List[str]]: 解析后的二维列表
        """
        import ast
        import pandas as pd
        import numpy as np

        try:
            # 预处理字符串，将 'nan' 替换为 '""'
            cleaned_string = csv_string.replace('nan', '""')

            # 先尝试直接解析
            parsed_data = ast.literal_eval(cleaned_string)

            # 验证数据格式
            result = []
            for row in parsed_data:
                if isinstance(row, list):
                    # 处理特殊值，如 NaN
                    processed_row = []
                    for cell in row:
                        if pd.isna(cell) or (isinstance(cell, float) and np.isnan(cell)):
                            processed_row.append("")
                        else:
                            processed_row.append(str(cell))
                    result.append(processed_row)
                else:
                    raise ValueError("每行应该是列表格式")

            return result

        except (ValueError, SyntaxError) as e:
            raise ValueError(f"无法解析表格数组: {e}") from e

    def render_wiki_table(self, table_array_str: str, question: str, answer: str,
                      output_dir: str, sample_id: int) -> dict:
        """
        渲染 Wiki 表格数据并保存元数据

        Args:
            table_array_str: 表格数组字符串
            question: 问题
            answer: 答案
            output_dir: 输出目录
            sample_id: 样本ID

        Returns:
            dict: 包含文件路径的信息
        """
        # 解析表格数据
        table_data = self.parse_csv_table_array(table_array_str)

        # 生成文件路径
        image_path = os.path.join(output_dir, f"sample_{sample_id}.png")
        metadata_path = os.path.join(output_dir, f"sample_{sample_id}.json")

        # 确保输出目录存在
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # 渲染图片
        self.render_image(table_data, image_path)

        # 生成 Markdown 内容
        markdown_content = self.to_markdown(table_data)

        # 保存元数据
        metadata = {
            "id": sample_id,
            "table_array": table_array_str,
            "question": question,
            "answer": answer,
            "markdown_content": markdown_content,
            "image_path": image_path,
            "num_rows": len(table_data),
            "num_columns": len(table_data[0]) if table_data else 0
        }

        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        print(f"📋 元数据已保存: {metadata_path}")

        return metadata

    def get_table_stats(self, data: List[List[str]]) -> dict:
        """
        获取表格统计信息

        Args:
            data: 表格数据

        Returns:
            dict: 统计信息
        """
        if not data:
            return {"rows": 0, "columns": 0}

        return {
            "rows": len(data),
            "columns": len(data[0]) if data[0] else 0,
            "total_cells": sum(len(row) for row in data)
        }

    def _generate_table_layout(self, data: List[List[str]]) -> dict:
        """
        基于真实Bbox测量生成表格布局信息

        Args:
            data: 表格数据

        Returns:
            dict: 包含行、列、图片尺寸和表格边界的布局信息
        """
        if not data:
            raise ValueError("表格数据不能为空")

        # 创建 DataFrame
        df = pd.DataFrame(data)

        # 动态计算合适的图片尺寸
        optimal_size = self._calculate_optimal_size(data)

        # 创建图表
        fig, ax = plt.subplots(figsize=optimal_size, dpi=self.dpi)
        ax.axis('off')  # 隐藏坐标轴

        # 动态计算列宽
        num_columns = len(df.columns)
        num_rows = len(data)

        # 根据内容长度调整列宽
        col_widths = self._calculate_column_widths(data, optimal_size[0])

        # 创建表格
        table = ax.table(
            cellText=df.values,
            colLabels=df.columns,
            cellLoc='center',
            loc='center',
            colWidths=col_widths
        )

        # 设置表格样式
        table.auto_set_font_size(True)

        # 动态调整字体大小
        font_size = self._calculate_font_size(data, optimal_size)
        table.set_fontsize(font_size)

        # 动态调整表格缩放
        scale_factor = self._calculate_scale_factor(data, optimal_size)
        table.scale(scale_factor[0], scale_factor[1])

        # 设置标题
        title = "Generated Table Data"
        title_font_size = max(font_size + 2, 12)  # 标题字体稍大
        ax.set_title(title, fontsize=title_font_size, pad=20, fontweight='bold')

        # 【关键步骤】强制渲染触发：在获取坐标前，必须调用 fig.canvas.draw()
        # 迫使 Matplotlib 完成由于 Text Wrap 导致的布局重排
        fig.canvas.draw()

        # 获取图片总尺寸
        fig_width_inch, fig_height_inch = fig.get_size_inches()
        image_width = int(fig_width_inch * self.dpi)
        image_height = int(fig_height_inch * self.dpi)

        # 初始化行和列信息
        rows_info = []
        columns_info = []

        # 获取真实 Bbox 并处理行信息
        row_heights = {}  # 记录每行的最大高度
        row_y_positions = {}  # 记录每行的最小Y位置（最靠上的顶边）

        # 遍历所有单元格获取真实 Bbox
        for (row_idx, col_idx), cell in table.get_celld().items():
            # 获取单元格的窗口范围（像素坐标）
            bbox = cell.get_window_extent(renderer=fig.canvas.get_renderer())

            # 转换坐标系：Matplotlib 原点在左下角，我们需要原点在左上角
            # Layout_Y = Image_Total_Height - Bbox.y1 (Top_Edge)
            layout_y = image_height - bbox.y1
            layout_height = bbox.height

            # 更新行信息：取该行所有单元格中 height 的最大值
            if row_idx not in row_heights:
                row_heights[row_idx] = layout_height
            else:
                row_heights[row_idx] = max(row_heights[row_idx], layout_height)

            # 更新行Y位置：取该行所有单元格中 y 的最小值（即最靠上的顶边）
            if row_idx not in row_y_positions:
                row_y_positions[row_idx] = layout_y
            else:
                row_y_positions[row_idx] = min(row_y_positions[row_idx], layout_y)

        # 生成行信息
        for row_idx in range(num_rows):
            rows_info.append({
                "index": row_idx,
                "y": row_y_positions[row_idx],
                "height": row_heights[row_idx]
            })

        # 处理列信息
        col_x_positions = {}
        col_widths = {}

        for (row_idx, col_idx), cell in table.get_celld().items():
            if row_idx == 0:  # 只处理第一行的列信息
                bbox = cell.get_window_extent(renderer=fig.canvas.get_renderer())
                layout_x = bbox.x0  # X坐标不需要转换

                # 更新列信息
                if col_idx not in col_x_positions:
                    col_x_positions[col_idx] = layout_x
                    col_widths[col_idx] = bbox.width

        # 生成列信息（按列索引排序）
        for col_idx in range(num_columns):
            if col_idx in col_x_positions:
                columns_info.append({
                    "index": col_idx,
                    "x": col_x_positions[col_idx],
                    "width": col_widths[col_idx]
                })

        # 计算表格边界
        if rows_info and columns_info:
            min_x = min(col['x'] for col in columns_info)
            max_x = max(col['x'] + col['width'] for col in columns_info)
            min_y = min(row['y'] for row in rows_info)
            max_y = max(row['y'] + row['height'] for row in rows_info)

            table_bounds = {
                "x": min_x,
                "y": min_y,
                "width": max_x - min_x,
                "height": max_y - min_y
            }
        else:
            table_bounds = {"x": 0, "y": 0, "width": 0, "height": 0}

        # 关闭图表
        plt.close(fig)

        # 返回布局信息
        return {
            "rows": rows_info,
            "columns": columns_info,
            "image_size": {
                "width": image_width,
                "height": image_height
            },
            "table_bounds": table_bounds,
            "metadata": {
                "num_rows": num_rows,
                "num_columns": num_columns,
                "dpi": self.dpi,
                "generated_at": pd.Timestamp.now().isoformat()
            }
        }
