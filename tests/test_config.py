"""配置管理器测试。

验证 ConfigManager 的配置优先级、Agent 级别隔离和错误处理功能。
"""

import os
import pytest
import tempfile
from unittest.mock import patch

# 添加项目根目录到 Python 路径
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.table2image_agent.config import (
    ConfigManager,
    AgentType,
    get_scout_config,
    get_planner_config
)


class TestConfigManager:
    """配置管理器测试类"""

    def setup_method(self):
        """每个测试前清理环境变量"""
        # 清除所有相关环境变量
        env_vars_to_clear = [
            "GLOBAL_OPENAI_API_KEY", "GLOBAL_OPENAI_BASE_URL", "GLOBAL_OPENAI_MODEL",
            "SCOUT_OPENAI_API_KEY", "SCOUT_OPENAI_BASE_URL", "SCOUT_OPENAI_MODEL",
            "PLANNER_OPENAI_API_KEY", "PLANNER_OPENAI_BASE_URL", "PLANNER_OPENAI_MODEL",
            "SNIPER_OPENAI_API_KEY", "SNIPER_OPENAI_BASE_URL", "SNIPER_OPENAI_MODEL",
            "CODER_OPENAI_API_KEY", "CODER_OPENAI_BASE_URL", "CODER_OPENAI_MODEL",
            "OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL"
        ]

        for var in env_vars_to_clear:
            if var in os.environ:
                del os.environ[var]

    def test_global_config_priority(self):
        """测试全局配置优先级"""
        # 设置全局配置
        os.environ["GLOBAL_OPENAI_API_KEY"] = "global-key"
        os.environ["GLOBAL_OPENAI_BASE_URL"] = "https://global.api.com"
        os.environ["GLOBAL_OPENAI_MODEL"] = "global-model"

        # 同时设置 Agent 特定配置
        os.environ["SCOUT_OPENAI_API_KEY"] = "scout-specific-key"

        # Scout 应该使用全局配置（因为 global 优先级更高）
        config = get_scout_config()

        assert config.api_key == "global-key", "应该使用全局 API key"
        assert config.base_url == "https://global.api.com", "应该使用全局 base URL"
        assert config.model_name == "global-model", "应该使用全局 model"

        print(f"✅ 全局配置优先级测试通过")
        print(f"   API Key: {config.api_key}")
        print(f"   Model: {config.model_name}")

    def test_agent_specific_config_priority(self):
        """测试 Agent 特定配置优先级"""
        # 设置 Agent 特定配置
        os.environ["PLANNER_OPENAI_API_KEY"] = "planner-specific-key"
        os.environ["PLANNER_OPENAI_MODEL"] = "planner-specific-model"

        config = get_planner_config()

        assert config.api_key == "planner-specific-key", "应该使用 Agent 特定配置"
        assert config.model_name == "planner-specific-model", "应该使用 Agent 特定模型"

        print(f"✅ Agent 特定配置优先级测试通过")
        print(f"   API Key: {config.api_key}")
        print(f"   Model: {config.model_name}")

    def test_backward_compatibility(self):
        """测试向后兼容性（OPENAI_* 变量）"""
        # 设置旧式配置
        os.environ["OPENAI_API_KEY"] = "legacy-key"
        os.environ["OPENAI_MODEL"] = "legacy-model"

        # Scout 应该使用旧式配置（因为向后兼容）
        config = get_scout_config()

        assert config.api_key == "legacy-key", "应该使用向后兼容配置"
        assert config.model_name == "legacy-model", "应该使用向后兼容模型"

        print(f"✅ 向后兼容性测试通过")
        print(f"   API Key: {config.api_key}")
        print(f"   Model: {config.model_name}")

    def test_default_fallback(self):
        """测试默认配置回退"""
        # 不设置任何配置

        config = get_scout_config()

        assert config.api_key == ConfigManager.DEFAULT_CONFIG["api_key"]
        assert config.base_url == ConfigManager.DEFAULT_CONFIG["base_url"]
        assert config.model_name == ConfigManager.DEFAULT_CONFIG["model_name"]

        print(f"✅ 默认配置回退测试通过")
        print(f"   API Key: {config.api_key[:10]}...")
        print(f"   Base URL: {config.base_url}")
        print(f"   Model: {config.model_name}")

    def test_config_validation(self):
        """测试配置验证"""
        # 测试无效配置（缺少 API key）
        os.environ["SCOUT_OPENAI_API_KEY"] = ""  # 空值

        config = get_scout_config()

        # 配置应该仍然创建，但使用默认值
        assert config.api_key == ConfigManager.DEFAULT_CONFIG["api_key"]

        print(f"✅ 配置验证测试通过")
        print(f"   使用默认 API Key: {config.api_key[:10]}...")

    def test_config_source_detection(self):
        """测试配置来源检测"""
        # 测试 Agent 特定配置
        os.environ["PLANNER_OPENAI_API_KEY"] = "test-key"
        os.environ["PLANNER_OPENAI_MODEL"] = "test-model"

        config = get_planner_config()
        source = ConfigManager._detect_config_source(AgentType.PLANNER)

        assert source == "Agent Specific", f"应该检测到 Agent Specific 配置，实际是: {source}"

        print(f"✅ 配置来源检测测试通过")
        print(f"   检测到配置来源: {source}")

    def test_all_configs_summary(self):
        """测试所有配置的摘要功能"""
        # 设置一些测试配置
        os.environ["GLOBAL_OPENAI_API_KEY"] = "global-test-key"
        os.environ["SCOUT_OPENAI_API_KEY"] = "scout-test-key"
        os.environ["PLANNER_OPENAI_API_KEY"] = "planner-test-key"
        os.environ["OPENAI_API_KEY"] = "legacy-test-key"

        print("🧪 开始配置摘要测试...")

        # 调用摘要功能（会输出详细信息）
        ConfigManager.print_config_summary()

        # 验证配置数量
        all_configs = ConfigManager.get_all_configs()
        assert len(all_configs) == 4, "应该有 4 个 Agent 配置"

        # 验证错误检测
        errors = ConfigManager.validate_all_configs()
        # 应该有一些配置使用默认值，导致验证错误
        assert len(errors) > 0, "应该有配置验证错误（使用了默认值）"

        print(f"✅ 配置摘要测试完成")
        print(f"   配置数量: {len(all_configs)}")
        print(f"   验证错误数: {len(errors)}")

    def test_error_handling(self):
        """测试错误处理"""
        # 测试缺少 API key 的情况
        os.environ["SCOUT_OPENAI_API_KEY"] = ""  # 设置为空

        with pytest.raises(ValueError, match="SCOUT Agent 缺少有效的 API_KEY"):
            get_scout_config()

        print(f"✅ 错误处理测试通过")


def test_global_vs_agent_priority():
    """测试全局 vs Agent 配置优先级"""
    test = TestConfigManager()
    test.setup_method()
    test.test_global_config_priority()


def test_agent_specific_config():
    """测试 Agent 特定配置"""
    test = TestConfigManager()
    test.setup_method()
    test.test_agent_specific_config_priority()


def test_backward_compatibility():
    """测试向后兼容性"""
    test = TestConfigManager()
    test.setup_method()
    test.test_backward_compatibility()


def test_default_fallback():
    """测试默认配置回退"""
    test = TestConfigManager()
    test.setup_method()
    test.test_default_fallback()


def test_config_validation():
    """测试配置验证"""
    test = TestConfigManager()
    test.setup_method()
    test.test_config_validation()


def test_config_source_detection():
    """测试配置来源检测"""
    test = TestConfigManager()
    test.setup_method()
    test.test_config_source_detection()


def test_all_configs_summary():
    """测试所有配置摘要"""
    test = TestConfigManager()
    test.setup_method()
    test.test_all_configs_summary()


def test_error_handling():
    """测试错误处理"""
    test = TestConfigManager()
    test.setup_method()
    test.test_error_handling()


if __name__ == "__main__":
    # 手动运行测试的主函数
    print("🧪 开始配置管理器测试...")

    tests = [
        test_global_vs_agent_priority,
        test_agent_specific_config,
        test_backward_compatibility,
        test_default_fallback,
        test_config_validation,
        test_config_source_detection,
        test_all_configs_summary,
        test_error_handling
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
            print(f"✅ {test_func.__name__} 通过")
        except Exception as e:
            failed += 1
            print(f"❌ {test_func.__name__} 失败: {e}")

    print(f"\n🎉 配置管理器测试完成！")
    print(f"   通过: {passed} 个测试")
    print(f"   失败: {failed} 个测试")
    print(f"   成功率: {passed/(passed+failed)*100:.1f}%")