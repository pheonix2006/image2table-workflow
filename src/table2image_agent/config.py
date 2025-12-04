"""配置管理器：支持多 Agent 的配置隔离和优先级管理。

实现 Agent 级别的配置管理，支持：
1. 全局默认配置
2. Agent 特定配置
3. 向后兼容性
4. 配置优先级逻辑
"""

import os
from enum import Enum
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# 自动加载环境变量
load_dotenv()


class AgentType(Enum):
    """Agent 类型枚举"""
    SCOUT = "SCOUT"
    PLANNER = "PLANNER"
    SNIPER = "SNIPER"
    CODER = "CODER"


@dataclass
class LLMConfig:
    """LLM 配置数据类"""
    api_key: str
    base_url: str
    model_name: str
    agent_type: AgentType

    def __post_init__(self):
        """配置验证"""
        if not self.api_key:
            raise ValueError(f"{self.agent_type.value} Agent 缺少 API_KEY")
        if not self.base_url:
            raise ValueError(f"{self.agent_type.value} Agent 缺少 BASE_URL")
        if not self.model_name:
            raise ValueError(f"{self.agent_type.value} Agent 缺少 MODEL_NAME")


class ConfigManager:
    """配置管理器：负责读取和管理 Agent 配置"""

    # 配置优先级顺序：Agent Specific > Global > Legacy > Default
    CONFIG_PREFIXES = [
        lambda agent_type: f"{agent_type.value}_OPENAI_" if hasattr(agent_type, 'value') else f"{agent_type}_OPENAI_",
        lambda agentType: "GLOBAL_OPENAI_",
        lambda agentType: "OPENAI_",  # 向后兼容
    ]

    # 默认配置值
    DEFAULT_CONFIG = {
        "api_key": "sk-default-key",
        "base_url": "https://api.openai.com/v1",
        "model_name": "gpt-4o"
    }

    @classmethod
    def _get_env_var(cls, prefix: str, suffix: str) -> Optional[str]:
        """
        获取环境变量，支持多种命名风格

        Args:
            prefix: 前缀，如 "SCOUT_OPENAI_"
            suffix: 后缀，如 "API_KEY"

        Returns:
            Optional[str]: 环境变量值
        """
        # 尝试多种命名组合
        variations = [
            f"{prefix}{suffix}",           # SCOUT_OPENAI_API_KEY
            f"{prefix}{suffix.lower()}", # SCOUT_OPENAI_api_key (小写）
        ]

        for var_name in variations:
            value = os.getenv(var_name)
            if value is not None:
                return value

        return None

    @classmethod
    def _get_agent_config_by_priority(cls, agent_type: AgentType) -> LLMConfig:
        """
        按优先级获取 Agent 配置

        Args:
            agent_type: Agent 类型

        Returns:
            LLMConfig: Agent 配置
        """
        suffix_map = {
            "API_KEY": "api_key",
            "BASE_URL": "base_url",
            "MODEL_NAME": "model_name",
            "MODEL": "model_name"  # 支持 MODEL 命名
        }

        # 按优先级顺序查找配置
        for prefix_func in cls.CONFIG_PREFIXES:
            prefix = prefix_func(agent_type)

            config_values = {}
            for suffix, field_name in suffix_map.items():
                value = cls._get_env_var(prefix, suffix)
                if value is not None:
                    config_values[field_name] = value

            # 如果找到所有必需的配置值，则使用该前缀
            required_fields = ["api_key", "base_url", "model_name"]
            if all(field in config_values for field in required_fields):
                return LLMConfig(
                    agent_type=agent_type,
                    **config_values
                )

        # 如果没有找到任何配置，使用默认值
        return LLMConfig(
            agent_type=agent_type,
            **cls.DEFAULT_CONFIG
        )

    @classmethod
    def from_agent(cls, agent_type: AgentType) -> LLMConfig:
        """
        为指定 Agent 创建配置

        Args:
            agent_type: Agent 类型

        Returns:
            LLMConfig: Agent 配置
        """
        config = cls._get_agent_config_by_priority(agent_type)

        print(f"🔧 配置加载完成 [{agent_type.value}]:")
        print(f"   API Key: {config.api_key[:10]}...")
        print(f"   Base URL: {config.base_url}")
        print(f"   Model: {config.model_name}")

        # 显示配置来源
        source = cls._detect_config_source(agent_type)
        print(f"   配置来源: {source}")

        return config

    @classmethod
    def _detect_config_source(cls, agent_type) -> str:
        """
        检测配置来源（用于调试）

        Args:
            agent_type: Agent 类型（可以是枚举或字符串）

        Returns:
            str: 配置来源描述
        """
        # 处理 agent_type 为枚举或字符串的情况
        if hasattr(agent_type, 'value'):
            agent_str = agent_type.value
        else:
            agent_str = str(agent_type)

        agent_prefix = f"{agent_str}_OPENAI_"
        if any(os.getenv(f"{agent_prefix}{suffix}") is not None for suffix in ["API_KEY", "BASE_URL", "MODEL_NAME", "MODEL"]):
            return "Agent Specific"

        global_prefix = "GLOBAL_OPENAI_"
        if any(os.getenv(f"{global_prefix}{suffix}") is not None for suffix in ["API_KEY", "BASE_URL", "MODEL_NAME", "MODEL"]):
            return "Global Default"

        legacy_prefix = "OPENAI_"
        if any(os.getenv(f"{legacy_prefix}{suffix}") is not None for suffix in ["API_KEY", "BASE_URL", "MODEL_NAME", "MODEL"]):
            return "Legacy (OPENAI_*)"

        return "Hardcoded Default"

    @classmethod
    def get_all_configs(cls) -> dict[AgentType, LLMConfig]:
        """
        获取所有 Agent 的配置

        Returns:
            dict[AgentType, LLMConfig]: 所有 Agent 配置的字典
        """
        configs = {}
        for agent_type in AgentType:
            configs[agent_type] = cls.from_agent(agent_type)
        return configs

    @classmethod
    def validate_all_configs(cls) -> list[str]:
        """
        验证所有配置的完整性

        Returns:
            list[str]: 验证错误列表
        """
        errors = []

        for agent_type in AgentType:
            try:
                config = cls.from_agent(agent_type)
                if not config.api_key or config.api_key == "sk-default-key":
                    errors.append(f"{agent_type.value}: 缺少有效的 API_KEY")
                if not config.base_url:
                    errors.append(f"{agent_type.value}: 缺少 BASE_URL")
                if not config.model_name:
                    errors.append(f"{agent_type.value}: 缺少 MODEL_NAME")
            except Exception as e:
                errors.append(f"{agent_type.value}: 配置加载失败 - {e}")

        return errors

    @classmethod
    def print_config_summary(cls):
        """
        打印所有配置的摘要
        """
        print("📋 配置系统摘要:")
        print("=" * 50)

        configs = cls.get_all_configs()
        for agent_type, config in configs.items():
            print(f"\n🤖 {agent_type.value} Agent:")
            print(f"   📍 配置来源: {cls._detect_config_source(agent_type)}")
            print(f"   🔑 API Key: {config.api_key[:10]}...")
            print(f"   🌐 Base URL: {config.base_url}")
            print(f"   🧠 Model: {config.model_name}")

        print("\n" + "=" * 50)

        # 验证配置
        errors = cls.validate_all_configs()
        if errors:
            print("\n⚠️  配置验证问题:")
            for error in errors:
                print(f"   ❌ {error}")
        else:
            print("\n✅ 所有配置验证通过！")


# 便捷函数
def get_scout_config() -> LLMConfig:
    """获取 Scout Agent 配置"""
    return ConfigManager.from_agent(AgentType.SCOUT)


def get_planner_config() -> LLMConfig:
    """获取 Planner Agent 配置"""
    return ConfigManager.from_agent(AgentType.PLANNER)


def get_sniper_config() -> LLMConfig:
    """获取 Sniper Agent 配置"""
    return ConfigManager.from_agent(AgentType.SNIPER)


def get_coder_config() -> LLMConfig:
    """获取 Coder Agent 配置"""
    return ConfigManager.from_agent(AgentType.CODER)


if __name__ == "__main__":
    # 测试配置管理器
    ConfigManager.print_config_summary()