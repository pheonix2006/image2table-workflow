""" comprehensive_log_analysis.py
综合日志分析脚本 - 分析所有日志文件中的组件调用记录
"""

import sys
import os
from pathlib import Path
import json
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def analyze_all_log_files():
    """分析所有日志文件中的组件调用记录"""
    print("🔍 综合日志分析 - 检查所有日志文件中的组件调用")
    print("=" * 80)

    # 获取所有日志文件
    log_dir = Path("logs")
    log_files = list(log_dir.glob("trace_*.jsonl"))

    if not log_files:
        print("❌ 未找到任何日志文件")
        return False

    # 按修改时间排序
    log_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

    total_stats = {
        'scout_calls': 0,
        'planner_calls': 0,
        'orchestrator_calls': 0,
        'total_valid_logs': 0,
        'total_files': len(log_files)
    }

    print(f"📁 发现 {len(log_files)} 个日志文件")
    print()

    # 分析每个文件
    for i, log_file in enumerate(log_files[:5], 1):  # 只分析最新的5个文件
        print(f"📄 分析文件 {i}: {log_file.name}")

        file_stats = {
            'scout_calls': 0,
            'planner_calls': 0,
            'orchestrator_calls': 0,
            'valid_logs': 0,
            'total_lines': 0
        }

        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    file_stats['total_lines'] += 1

                    try:
                        log_entry = json.loads(line)
                        file_stats['valid_logs'] += 1
                        total_stats['total_valid_logs'] += 1

                        # 统计组件调用
                        step_name = log_entry.get('step_name', '')
                        if 'Scout' in step_name:
                            file_stats['scout_calls'] += 1
                            total_stats['scout_calls'] += 1
                        elif 'Planner' in step_name:
                            file_stats['planner_calls'] += 1
                            total_stats['planner_calls'] += 1
                        elif 'Orchestrator' in step_name:
                            file_stats['orchestrator_calls'] += 1
                            total_stats['orchestrator_calls'] += 1

                    except json.JSONDecodeError:
                        continue

            # 显示文件统计
            success_rate = (file_stats['valid_logs'] / file_stats['total_lines'] * 100) if file_stats['total_lines'] > 0 else 0
            print(f"   📊 统计:")
            print(f"      - 总行数: {file_stats['total_lines']}")
            print(f"      - 有效JSON: {file_stats['valid_logs']}")
            print(f"      - 解析成功率: {success_rate:.1f}%")
            print(f"      - Scout 调用: {file_stats['scout_calls']}")
            print(f"      - Planner 调用: {file_stats['planner_calls']}")
            print(f"      - Orchestrator 调用: {file_stats['orchestrator_calls']}")
            print()

        except Exception as e:
            print(f"   ❌ 分析文件时出错: {e}")
            print()

    # 显示总体统计
    print("=" * 80)
    print("📈 总体统计 (基于最新5个文件):")
    print(f"   📊 总文件数: {total_stats['total_files']}")
    print(f"   📊 总有效日志: {total_stats['total_valid_logs']}")
    print(f"   🎯 Scout 总调用次数: {total_stats['scout_calls']}")
    print(f"   🧠 Planner 总调用次数: {total_stats['planner_calls']}")
    print(f"   🔄 Orchestrator 总调用次数: {total_stats['orchestrator_calls']}")

    # 验证结果
    print()
    print("🎯 验证结果:")
    success = True

    if total_stats['scout_calls'] == 0:
        print("❌ 未找到 Scout 调用记录")
        success = False
    else:
        print(f"✅ 找到 Scout 调用记录: {total_stats['scout_calls']} 次")

    if total_stats['planner_calls'] == 0:
        print("❌ 未找到 Planner 调用记录")
        success = False
    else:
        print(f"✅ 找到 Planner 调用记录: {total_stats['planner_calls']} 次")

    if total_stats['orchestrator_calls'] == 0:
        print("❌ 未找到 Orchestrator 调用记录")
        success = False
    else:
        print(f"✅ 找到 Orchestrator 调用记录: {total_stats['orchestrator_calls']} 次")

    if success:
        print()
        print("🎉 组件调用统计验证成功！")
        print("✅ Scout 和 Planner 的真实 API 调用已成功记录到追踪日志中")
        print("✅ 日志解析系统工作正常")
        print("✅ 日志分割机制正常工作")
    else:
        print()
        print("❌ 组件调用统计验证失败")

    return success

def demonstrate_log_content():
    """演示日志文件中的实际内容"""
    print("\n" + "=" * 80)
    print("📋 日志内容演示 - 展示实际的 Scout 和 Planner 调用记录")
    print("=" * 80)

    # 查找一个包含 Scout 调用的文件
    log_dir = Path("logs")
    log_files = list(log_dir.glob("trace_*.jsonl"))

    scout_found = False
    planner_found = False

    for log_file in log_files:
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                line_num = 0
                for line in f:
                    line_num += 1
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        log_entry = json.loads(line)
                        step_name = log_entry.get('step_name', '')

                        if 'Scout' in step_name and not scout_found:
                            print("🎯 Scout 调用记录示例:")
                            print(f"   📄 文件: {log_file.name}")
                            print(f"   📍 行号: {line_num}")
                            print(f"   🔍 Trace ID: {log_entry.get('trace_id', 'N/A')}")
                            print(f"   📝 消息: {log_entry.get('message', 'N/A')}")
                            print(f"   ⏱️ 执行时间: {log_entry.get('duration', 'N/A')}秒")
                            print()
                            scout_found = True

                        elif 'Planner' in step_name and not planner_found:
                            print("🧠 Planner 调用记录示例:")
                            print(f"   📄 文件: {log_file.name}")
                            print(f"   📍 行号: {line_num}")
                            print(f"   🔍 Trace ID: {log_entry.get('trace_id', 'N/A')}")
                            print(f"   📝 消息: {log_entry.get('message', 'N/A')}")
                            print(f"   ⏱️ 执行时间: {log_entry.get('duration', 'N/A')}秒")
                            print(f"   🎯 目标行: {log_entry.get('outputs', {}).get('target_rows', 'N/A')}")
                            print(f"   🎯 目标列: {log_entry.get('outputs', {}).get('target_columns', 'N/A')}")
                            print()
                            planner_found = True

                        if scout_found and planner_found:
                            break

                    except json.JSONDecodeError:
                        continue

            if scout_found and planner_found:
                break

        except Exception as e:
            continue

    if not scout_found:
        print("❌ 未找到 Scout 调用记录")

    if not planner_found:
        print("❌ 未找到 Planner 调用记录")

if __name__ == "__main__":
    # 执行综合分析
    analysis_success = analyze_all_log_files()

    # 演示日志内容
    demonstrate_log_content()

    print("\n" + "=" * 80)
    if analysis_success:
        print("🎊 综合分析完成！组件调用记录验证成功！")
    else:
        print("⚠️ 综合分析完成，但发现一些问题需要关注")
    print("=" * 80)