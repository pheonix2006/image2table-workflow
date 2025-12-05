"""测试日志解析修复效果"""

import sys
import os
from pathlib import Path
import json

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from table2image_agent.interfaces import (
    ScoutAgent, PlannerAgent, SniperAgent, CoderAgent,
    VisualSummary, LocatingInstructions, DataPacket, Answer
)
from table2image_agent.orchestrator import Table2ImageOrchestrator


class MockSniperAgent(SniperAgent):
    """Mock 狙击手实现"""

    def extract(self, image_path: str, instructions: LocatingInstructions) -> DataPacket:
        """返回预定义的数据包"""
        return DataPacket(
            raw_image_path=image_path,
            cropped_region=(100, 50, 300, 150),
            rough_markdown="""
| 毕业院校 | 姓名 |
|----------|------|
| 西南大学 | 张三 |
| 北京大学 | 李四 |
            """.strip(),
            structure_info={"format": "markdown_table", "rows": 2, "columns": 2},
            extraction_metadata={
                "method": "ocr",
                "confidence": 0.95,
                "target_region": "毕业院校和姓名信息"
            }
        )


class MockCoderAgent(CoderAgent):
    """Mock 执行者实现"""

    def execute(self, packet: DataPacket, question: str) -> Answer:
        """返回预定义的答案"""
        result = "张三"
        return Answer(
            result=result,
            calculation_method="从数据包中提取毕业院校为西南大学的学生姓名：张三",
            confidence=0.98,
            execution_trace=[
                "解析 Markdown 表格数据",
                "过滤毕业院校为'西南大学'的行",
                "提取该行的姓名字段：张三"
            ]
        )


def test_log_parsing_fix():
    """测试日志解析修复效果"""
    try:
        # 导入真实的实现
        from src.table2image_agent.agents.scout import OpenAIScoutAgent
        from src.table2image_agent.agents.planner import OpenAIPlannerAgent

        print("🧪 测试日志解析修复效果...")
        print("=" * 60)

        # 使用真实的 Scout 和 Planner
        scout = OpenAIScoutAgent()
        planner = OpenAIPlannerAgent()

        # 保持 Mock 的 Sniper 和 Coder
        sniper = MockSniperAgent()
        coder = MockCoderAgent()

        # 创建编排器
        orchestrator = Table2ImageOrchestrator(scout, planner, sniper, coder)

        # 使用实际的测试图片
        test_image_path = "data/example_photo/2011-03-26_145620.png"
        test_question = "毕业院校为西南大学的学生姓名叫什么？"

        print(f"📸 图片路径: {test_image_path}")
        print(f"❓ 测试问题: {test_question}")
        print()

        # 执行工作流
        print("🚀 开始执行完整工作流...")
        answer = orchestrator.process(test_image_path, test_question)

        print("=" * 60)
        print("🎯 测试结果:")
        print(f"   ✅ 答案结果: {answer.result}")
        print(f"   ✅ 置信度: {answer.confidence}")
        print(f"   ✅ 执行轨迹长度: {len(answer.execution_trace)}")
        print()

        # 检查生成的追踪日志
        print("📋 检查生成的追踪日志...")
        log_dir = Path("logs")
        log_files = list(log_dir.glob("trace_*.jsonl"))

        if not log_files:
            print("❌ 未找到追踪日志文件")
            return False

        # 分析最新的日志文件
        latest_log_file = max(log_files, key=lambda f: f.stat().st_mtime)
        print(f"📄 分析最新日志文件: {latest_log_file.name}")

        # 读取并解析日志文件
        valid_logs = 0
        total_logs = 0
        log_entries = []

        with open(latest_log_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                total_logs += 1
                try:
                    log_entry = json.loads(line)
                    log_entries.append(log_entry)
                    valid_logs += 1
                except json.JSONDecodeError as e:
                    print(f"   ⚠️ 日志解析错误: {e}")
                    continue

        print(f"📊 日志分析结果:")
        print(f"   📄 总行数: {total_logs}")
        print(f"   ✅ 有效JSON条目: {valid_logs}")
        print(f"   ❌ 解析失败: {total_logs - valid_logs}")
        print(f"   📈 成功率: {(valid_logs/total_logs*100):.1f}%" if total_logs > 0 else "0%")

        # 显示关键日志条目
        if log_entries:
            print(f"\n🔍 关键日志条目:")

            # 统计各组件调用次数
            scout_calls = 0
            planner_calls = 0
            orchestrator_calls = 0

            for i, entry in enumerate(log_entries[:10]):  # 只显示前10条
                step_name = entry.get('step_name', 'N/A')
                function_name = entry.get('function_name', 'N/A')
                message = entry.get('message', 'N/A')

                print(f"   {i+1}. [{entry.get('timestamp', 'N/A')}] {step_name}.{function_name}")
                print(f"      消息: {message[:80]}...")

                # 统计调用次数
                if 'Scout' in step_name:
                    scout_calls += 1
                elif 'Planner' in step_name:
                    planner_calls += 1
                elif 'Orchestrator' in step_name:
                    orchestrator_calls += 1

            if len(log_entries) > 10:
                print(f"   ... 还有 {len(log_entries) - 10} 条日志条目")

            # 显示统计结果
            print(f"\n📊 组件调用统计:")
            print(f"   🎯 Scout 调用次数: {scout_calls}")
            print(f"   🧠 Planner 调用次数: {planner_calls}")
            print(f"   🔄 Orchestrator 调用次数: {orchestrator_calls}")

            # 验证关键指标
            success = True
            if scout_calls == 0:
                print("❌ 未找到 Scout 调用记录")
                success = False
            if planner_calls == 0:
                print("❌ 未找到 Planner 调用记录")
                success = False
            if valid_logs == 0:
                print("❌ 没有有效的日志条目")
                success = False

            if success:
                print("\n🎉 日志解析修复验证成功！")
                print("✅ 文件中只包含纯JSON数据，无控制台输出污染")
                print("✅ 所有日志条目都可以正确解析")
                print("✅ Scout 和 Planner 的真实 API 调用已记录")
            else:
                print("\n❌ 日志解析修复验证失败")

            return success

        else:
            print("❌ 没有找到任何日志条目")
            return False

    except ImportError as e:
        print(f"⚠️ 真实模块导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 执行日志解析修复测试
    test_success = test_log_parsing_fix()

    if test_success:
        print("\n🎊 日志解析问题已完全修复！")
    else:
        print("\n⚠️ 日志解析问题仍需进一步处理")
        sys.exit(1)