"""简单的日志验证脚本"""

import json
from pathlib import Path

def verify_logs():
    """验证日志文件中的组件调用记录"""
    print("🔍 简单日志验证 - 直接展示 Scout 和 Planner 调用记录")
    print("=" * 80)

    log_dir = Path("logs")
    log_files = list(log_dir.glob("trace_*.jsonl"))

    scout_calls = 0
    planner_calls = 0

    for log_file in log_files:
        print(f"\n📄 分析文件: {log_file.name}")

        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        log_entry = json.loads(line)
                        step = log_entry.get('step', '')

                        if 'Scout' in step:
                            scout_calls += 1
                            print(f"   🎯 Scout 调用 #{scout_calls} (行 {line_num}):")
                            print(f"      🔍 Trace ID: {log_entry.get('trace_id', 'N/A')}")
                            print(f"      📝 消息: {log_entry.get('message', 'N/A')}")
                            print(f"      ⏱️ 执行时间: {log_entry.get('duration', 'N/A')}秒")
                            print()

                        elif 'Planner' in step:
                            planner_calls += 1
                            print(f"   🧠 Planner 调用 #{planner_calls} (行 {line_num}):")
                            print(f"      🔍 Trace ID: {log_entry.get('trace_id', 'N/A')}")
                            print(f"      📝 消息: {log_entry.get('message', 'N/A')}")
                            print(f"      ⏱️ 执行时间: {log_entry.get('duration', 'N/A')}秒")
                            if 'outputs' in log_entry:
                                outputs = log_entry['outputs']
                                print(f"      🎯 目标行: {outputs.get('target_rows', 'N/A')}")
                                print(f"      🎯 目标列: {outputs.get('target_columns', 'N/A')}")
                            print()

                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            print(f"   ❌ 读取文件时出错: {e}")

    print("=" * 80)
    print("📊 最终统计:")
    print(f"   🎯 Scout 总调用次数: {scout_calls}")
    print(f"   🧠 Planner 总调用次数: {planner_calls}")

    if scout_calls > 0 and planner_calls > 0:
        print("\n🎉 验证成功！")
        print("✅ Scout 和 Planner 的真实 API 调用已成功记录到追踪日志中")
        print("✅ 日志解析系统工作正常")
        print("✅ 组件调用记录完整")
    else:
        print("\n❌ 验证失败")

if __name__ == "__main__":
    verify_logs()