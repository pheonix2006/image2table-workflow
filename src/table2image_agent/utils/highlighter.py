"""VisualHighlighter - 表格语义高亮工具。

支持在现有表格图片上进行语义高亮 (Semantic Highlighting)，
用于 Visual-CoT (视觉思维链) 推理。

核心功能：
- 坐标解析：根据 Layout JSON 解析行、列、单元格坐标
- 绘制逻辑：使用 PIL 绘制半透明彩色蒙层
- 颜色方案：SCAN (黄色)、FOCUS (红色)、ANSWER (绿色)
"""

import json
from pathlib import Path
from typing import Dict, List, Literal, Tuple

from PIL import Image, ImageDraw


ColorScheme = Literal["scan", "focus", "answer"]
HighlightType = Literal["col", "row", "cell"]
HighlightInstruction = Dict[str, str | int | ColorScheme]


class VisualHighlighter:
    """表格视觉高亮器。

    根据 Layout 坐标和高亮指令在图片上绘制半透明彩色蒙层。
    """

    # 颜色方案定义 (RGB)
    COLOR_MAP: Dict[ColorScheme, Tuple[int, int, int]] = {
        "scan": (255, 255, 0),  # 黄色 - 扫描关注
        "focus": (255, 0, 0),  # 红色 - 逻辑锁定
        "answer": (0, 255, 0),  # 绿色 - 最终答案
    }

    # Alpha 透明度值 (0-255) - 边框模式使用不透明颜色
    DEFAULT_ALPHA = 255  # 边框模式使用不透明颜色
    DEFAULT_BORDER_WIDTH = 3  # 边框宽度

    def __init__(self, border_width: int | None = None):
        """初始化高亮器。

        Args:
            border_width: 边框宽度（像素），默认 3
        """
        self.border_width = border_width if border_width is not None else self.DEFAULT_BORDER_WIDTH

    def highlight(
        self,
        image_path: str | Path,
        layout_path: str | Path,
        output_path: str | Path,
        instructions: List[HighlightInstruction],
    ) -> None:
        """在图片上绘制高亮边框。

        Args:
            image_path: 输入图片路径
            layout_path: Layout JSON 文件路径
            output_path: 输出图片路径
            instructions: 高亮指令列表，每个指令包含:
                - type: "col", "row", 或 "cell"
                - index: 行/列索引（对 cell 需要 row 和 col）
                - row: 行索引（仅 cell 类型）
                - col: 列索引（仅 cell 类型）
                - color: "scan", "focus", 或 "answer"
        """
        # 加载图片（保持原图格式）
        image = Image.open(image_path).convert("RGBA")

        # 加载 Layout
        with open(layout_path, "r", encoding="utf-8") as f:
            layout = json.load(f)

        # 创建绘制层
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # 处理每个高亮指令
        for instruction in instructions:
            self._apply_highlight(draw, layout, instruction)

        # 合并原图和高亮层
        highlighted_image = Image.alpha_composite(image, overlay)

        # 转换回 RGB 并保存
        highlighted_image.convert("RGB").save(output_path, "PNG")

    def _apply_highlight(
        self,
        draw: ImageDraw.ImageDraw,
        layout: Dict,
        instruction: HighlightInstruction,
    ) -> None:
        """应用单个高亮指令。

        Args:
            draw: PIL ImageDraw 对象
            layout: Layout 数据
            instruction: 高亮指令
        """
        highlight_type: HighlightType = instruction["type"]  # type: ignore
        color: ColorScheme = instruction["color"]  # type: ignore

        # 解析颜色（边框模式使用不透明颜色）
        rgb = self.COLOR_MAP[color]
        border_color = rgb + (self.DEFAULT_ALPHA,)

        # 根据类型计算矩形
        if highlight_type == "col":
            rect = self._get_column_rect(layout, int(instruction["index"]))  # type: ignore
        elif highlight_type == "row":
            rect = self._get_row_rect(layout, int(instruction["index"]))  # type: ignore
        elif highlight_type == "cell":
            rect = self._get_cell_rect(
                layout,
                int(instruction["row"]),  # type: ignore
                int(instruction["col"]),  # type: ignore
            )
        else:
            raise ValueError(f"未知的高亮类型: {highlight_type}")

        # 绘制边框（而不是填充）
        draw.rectangle(
            [
                (rect["x"], rect["y"]),
                (rect["x"] + rect["width"], rect["y"] + rect["height"]),
            ],
            outline=border_color,
            width=self.border_width,
        )

    def _get_column_rect(
        self, layout: Dict, col_idx: int
    ) -> Dict[str, float]:
        """计算列的矩形区域。

        读取 columns[col_idx] 的 x 和 width，
        y 和 height 取 table_bounds 的全高。

        Args:
            layout: Layout 数据
            col_idx: 列索引

        Returns:
            矩形区域字典 {x, y, width, height}
        """
        column = layout["columns"][col_idx]
        bounds = layout["table_bounds"]

        return {
            "x": column["x"],
            "y": bounds["y"],
            "width": column["width"],
            "height": bounds["height"],
        }

    def _get_row_rect(
        self, layout: Dict, row_idx: int
    ) -> Dict[str, float]:
        """计算行的矩形区域。

        读取 rows[row_idx] 的 y 和 height，
        x 和 width 取 table_bounds 的全宽。

        Args:
            layout: Layout 数据
            row_idx: 行索引

        Returns:
            矩形区域字典 {x, y, width, height}
        """
        row = layout["rows"][row_idx]
        bounds = layout["table_bounds"]

        return {
            "x": bounds["x"],
            "y": row["y"],
            "width": bounds["width"],
            "height": row["height"],
        }

    def _get_cell_rect(
        self, layout: Dict, row_idx: int, col_idx: int
    ) -> Dict[str, float]:
        """计算单元格的矩形区域。

        计算行列交点：
        x = columns[col_idx]['x']
        y = rows[row_idx]['y']
        width = columns[col_idx]['width']
        height = rows[row_idx]['height']

        Args:
            layout: Layout 数据
            row_idx: 行索引
            col_idx: 列索引

        Returns:
            矩形区域字典 {x, y, width, height}
        """
        column = layout["columns"][col_idx]
        row = layout["rows"][row_idx]

        return {
            "x": column["x"],
            "y": row["y"],
            "width": column["width"],
            "height": row["height"],
        }
