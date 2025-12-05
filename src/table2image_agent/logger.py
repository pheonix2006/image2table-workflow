"""
结构化追踪系统 - 提供全链路日志记录功能

使用loguru记录每个Agent的完整交互细节，包括：
- Trace ID追踪
- 输入输出参数
- 执行时间
- 异常信息
"""

import json
import threading
import time
import uuid
from contextvars import ContextVar
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Optional

from loguru import logger

# 全局Trace ID上下文
trace_context: ContextVar[Optional[str]] = ContextVar('trace_context', default=None)


class TracingManager:
    """追踪管理器，负责配置日志和管理Trace ID"""

    def __init__(self):
        self._setup_logger()

    def _setup_logger(self):
        """配置loguru日志系统"""
        # 移除默认处理器
        logger.remove()

        # 确保logs目录存在
        Path("logs").mkdir(exist_ok=True)

        # Console Sink: 只输出到控制台
        logger.add(
            sink=self._console_only_sink,
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | 📊 {message}",
            colorize=True,
            catch=True
        )

        # File Sink: 只写入文件，不输出到控制台
        logger.add(
            sink=self._file_only_sink,
            level="DEBUG",
            format="{message}",
            catch=True
        )

    def _console_only_sink(self, message):
        """仅控制台输出处理器"""
        try:
            # 尝试解析JSON并友好显示
            log_data = json.loads(message)

            # 提取关键信息
            timestamp = log_data.get("timestamp", "")
            trace_id = log_data.get("trace_id", "")
            step_name = log_data.get("step_name", "")
            function_name = log_data.get("function_name", "")
            msg = log_data.get("message", "")

            # 构建控制台输出
            prefix = f"🔍 [{trace_id}]" if trace_id else "📊"
            if step_name and function_name:
                output = f"{prefix} {step_name}.{function_name}: {msg}"
            elif step_name:
                output = f"{prefix} {step_name}: {msg}"
            else:
                output = f"{prefix} {msg}"

            print(output)

        except json.JSONDecodeError:
            # 如果不是JSON，直接输出
            print(message, end="")

    def _file_only_sink(self, message):
        """仅文件输出处理器"""
        try:
            # 验证是否为有效JSON
            json.loads(message)
            # 如果是有效JSON，写入文件
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            log_file = f"logs/trace_{timestamp}.jsonl"
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(message + "\n")
        except json.JSONDecodeError:
            # 不是JSON，不写入文件
            pass

    
    def log_json(self, level: str, message: str, **kwargs):
        """记录JSON格式的日志"""
        trace_id = kwargs.get("trace_id", self.get_current_trace())

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "trace_id": trace_id,
            "message": message,
            **kwargs
        }

        # 输出到文件（JSONL格式）
        logger.info(json.dumps(log_entry, ensure_ascii=False))

        # 同时输出到控制台（简化格式）
        console_message = f"🔍 [{trace_id or 'N/A':8}] {message}"
        logger.info(console_message)

    def init_trace(self) -> str:
        """初始化新的追踪会话，返回Trace ID"""
        trace_id = str(uuid.uuid4())[:8]  # 使用短ID便于显示
        trace_context.set(trace_id)

        self.log_json(
            "INFO",
            "🚀 开始新的追踪会话",
            trace_id=trace_id,
            step="INIT"
        )

        return trace_id

    def get_current_trace(self) -> Optional[str]:
        """获取当前Trace ID"""
        return trace_context.get()

    def clear_trace(self):
        """清除当前Trace ID"""
        trace_id = self.get_current_trace()
        if trace_id:
            self.log_json(
                "INFO",
                "🏁 结束追踪会话",
                trace_id=trace_id,
                step="END"
            )
        trace_context.set(None)


# 全局追踪管理器实例
tracing = TracingManager()


def trace_step(step_name: str):
    """
    追踪装饰器，记录函数执行的完整过程

    Args:
        step_name: 步骤名称，用于日志标识
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 获取或创建Trace ID
            trace_id = tracing.get_current_trace()
            if not trace_id:
                trace_id = tracing.init_trace()

            # 准备输入数据
            inputs = {
                "args": _sanitize_data(args),
                "kwargs": _sanitize_data(kwargs)
            }

            tracing.log_json(
                "INFO",
                f"🔵 开始执行: {func.__name__}",
                trace_id=trace_id,
                step=step_name,
                function=func.__name__,
                inputs=inputs
            )

            start_time = time.time()

            try:
                # 执行函数
                result = func(*args, **kwargs)

                # 计算执行时间
                duration = time.time() - start_time

                # 记录成功结果
                tracing.log_json(
                    "INFO",
                    f"🟢 执行成功: {func.__name__} ({duration:.2f}s)",
                    trace_id=trace_id,
                    step=step_name,
                    function=func.__name__,
                    outputs=_sanitize_data(result),
                    duration=duration
                )

                return result

            except Exception as e:
                duration = time.time() - start_time

                # 记录错误信息
                tracing.log_json(
                    "ERROR",
                    f"🔴 执行失败: {func.__name__} ({duration:.2f}s) - {str(e)}",
                    trace_id=trace_id,
                    step=step_name,
                    function=func.__name__,
                    error=str(e),
                    error_type=type(e).__name__,
                    duration=duration
                )

                # 重新抛出异常
                raise

        return wrapper
    return decorator


def _sanitize_data(data: Any) -> Any:
    """
    清理敏感数据，防止日志爆炸

    Args:
        data: 需要清理的数据

    Returns:
        清理后的数据
    """
    try:
        # 处理基本类型
        if data is None:
            return None
        elif isinstance(data, (str, int, float, bool)):
            return data
        elif isinstance(data, bytes):
            # 处理bytes类型（如Base64编码的图片数据）
            if len(data) > 1000:
                return "<Base64_Image_Bytes_Truncated>"
            else:
                return f"<Base64_Bytes_Length_{len(data)}>"
        elif isinstance(data, (list, tuple)):
            return [_sanitize_data(item) for item in data]
        elif isinstance(data, dict):
            return {key: _sanitize_data(value) for key, value in data.items()}
        else:
            # 处理复杂对象 - 只处理已知安全的类型
            data_type = type(data).__name__

            # 处理已知的问题类型
            if data_type in ('RLock', 'Lock'):
                return "<Thread_Lock_Object>"
            elif data_type == 'mappingproxy':
                return dict(data)
            elif isinstance(data, ContextVar):
                return f"<ContextVar_Name_{data.name}>"
            elif hasattr(data, '__dict__') and not data_type.startswith('_'):
                # 对于自定义对象，尝试序列化其字典表示（跳过内部属性）
                return _sanitize_data({k: v for k, v in data.__dict__.items() if not k.startswith('_')})
            else:
                # 其他类型返回类型信息
                return f"<Object_Type_{data_type}>"

    except Exception as e:
        # 如果处理过程中出现异常，返回类型信息
        return f"<Error_Sanitizing_{type(data).__name__}:_{str(e)}>"


def log_custom(step: str, message: str, **kwargs):
    """
    记录自定义日志

    Args:
        step: 步骤名称
        message: 日志消息
        **kwargs: 额外的数据
    """
    trace_id = tracing.get_current_trace()
    if not trace_id:
        trace_id = tracing.init_trace()

    extra_data = {
        "trace_id": trace_id,
        "step": step,
        **_sanitize_data(kwargs)
    }

    tracing.log_json("INFO", message, **extra_data)