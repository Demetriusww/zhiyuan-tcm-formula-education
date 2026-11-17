"""
大模型服务模块
为方剂通识问答和既有知识分析接口提供 DeepSeek 调用能力
"""
import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.exceptions import LLMServiceError
from app.core.logger import llm_logger
from app.models.schemas import (
    CompatibilityAnalysis,
    OptimizationSuggestion,
    EfficacyPrediction,
    PrescriptionHerb
)


class LLMService:
    """大模型服务类"""
    
    def __init__(self):
        self.api_key = settings.LLM_API_KEY
        self.api_base = settings.LLM_API_BASE.rstrip("/")
        self.model = settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS
        self.timeout = settings.LLM_TIMEOUT
        
        llm_logger.info(f"LLM服务初始化完成，模型: {self.model}")
    
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=3, max=8),
        reraise=True
    )
    async def _call_llm(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        调用 DeepSeek OpenAI 兼容聊天接口
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
        
        Returns:
            模型响应文本
        """
        if not self.api_key:
            raise LLMServiceError("LLM API密钥未配置")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens or self.max_tokens
        }
        
        try:
            llm_logger.debug(f"调用 DeepSeek API，模型: {self.model}, 消息数: {len(messages)}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                
                # DeepSeek 返回格式与 OpenAI 兼容
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"]
                elif "output" in result and "text" in result["output"]:
                    # 兼容旧版格式
                    content = result["output"]["text"]
                else:
                    raise LLMServiceError(f"API返回格式异常: {result}")
                
                llm_logger.debug(f"DeepSeek API 调用成功，响应长度: {len(content)}")
                return content
                
        except httpx.TimeoutException:
            llm_logger.error("DeepSeek API 调用超时")
            raise LLMServiceError("AI服务响应超时，请稍后重试")
        except httpx.HTTPStatusError as e:
            error_text = e.response.text
            llm_logger.error(f"DeepSeek API 调用失败: {e.response.status_code} - {error_text}")
            raise LLMServiceError(f"AI服务调用失败: {e.response.status_code}, {error_text}")
        except Exception as e:
            llm_logger.error(f"DeepSeek API 调用异常: {str(e)}")
            raise LLMServiceError(f"AI服务调用异常: {str(e)}")
    
    async def analyze_compatibility(
        self,
        prescription_name: str,
        herbs: List[PrescriptionHerb]
    ) -> CompatibilityAnalysis:
        """
        分析方剂配伍关系
        
        Args:
            prescription_name: 方剂名称
            herbs: 组成药物列表
        
        Returns:
            配伍分析结果
        """
        herbs_str = "\n".join([
            f"- {h.name}: {h.dosage}" + (f" ({h.preparation})" if h.preparation else "")
            for h in herbs
        ])
        
        prompt = f"""请分析以下中医方剂的配伍关系：

方剂名称：{prescription_name}

组成药物：
{herbs_str}

请从中医方剂学角度分析：
1. 君、臣、佐、使的配伍结构
2. 药物之间的协同作用
3. 潜在的药物冲突或禁忌
4. 综合评分（0-100分）

请以JSON格式返回分析结果，格式如下：
{{
    "overall_score": 85,
    "monarch_herb": {{"name": "药物名", "dosage": "剂量", "reason": "为君药的理由"}},
    "minister_herbs": [...],
    "assistant_herbs": [...],
    "messenger_herbs": [...],
    "compatibility_analysis": "配伍分析文字",
    "synergy_effects": ["协同作用1", "协同作用2"],
    "potential_conflicts": ["潜在冲突1"]  // 如无则返回空数组
}}"""
        
        messages = [
            {"role": "system", "content": "你是一位资深的中医方剂学专家，精通中医配伍理论。请基于中医经典理论进行分析。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = await self._call_llm(messages, temperature=0.3)
            
            # 解析JSON响应
            # 处理可能的Markdown代码块
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            result = json.loads(response.strip())
            
            # 构建响应对象
            return CompatibilityAnalysis(
                prescription_name=prescription_name,
                overall_score=result.get("overall_score", 0),
                monarch_herb=result.get("monarch_herb"),
                minister_herbs=result.get("minister_herbs", []),
                assistant_herbs=result.get("assistant_herbs", []),
                messenger_herbs=result.get("messenger_herbs", []),
                compatibility_analysis=result.get("compatibility_analysis", ""),
                synergy_effects=result.get("synergy_effects", []),
                potential_conflicts=result.get("potential_conflicts", [])
            )
            
        except json.JSONDecodeError as e:
            llm_logger.error(f"解析LLM响应失败: {str(e)}")
            raise LLMServiceError("AI分析结果解析失败")
        except Exception as e:
            llm_logger.error(f"配伍分析失败: {str(e)}")
            raise LLMServiceError(f"配伍分析失败: {str(e)}")
    
    async def generate_optimization_suggestions(
        self,
        prescription_name: str,
        herbs: List[PrescriptionHerb],
        target_symptoms: Optional[List[str]] = None
    ) -> List[OptimizationSuggestion]:
        """
        生成方剂优化建议
        
        Args:
            prescription_name: 方剂名称
            herbs: 组成药物列表
            target_symptoms: 目标症状
        
        Returns:
            优化建议列表
        """
        herbs_str = "\n".join([f"- {h.name}: {h.dosage}" for h in herbs])
        symptoms_str = ", ".join(target_symptoms) if target_symptoms else "未指定"
        
        prompt = f"""请为以下中医方剂提供优化建议：

方剂名称：{prescription_name}

组成药物：
{herbs_str}

目标症状：{symptoms_str}

请从以下角度提供优化建议：
1. 药味精简（是否可以减少药味而不影响疗效）
2. 药味替代（是否有更好的替代药物）
3. 剂量调整（各药剂量是否需要调整）
4. 药物添加（是否需要添加其他药物）

请以JSON格式返回，格式如下：
{{
    "suggestions": [
        {{
            "type": "simplify/substitute/dosage/add/remove",
            "title": "建议标题",
            "description": "具体建议描述",
            "reason": "建议理由",
            "confidence": 0.85
        }}
    ]
}}"""
        
        messages = [
            {"role": "system", "content": "你是一位资深的中医临床专家，擅长方剂优化和个体化治疗。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = await self._call_llm(messages, temperature=0.4)
            
            # 解析JSON
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            result = json.loads(response.strip())
            suggestions_data = result.get("suggestions", [])
            
            return [
                OptimizationSuggestion(**suggestion)
                for suggestion in suggestions_data
            ]
            
        except Exception as e:
            llm_logger.error(f"生成优化建议失败: {str(e)}")
            raise LLMServiceError(f"生成优化建议失败: {str(e)}")
    
    async def predict_efficacy(
        self,
        prescription_name: str,
        herbs: List[PrescriptionHerb],
        target_symptoms: List[str]
    ) -> EfficacyPrediction:
        """
        预测方剂疗效
        
        Args:
            prescription_name: 方剂名称
            herbs: 组成药物列表
            target_symptoms: 目标症状
        
        Returns:
            疗效预测结果
        """
        herbs_str = "\n".join([f"- {h.name}: {h.dosage}" for h in herbs])
        symptoms_str = ", ".join(target_symptoms)
        
        prompt = f"""请预测以下中医方剂对目标症状的疗效：

方剂名称：{prescription_name}

组成药物：
{herbs_str}

目标症状：{symptoms_str}

请分析：
1. 预测疗效评分（0-100分）
2. 作用机制
3. 支持证据
4. 禁忌症和注意事项

请以JSON格式返回：
{{
    "predicted_efficacy": 85,
    "confidence_level": 0.82,
    "mechanism_analysis": "作用机制分析...",
    "supporting_evidence": ["证据1", "证据2"],
    "contraindications": ["禁忌1", "禁忌2"]  // 如无则返回空数组
}}"""
        
        messages = [
            {"role": "system", "content": "你是一位资深的中医临床研究员，擅长循证医学和疗效评估。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = await self._call_llm(messages, temperature=0.3)
            
            # 解析JSON
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            result = json.loads(response.strip())
            
            return EfficacyPrediction(
                prescription_id=0,  # 由调用方设置
                target_symptoms=target_symptoms,
                predicted_efficacy=result.get("predicted_efficacy", 0),
                confidence_level=result.get("confidence_level", 0),
                mechanism_analysis=result.get("mechanism_analysis", ""),
                supporting_evidence=result.get("supporting_evidence", []),
                contraindications=result.get("contraindications", [])
            )
            
        except Exception as e:
            llm_logger.error(f"疗效预测失败: {str(e)}")
            raise LLMServiceError(f"疗效预测失败: {str(e)}")
    
    async def recommend_prescriptions(
        self,
        symptoms: str,
        constraints: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        根据症状推荐方剂
        
        Args:
            symptoms: 症状描述
            constraints: 约束条件
        
        Returns:
            推荐方剂列表
        """
        constraints_str = json.dumps(constraints, ensure_ascii=False) if constraints else "无特殊约束"
        
        prompt = f"""根据以下症状推荐合适的中医方剂：

症状描述：{symptoms}

约束条件：{constraints_str}

请推荐3-5个最合适的经典方剂，包含：
1. 方剂名称
2. 匹配度评分（0-100）
3. 推荐理由
4. 主要药物组成

请以JSON格式返回：
{{
    "recommendations": [
        {{
            "name": "方剂名",
            "match_score": 92,
            "reason": "推荐理由...",
            "herbs": ["药物1", "药物2", "药物3"]
        }}
    ]
}}"""
        
        messages = [
            {"role": "system", "content": "你是一位资深的中医临床专家，擅长辨证论治和方剂选用。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = await self._call_llm(messages, temperature=0.4)
            
            # 解析JSON
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            result = json.loads(response.strip())
            return result.get("recommendations", [])
            
        except Exception as e:
            llm_logger.error(f"方剂推荐失败: {str(e)}")
            raise LLMServiceError(f"方剂推荐失败: {str(e)}")


# 全局LLM服务实例
llm_service = LLMService()
