"""WikiTQ 批处理脚本：将 CSV 数据转换为表格图片和元数据。

读取 data/example_tablequestion/wiki_table_100_samples.csv
处理前 5 个样本，生成:
- data/processed/sample_{id}.png (渲染的表格图片)
- data/processed/sample_{id}.json (包含问题、答案和 Markdown 内容)
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from table2image_agent.utils.renderer import TableRenderer


def main():
    """主处理函数"""
    # 文件路径
    csv_path = "data/example_tablequestion/wiki_table_100_samples.csv"
    output_dir = "data/layout_fix_demo"

    print("🚀 开始处理 WikiTQ 数据集...")
    print(f"📁 输入文件: {csv_path}")
    print(f"📁 输出目录: {output_dir}")

    # 检查输入文件
    if not Path(csv_path).exists():
        print(f"❌ 错误: 输入文件不存在 - {csv_path}")
        return 1

    # 确保输出目录存在
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # 读取 CSV 数据
    try:
        df = pd.read_csv(csv_path, keep_default_na=False, na_values=[])
        print(f"✅ 成功读取 CSV，共 {len(df)} 行数据")
    except Exception as e:
        print(f"❌ 读取 CSV 失败: {e}")
        return 1

    # 创建渲染器
    renderer = TableRenderer()

    # 处理前 5 行（用于测试）
    samples_to_process = min(5, len(df))
    print(f"🎯 处理前 {samples_to_process} 个样本...")

    success_count = 0
    for i in range(samples_to_process):
        try:
            row = df.iloc[i]

            # 解析数据
            table_array_str = row['table_array']
            question = row['question']
            answer = row['answer']

            print(f"\n📋 处理样本 {i+1}/{samples_to_process}:")
            print(f"   问题: {question}")
            print(f"   答案: {answer}")
            print(f"   数据: {table_array_str}")

            # 调用渲染器处理
            result = renderer.render_wiki_table(
                table_array_str=table_array_str,
                question=question,
                answer=answer,
                output_dir=output_dir,
                sample_id=i+1
            )

            # 生成布局文件（使用修复后的 _generate_table_layout 方法）
            table_data = renderer.parse_csv_table_array(table_array_str)
            layout = renderer._generate_table_layout(table_data)

            # 保存布局文件
            layout_path = os.path.join(output_dir, f"sample_{i+1}_layout.json")
            with open(layout_path, 'w', encoding='utf-8') as f:
                json.dump(layout, f, ensure_ascii=False, indent=2)

            print(f"   ✅ 图片: {result['image_path']}")
            print(f"   ✅ 元数据: 包含问题、答案和 Markdown 内容")
            print(f"   ✅ 布局: 使用真实Bbox测量的坐标信息")

            success_count += 1

        except Exception as e:
            print(f"   ❌ 处理失败: {e}")
            continue

    # 输出处理结果
    print(f"\n🎉 处理完成!")
    print(f"   成功处理: {success_count}/{samples_to_process} 个样本")
    print(f"   输出目录: {Path(output_dir).absolute()}")

    # 显示输出目录内容
    try:
        processed_files = list(Path(output_dir).glob("*"))
        png_files = [f for f in processed_files if f.suffix == '.png']
        json_files = [f for f in processed_files if f.suffix == '.json']

        print(f"   生成图片: {len(png_files)} 个")
        print(f"   生成元数据: {len(json_files)} 个")

        if png_files:
            print("   🖼️ 图片文件:")
            for png_file in sorted(png_files):
                file_size = png_file.stat().st_size
                print(f"     - {png_file.name} ({file_size} 字节)")

        if json_files:
            print("   📄 元数据文件:")
            for json_file in sorted(json_files):
                print(f"     - {json_file.name}")

    except Exception as e:
        print(f"   ⚠️  无法列出输出文件: {e}")

    return 0 if success_count == samples_to_process else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)