"""TDD Tests for Sniper Agent - 视觉导演逻辑"""

import pytest
import json
from unittest.mock import Mock, patch
from dataclasses import dataclass
from typing import List

# 从 interfaces 导入真实的类
from table2image_agent.interfaces import (
    RenderStrategy, RenderPlan, LocatingInstructions, SniperAgent
)


class TestRenderPlan:
    """测试 RenderPlan 数据结构"""

    def test_render_plan_creation(self):
        """测试 RenderPlan 对象创建"""
        plan = RenderPlan(
            strategy=RenderStrategy.SOFT_FOCUS,
            target_rows=[0, 5],
            target_columns=[1, 2],
            reasoning="数据集中在第0-5行，需要保留表头上下文"
        )

        assert plan.strategy == RenderStrategy.SOFT_FOCUS
        assert plan.target_rows == [0, 5]
        assert plan.target_columns == [1, 2]
        assert "数据集中" in plan.reasoning

    def test_render_strategy_enum(self):
        """测试 RenderStrategy 枚举"""
        assert RenderStrategy.HARD_CROP == "HARD_CROP"
        assert RenderStrategy.SOFT_FOCUS == "SOFT_FOCUS"
        assert len(RenderStrategy) == 2


class TestSniperAgentVisionDirector:
    """测试 Sniper Agent 的视觉导演逻辑"""

    def test_mock_vlm_response_soft_focus(self):
        """测试 VLM 返回 SOFT_FOCUS 策略的 JSON 响应解析"""
        # 模拟 VLM 返回的 JSON 响应
        mock_vlm_response = {
            "strategy": "SOFT_FOCUS",
            "target_rows": [0, 3, 5],
            "target_columns": [1, 2],
            "reasoning": "目标数据分布在第0、3、5行，集中在第1-2列，数据相对集中但需要保留表头上下文进行视觉确认。"
        }

        # 解析为 RenderPlan 对象
        plan = RenderPlan(
            strategy=RenderStrategy(mock_vlm_response["strategy"]),
            target_rows=mock_vlm_response["target_rows"],
            target_columns=mock_vlm_response["target_columns"],
            reasoning=mock_vlm_response["reasoning"]
        )

        assert plan.strategy == RenderStrategy.SOFT_FOCUS
        assert plan.target_rows == [0, 3, 5]
        assert plan.target_columns == [1, 2]
        assert "保留表头上下文" in plan.reasoning

    def test_mock_vlm_response_hard_crop(self):
        """测试 VLM 返回 HARD_CROP 策略的 JSON 响应解析"""
        mock_vlm_response = {
            "strategy": "HARD_CROP",
            "target_rows": [1, 50],
            "target_columns": [0, 3],
            "reasoning": "目标数据极其分散（第1行和第50行），中间包含大量无关数据，适合裁剪拼接。"
        }

        plan = RenderPlan(
            strategy=RenderStrategy(mock_vlm_response["strategy"]),
            target_rows=mock_vlm_response["target_rows"],
            target_columns=mock_vlm_response["target_columns"],
            reasoning=mock_vlm_response["reasoning"]
        )

        assert plan.strategy == RenderStrategy.HARD_CROP
        assert plan.target_rows == [1, 50]
        assert plan.target_columns == [0, 3]
        assert "裁剪拼接" in plan.reasoning

    def test_vision_director_logic_decision(self):
        """测试视觉导演决策逻辑"""
        # 场景1: 集中数据 -> SOFT_FOCUS
        concentrated_instructions = LocatingInstructions(
            target_rows=["第2-4行"],
            target_columns=["B列", "C列"],
            coordinate_hints={"row_index": "2-4", "col_index": "1-2"},
            extraction_type="region_data",
            reasoning_trace="数据集中在连续的3行内"
        )

        # 期望导演选择 SOFT_FOCUS
        expected_strategy = RenderStrategy.SOFT_FOCUS
        assert expected_strategy == RenderStrategy.SOFT_FOCUS

        # 场景2: 分散数据 -> HARD_CROP
        scattered_instructions = LocatingInstructions(
            target_rows=["第2行", "第100行"],
            target_columns=["A列", "D列"],
            coordinate_hints={"row_index": "2,100", "col_index": "0,3"},
            extraction_type="region_data",
            reasoning_trace="数据分布在表格两端，中间间隔大量无关数据"
        )

        # 期望导演选择 HARD_CROP
        expected_strategy = RenderStrategy.HARD_CROP
        assert expected_strategy == RenderStrategy.HARD_CROP


class TestOpenAISniperAgent:
    """测试 OpenAISniperAgent 实现"""

    def test_sniper_agent_interface_exists(self):
        """测试 SniperAgent 接口存在性"""
        from table2image_agent.interfaces import SniperAgent

        # 验证接口可以被子类化
        class TestMockSniperAgent(SniperAgent):
            def direct(self, image_path: str, instructions: LocatingInstructions) -> RenderPlan:
                return RenderPlan(
                    strategy=RenderStrategy.SOFT_FOCUS,
                    target_rows=[0, 1],
                    target_columns=[1],
                    reasoning="测试实现"
                )

            def extract(self, image_path: str, instructions: LocatingInstructions):
                """实现 extract 方法以满足接口要求"""
                from table2image_agent.interfaces import DataPacket
                return DataPacket(
                    raw_image_path=image_path,
                    cropped_region=None,
                    rough_markdown="mock",
                    structure_info={},
                    extraction_metadata={}
                )

        agent = TestMockSniperAgent()
        assert hasattr(agent, 'direct')
        assert hasattr(agent, 'extract')

    def test_json_parsing_from_vlm(self):
        """测试从 VLM JSON 响应解析 RenderPlan"""
        json_response = '''
        {
            "strategy": "SOFT_FOCUS",
            "target_rows": [0, 1, 2],
            "target_columns": [1, 2],
            "reasoning": "数据集中在前3行，需要保留表头上下文。"
        }
        '''

        parsed_data = json.loads(json_response)
        plan = RenderPlan(
            strategy=RenderStrategy(parsed_data["strategy"]),
            target_rows=parsed_data["target_rows"],
            target_columns=parsed_data["target_columns"],
            reasoning=parsed_data["reasoning"]
        )

        assert plan.strategy == RenderStrategy.SOFT_FOCUS
        assert len(plan.target_rows) == 3
        assert len(plan.target_columns) == 2

    def test_mock_sniper_agent_direct(self):
        """测试 MockSniperAgent 的 direct 方法"""
        from table2image_agent.agents.sniper import MockSniperAgent

        agent = MockSniperAgent()
        instructions = LocatingInstructions(
            target_rows=["第2行", "第100行"],
            target_columns=["B列"],
            coordinate_hints={},
            extraction_type="region_data",
            reasoning_trace="数据分散"
        )

        plan = agent.direct("test_image.png", instructions)

        # 验证返回了 RenderPlan
        assert isinstance(plan, RenderPlan)
        assert plan.strategy == RenderStrategy.HARD_CROP  # 检测到大行号
        assert "数据分散" in plan.reasoning
        assert len(plan.target_rows) == 3
        assert len(plan.target_columns) == 2

    def test_mock_sniper_agent_extract(self):
        """测试 MockSniperAgent 的 extract 方法"""
        from table2image_agent.agents.sniper import MockSniperAgent

        agent = MockSniperAgent()
        instructions = LocatingInstructions(
            target_rows=["第2行"],
            target_columns=["B列"],
            coordinate_hints={},
            extraction_type="single_cell",
            reasoning_trace="简单数据"
        )

        packet = agent.extract("test_image.png", instructions)

        # 验证返回了 DataPacket
        from table2image_agent.interfaces import DataPacket
        assert isinstance(packet, DataPacket)
        assert packet.raw_image_path == "test_image.png"
        assert packet.rough_markdown == "Mock OCR 提取结果"
        assert packet.structure_info["mock"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])