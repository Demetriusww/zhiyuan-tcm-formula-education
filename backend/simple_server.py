"""
简化版FastAPI服务器 - 仅用于聊天功能
"""
import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from datetime import datetime
import httpx

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(
    title="中医方剂配伍分析API",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 从配置文件读取API Key
try:
    from app.core.config import settings
    LLM_API_KEY = settings.LLM_API_KEY
    LLM_API_BASE = settings.LLM_API_BASE
    LLM_MODEL = settings.LLM_MODEL
    print(f"从配置文件读取API Key: {'已配置' if LLM_API_KEY else '未配置'}")
except Exception as e:
    print(f"读取配置文件失败: {e}")
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    LLM_API_BASE = os.getenv("LLM_API_BASE", "https://api.deepseek.com")
    LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

# 系统提示词
SYSTEM_PROMPT = """你是“知源”面向普通公众的中医方剂通识科普助手。
请把方源、组成、传统功用、主治语境和君臣佐使的配伍思路讲清楚，语言通俗但不能夸大。

安全边界：
- 不诊断疾病，不判断某位用户是否适合某方。
- 不提供个人处方、剂量、加减、炮制、煎服或停药方案。
- 遇到个人症状、“我能不能吃”等内容，说明无法据此判断个体适用性，并建议咨询中医师或药师。
- 传统主治不能直接等同于现代疾病诊断；不编造古籍原文、研究或参考文献。
- 剂量只能作为古籍或资料说明，不能转化为个人用药建议。

格式要求：
- 使用 **短标题**、短段落、短横线列表或数字列表。
- 不使用表格、代码块或 HTML。
- 通常控制在约 800 至 1200 个汉字，结尾说明仅供方剂通识学习。"""


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    sessionId: str
    history: List[ChatMessage]


class ChatResponse(BaseModel):
    response: str
    sessionId: str
    timestamp: str
    persisted: bool = False


@app.post("/api/chat/analyze", response_model=ChatResponse)
async def chat_analyze(request: ChatRequest):
    """方剂通识科普问答接口"""
    try:
        print(f"收到请求: {request.sessionId}, 消息: {request.message[:50]}...")

        try:
            from app.services.tcm_context_service import build_local_context
            context_question = "\n".join(
                [item.content for item in request.history[-6:] if item.role == "user"]
                + [request.message]
            )
            local_context = build_local_context(context_question)
        except Exception as exc:
            print(f"读取本地方药资料失败: {exc}")
            local_context = ""

        # 构建消息列表
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if local_context:
            messages.append({"role": "system", "content": local_context})
        
        # 添加历史对话
        recent_history = request.history[-12:] if len(request.history) > 12 else request.history
        for msg in recent_history:
            if msg.content:  # 跳过空消息
                messages.append({"role": msg.role, "content": msg.content[:4000]})
        
        # 添加当前用户消息
        messages.append({"role": "user", "content": request.message})
        
        # 调用 DeepSeek API
        if not LLM_API_KEY:
            raise HTTPException(status_code=503, detail="API密钥未配置")
        
        headers = {
            "Authorization": f"Bearer {LLM_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": LLM_MODEL,
            "messages": messages,
            "temperature": 0.4,
            "max_tokens": 1800
        }
        
        print(f"调用 DeepSeek API，模型: {LLM_MODEL}")
        
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(
                f"{LLM_API_BASE.rstrip('/')}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            print(f"API调用成功，响应长度: {len(content)}")
            
            return ChatResponse(
                response=content,
                sessionId=request.sessionId,
                timestamp=datetime.now().isoformat()
            )
            
    except httpx.HTTPStatusError as e:
        error_msg = f"API调用失败: {e.response.status_code} - {e.response.text}"
        print(error_msg)
        raise HTTPException(status_code=503, detail=error_msg)
    except Exception as e:
        error_msg = f"服务异常: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "api_key_configured": bool(LLM_API_KEY),
        "model": LLM_MODEL
    }


if __name__ == "__main__":
    import uvicorn
    print(f"启动服务器...")
    print(f"API Key: {'已配置' if LLM_API_KEY else '未配置'}")
    print(f"模型: {LLM_MODEL}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
