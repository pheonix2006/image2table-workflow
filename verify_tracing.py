#!/usr/bin/env python3
"""
验证追踪系统输出结果的脚本
"""

import json
from pathlib import Path


def verify_tracing_output():
    """验证追踪系统输出"""
    print("=== 验证追踪系统输出 ===")

    logs_dir = Path("logs")
    jsonl_files = list(logs_dir.glob("*.jsonl"))

    if not jsonl_files:
        print("❌ 未找到JSONL文件")
        return

    # 选择最新的文件
    latest_file = max(jsonl_files, key=lambda x: x.stat().st_mtime)
    print(f"📁 检查文件: {latest_file.name}")
    print()

    with open(latest_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    json_lines = []
    control_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith('🔍 [') or line.startswith('📊') or '🚀' in line or '🔵' in line or '🟢' in line or '🔴' in line:
            control_lines.append(line)
        elif line.startswith('{'):
            try:
                json_data = json.loads(line)
                json_lines.append(json_data)
            except json.JSONDecodeError:
                print(f"⚠️  JSON解析失败: {line[:100]}...")
        else:
            control_lines.append(line)

    print(f"✅ 控制台输出行: {len(control_lines)}")
    print(f"✅ JSON数据行: {len(json_lines)}")
    print()

    # 验证JSON数据结构
    valid_json_entries = 0
    for entry in json_lines:
        required_fields = ['timestamp', 'level', 'trace_id', 'message']
        if all(field in entry for field in required_fields):
            valid_json_entries += 1

            # 验证数据截断功能
            if 'outputs' in entry:
                outputs = entry['outputs']
                if isinstance(outputs, dict):
                    for key, value in outputs.items():
                        if 'Truncated' in str(value):
                            print(f"✅ 长数据截断生效: {key} -> {value}")

            if 'inputs' in entry:
                inputs = entry['inputs']
                if isinstance(inputs, dict) and 'args' in inputs:
                    for arg in inputs['args']:
                        if isinstance(arg, str) and len(arg) > 1000:
                            if 'Truncated' in str(arg):
                                print(f"✅ 输入参数截断生效: 长字符串被截断")
                            else:
                                print(f"⚠️  长字符串未被截断: {arg[:50]}...")

    print(f"✅ 有效JSON条目: {valid_json_entries}/{len(json_lines)}")

    # 显示示例JSON条目
    if json_lines:
        print("\n📋 示例JSON日志条目:")
        example = json_lines[0]
        print(json.dumps(example, indent=2, ensure_ascii=False))

    print("\n🎉 追踪系统验证完成！")
    print(f"📄 详细日志文件: {latest_file}")


if __name__ == "__main__":
    verify_tracing_output()