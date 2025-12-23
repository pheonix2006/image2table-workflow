"""Auto-Fit 布局下的 VisualHighlighter 验证脚本。

使用新生成的 Auto-Fit 兼容布局文件，验证高亮效果。
"""

from pathlib import Path
from table2image_agent.utils.highlighter import VisualHighlighter

# 数据源路径
DATA_DIR = Path(__file__).parent.parent / "data" / "layout_fix_demo"
IMAGE_PATH = DATA_DIR / "sample_1.png"
LAYOUT_PATH = DATA_DIR / "sample_1_layout.json"

# 输出目录
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "layout_fix_demo"


def main():
    """验证三种高亮场景"""
    print("=" * 60)
    print("Auto-Fit 布局高亮验证脚本")
    print("=" * 60)

    # 验证数据源存在
    if not IMAGE_PATH.exists():
        print(f"❌ 错误: 图片文件不存在: {IMAGE_PATH}")
        return

    if not LAYOUT_PATH.exists():
        print(f"❌ 错误: Layout 文件不存在: {LAYOUT_PATH}")
        return

    print(f"✅ 数据源:")
    print(f"   图片: {IMAGE_PATH}")
    print(f"   Layout: {LAYOUT_PATH}")
    print()

    # 创建高亮器
    highlighter = VisualHighlighter(border_width=3)

    # 场景 A: 列扫描 (黄色) - 高亮 Year (Col 0), Venue (Col 2), Position (Col 3)
    print("📌 场景 A: 列扫描 (SCAN - 黄色)")
    print("   高亮 Year (Col 0), Position (Col 3), Venue (Col 2)")
    output_columns = OUTPUT_DIR / "output_autofit_columns.png"
    highlighter.highlight(
        IMAGE_PATH,
        LAYOUT_PATH,
        output_columns,
        [
            {"type": "col", "index": 0, "color": "scan"},
            {"type": "col", "index": 3, "color": "scan"},
            {"type": "col", "index": 2, "color": "scan"},
        ],
    )
    print(f"   输出: {output_columns}")
    print()

    # 场景 B: 精确锁定 (红色) - 高亮 Row 15 的 Year (Col 0) 和 Position (Col 3)
    print("📌 场景 B: 精确锁定 (FOCUS - 红色)")
    print("   高亮 Row 15 的 Year (Col 0) 和 Position (Col 3) (2008年, 4th)")
    output_focus = OUTPUT_DIR / "output_autofit_focus.png"
    highlighter.highlight(
        IMAGE_PATH,
        LAYOUT_PATH,
        output_focus,
        [
            {"type": "cell", "row": 15, "col": 0, "color": "focus"},
            {"type": "cell", "row": 15, "col": 3, "color": "focus"},
        ],
    )
    print(f"   输出: {output_focus}")
    print()

    # 场景 C: 答案高亮 (绿色) - 高亮 Row 14 的 Venue (Col 2)
    print("📌 场景 C: 答案高亮 (ANSWER - 绿色)")
    print("   高亮 Row 14 的 Venue (Col 2)")
    output_answer = OUTPUT_DIR / "output_autofit_answer.png"
    highlighter.highlight(
        IMAGE_PATH,
        LAYOUT_PATH,
        output_answer,
        [
            {"type": "cell", "row": 14, "col": 2, "color": "answer"},
        ],
    )
    print(f"   输出: {output_answer}")
    print()

    # 验证输出文件
    print("=" * 60)
    print("📊 输出验证:")
    print("=" * 60)

    for output_file in [output_columns, output_focus, output_answer]:
        if output_file.exists():
            size = output_file.stat().st_size
            print(f"✅ {output_file.name}: {size} 字节")
        else:
            print(f"❌ {output_file.name}: 未生成")

    print()
    print("=" * 60)
    print("🎉 验证完成！")
    print("=" * 60)
    print("\n请打开以下图片，验证 Auto-Fit 布局下的高亮对齐：")
    print("1. output_autofit_columns.png")
    print("2. output_autofit_focus.png")
    print("3. output_autofit_answer.png")


if __name__ == "__main__":
    main()