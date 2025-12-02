"""Core interfaces and data structures for the Table2Image Multi-Agent System."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path


@dataclass
class VisualSummary:
    """视觉摘要：描述表格的结构信息，不包含具体数据值"""
    table_title: str
    headers: List[str]
    row_structure: List[str]  # 行的结构描述，如 "部门名", "季度数据"等
    column_structure: List[str]  # 列的结构描述，如 "部门", "Q1", "Q2", "Q3", "Q4"
    merge_cells: List[Tuple[int, int, int, int]]  # (row_start, col_start, row_end, col_end)
    layout_description: str  # 表格布局的整体描述

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，便于传输"""
        return {
            "table_title": self.table_title,
            "headers": self.headers,
            "row_structure": self.row_structure,
            "column_structure": self.column_structure,
            "merge_cells": self.merge_cells,
            "layout_description": self.layout_description
        }


@dataclass
class LocatingInstructions:
    """定位指令：具体的数据定位信息"""
    target_rows: List[str]  # 目标行描述，如 ["研发部", "市场部"]
    target_columns: List[str]  # 目标列描述，如 ["2023年Q1", "2023年Q2"]
    coordinate_hints: Dict[str, str]  # 坐标提示，如 {"row_index": "2-3", "col_index": "1-2"}
    extraction_type: str  # 提取类型： "single_cell", "row_data", "column_data", "region_data"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "target_rows": self.target_rows,
            "target_columns": self.target_columns,
            "coordinate_hints": self.coordinate_hints,
            "extraction_type": self.extraction_type
        }


@dataclass
class DataPacket:
    """数据包：包含提取的数据和视觉确认信息"""
    raw_image_path: str  # 原始图像路径
    cropped_region: Optional[Tuple[int, int, int, int]]  # 裁剪区域 (x1, y1, x2, y2)
    rough_markdown: str  # 粗略的 Markdown OCR 文本
    structure_info: Dict[str, Any]  # 结构信息
    extraction_metadata: Dict[str, Any]  # 提取的元数据

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "raw_image_path": self.raw_image_path,
            "cropped_region": self.cropped_region,
            "rough_markdown": self.rough_markdown,
            "structure_info": self.structure_info,
            "extraction_metadata": self.extraction_metadata
        }


@dataclass
class Answer:
    """最终答案：包含结果和执行信息"""
    result: str  # 最终答案
    calculation_method: str  # 计算方法
    confidence: float  # 置信度
    execution_trace: List[str]  # 执行轨迹
    error_message: Optional[str] = None  # 错误信息（如果有）

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "result": self.result,
            "calculation_method": self.calculation_method,
            "confidence": self.confidence,
            "execution_trace": self.execution_trace,
            "error_message": self.error_message
        }


class ScoutAgent(ABC):
    """视觉侦察兵接口：负责全局扫描表格结构"""

    @abstractmethod
    def scan(self, image_path: str) -> VisualSummary:
        """
        扫描图像，生成视觉摘要

        Args:
            image_path: 图像文件路径

        Returns:
            VisualSummary: 表格结构的视觉摘要
        """
        pass


class PlannerAgent(ABC):
    """指挥官接口：负责逻辑分解和生成定位指令"""

    @abstractmethod
    def plan(self, question: str, summary: VisualSummary) -> LocatingInstructions:
        """
        基于问题和视觉摘要生成定位指令

        Args:
            question: 用户问题
            summary: 视觉摘要

        Returns:
            LocatingInstructions: 具体的定位指令
        """
        pass


class SniperAgent(ABC):
    """视觉狙击手接口：负责精确数据提取"""

    @abstractmethod
    def extract(self, image_path: str, instructions: LocatingInstructions) -> DataPacket:
        """
        根据定位指令精确提取数据

        Args:
            image_path: 原始图像路径
            instructions: 定位指令

        Returns:
            DataPacket: 包含提取数据的包
        """
        pass


class CoderAgent(ABC):
    """执行者接口：负责逻辑执行和计算"""

    @abstractmethod
    def execute(self, packet: DataPacket, question: str) -> Answer:
        """
        基于数据包和问题执行计算

        Args:
            packet: 数据包
            question: 原始问题

        Returns:
            Answer: 最终答案
        """
        pass