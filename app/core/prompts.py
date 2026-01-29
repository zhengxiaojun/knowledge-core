"""
Prompt templates management.
Centralized prompt templates for LLM calls with version control.
"""
from typing import Dict
from datetime import datetime


class PromptTemplates:
    """Centralized prompt template management."""

    VERSION = "1.0.0"
    LAST_UPDATED = "2026-01-29"

    # Step 1: Requirement Intent Analysis
    INTENT_ANALYSIS = """
你是一名资深测试架构师，擅长分析需求并识别测试意图。

【任务】
分析以下需求文档，识别关键测试意图。
测试意图是高层次的测试目标，例如"验证核心功能"、"测试特定类型错误"、"检查性能"等。

对每个意图，提供简短描述并分类其范围（functional/exception/risk/boundary）。

【需求内容】
{requirement_content}

【输出格式】
JSON格式：
{{
  "intents": [
    {{"description": "意图描述", "scope": "functional|exception|risk|boundary"}}
  ]
}}
"""

    # Step 2: Test Point Generation
    TEST_POINT_GENERATION = """
你是一名资深测试架构师，擅长从需求中提取测试点。

【任务】
基于以下需求和历史测试知识，生成结构化的测试点列表。

【需求内容】
{requirement_content}

【历史测试知识】
{historical_knowledge}

【输出要求】
生成JSON数组，每个测试点包含：
- category: "正常" | "异常" | "边界"
- description: 测试点描述（简洁明确，不超过50字）

【注意事项】
1. 测试点应该是稳定的、可复用的
2. 不包含UI细节、接口字段等易变内容
3. 优先复用历史测试知识中的测试点

【输出格式】
{{
  "test_points": [
    {{"category": "正常", "description": "验证用户登录成功流程"}},
    {{"category": "异常", "description": "验证密码错误时的提示"}},
    {{"category": "边界", "description": "验证密码长度限制"}}
  ]
}}
"""

    # Step 3: Test Case Generation
    TEST_CASE_GENERATION = """
你是一名测试工程师，为测试点生成详细测试用例。

【测试点】
{test_point_description}

【需求背景】
{requirement_context}

【历史参考用例】
{reference_cases}

【输出要求】
生成完整的测试用例，包含：
- title: 用例标题
- precondition: 前置条件（可选）
- steps: 测试步骤（数组）
- expected: 预期结果

【注意事项】
1. 步骤要具体、可执行
2. 预期结果要明确、可验证
3. 考虑异常情况和边界条件

【输出格式】
{{
  "title": "测试用例标题",
  "precondition": "前置条件",
  "steps": ["步骤1", "步骤2", "步骤3"],
  "expected": "预期结果"
}}
"""

    # Knowledge Extraction from Requirements
    KNOWLEDGE_EXTRACTION = """
你是一名资深测试架构师，擅长从需求与缺陷中抽象稳定测试知识。

【角色】
识别并提取关键测试知识单元（测试点、测试场景、风险点）。

【任务】
从以下文本中提取测试知识：
1. 抽象稳定、可复用的测试点/场景/风险
2. 不包含UI、接口字段、实现细节
3. 每条必须可长期复用

【文本内容】
{text}

【输出格式】
{{
  "nodes": [
    {{"id": "temp-1", "type": "TestPoint|Scenario|Risk", "content": "内容描述", "confidence": 0.8}}
  ],
  "edges": [
    {{"source": "temp-1", "target": "temp-2", "relation": "CONTAINS|RELATES_TO"}}
  ]
}}
"""

    # Risk Point Extraction from Defect
    RISK_EXTRACTION = """
你是一名质量专家，擅长从缺陷中提取风险点。

【任务】
分析以下缺陷，提取可复用的风险点。

【缺陷信息】
标题: {defect_title}
现象: {phenomenon}
根因: {root_cause}

【输出要求】
生成风险点描述，要求：
1. 抽象、通用、可复用
2. 不包含具体的实现细节
3. 突出风险的本质

【输出格式】
{{
  "risk_point": "风险点描述",
  "severity": "high|medium|low",
  "mitigation": "建议的测试方法"
}}
"""

    @classmethod
    def get_intent_analysis_prompt(cls, requirement_content: str) -> str:
        """Get prompt for intent analysis."""
        return cls.INTENT_ANALYSIS.format(requirement_content=requirement_content)

    @classmethod
    def get_test_point_prompt(cls, requirement_content: str, historical_knowledge: str) -> str:
        """Get prompt for test point generation."""
        return cls.TEST_POINT_GENERATION.format(
            requirement_content=requirement_content,
            historical_knowledge=historical_knowledge
        )

    @classmethod
    def get_test_case_prompt(cls, test_point: str, requirement: str, references: str = "") -> str:
        """Get prompt for test case generation."""
        return cls.TEST_CASE_GENERATION.format(
            test_point_description=test_point,
            requirement_context=requirement,
            reference_cases=references or "无"
        )

    @classmethod
    def get_knowledge_extraction_prompt(cls, text: str) -> str:
        """Get prompt for knowledge extraction."""
        return cls.KNOWLEDGE_EXTRACTION.format(text=text)

    @classmethod
    def get_risk_extraction_prompt(cls, title: str, phenomenon: str, root_cause: str) -> str:
        """Get prompt for risk extraction."""
        return cls.RISK_EXTRACTION.format(
            defect_title=title,
            phenomenon=phenomenon or "未描述",
            root_cause=root_cause or "未分析"
        )

    @classmethod
    def get_version_info(cls) -> Dict[str, str]:
        """Get prompt version information."""
        return {
            "version": cls.VERSION,
            "last_updated": cls.LAST_UPDATED
        }
