"""聊天对话 API，提供方剂分析对话和数据库持久化历史。"""
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import DatabaseError, LLMServiceError
from app.core.logger import llm_logger
from app.models.database_models import Conversation
from app.models.schemas import APIResponse, ChatRequest, ChatResponse
from app.services.llm_service import llm_service
from app.services.tcm_context_service import build_local_context

router = APIRouter()


SYSTEM_PROMPT = """你是“知源”面向普通公众的中医方剂通识科普助手。

你的任务是把古方和中药讲清楚，帮助没有中医基础的人理解方源、组成、传统功用、
主治语境和配伍思路，尤其是君臣佐使所表达的主次分工。你不是医生，也不进行线上诊疗。

回答要求：
1. 使用准确、通俗、克制的中文，先解释是什么，再解释为什么这样配伍。
2. 具体方剂或中药的名称、出处、组成、功用、主治、性味归经，优先依据系统提供的本地资料。
3. 本地资料没有覆盖的事实不要编造；无法确认时直接说明“当前资料未收录/需要核对原始文献”。
4. 剂量只能作为古籍或平台资料说明，必须指出古籍剂量、教学剂量和个人用药剂量不能直接等同。
5. 不诊断疾病，不判断某位用户是否适合某方，不提供个人处方、剂量、加减、炮制、煎服或停药方案。
6. 当用户描述自身症状、询问“我能不能吃”或要求开方时，明确说明无法据此判断个体适用性，
   并建议就医或咨询中医师、药师；急症、孕期、儿童、肝肾功能异常和正在服药者尤其要谨慎。
7. 不把传统“主治”直接等同于某个现代疾病诊断，也不作疗效保证。
8. 不虚构现代研究、指南、古籍原文或参考文献。

表达格式：
- 用 **短标题** 分段，使用短段落、短横线列表或数字列表。
- 不使用表格、代码块、HTML、复杂公式或过多层级标题。
- 每次聚焦用户最关心的两到四个问题，通常控制在约 800 至 1200 个汉字。
- 涉及具体方剂时，尽量按“方源与类别、组成、传统功用与主治语境、配伍观察、安全边界”讲。
- 结尾用一句话提醒：本回答用于方剂通识学习，不能替代面诊和专业用药指导。"""


def _message_dict(message: Conversation) -> dict:
    return {
        "id": message.id,
        "role": message.role,
        "content": message.content,
        "created_at": message.created_at.isoformat() if message.created_at else None,
    }


@router.post("/analyze", response_model=APIResponse, summary="方剂通识科普问答")
async def chat_analyze(request: ChatRequest, db: Session = Depends(get_db)):
    llm_logger.info(
        "收到聊天请求，sessionId: %s, 消息长度: %s",
        request.sessionId,
        len(request.message),
    )
    recent_history = request.history[-12:]
    context_question = "\n".join(
        [item.content for item in recent_history if item.role == "user"][-6:]
        + [request.message]
    )
    local_context = build_local_context(context_question)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if local_context:
        messages.append({"role": "system", "content": local_context})
    messages.extend(
        {"role": item.role, "content": item.content[:4000]}
        for item in recent_history
    )
    messages.append({"role": "user", "content": request.message})

    try:
        response_text = await llm_service._call_llm(
            messages=messages,
            temperature=0.4,
            max_tokens=1800,
        )
    except LLMServiceError:
        raise
    except Exception as exc:
        llm_logger.error("聊天模型调用失败: %s", exc)
        raise LLMServiceError(f"AI服务调用失败: {exc}") from exc

    timestamp = datetime.now()
    try:
        db.add_all(
            [
                Conversation(
                    session_id=request.sessionId,
                    role="user",
                    content=request.message,
                    created_at=timestamp,
                ),
                Conversation(
                    session_id=request.sessionId,
                    role="assistant",
                    content=response_text,
                    created_at=datetime.now(),
                ),
            ]
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        llm_logger.error("聊天记录持久化失败: %s", exc)
        raise DatabaseError(f"聊天记录保存失败: {exc}") from exc

    result = ChatResponse(
        response=response_text,
        sessionId=request.sessionId,
        timestamp=timestamp.isoformat(),
        persisted=True,
    )
    return APIResponse(message="分析完成", data=result)


@router.get("/history/{session_id}", response_model=APIResponse, summary="获取对话历史")
async def get_chat_history(session_id: str, db: Session = Depends(get_db)):
    try:
        rows: List[Conversation] = (
            db.query(Conversation)
            .filter(Conversation.session_id == session_id)
            .order_by(Conversation.created_at.asc(), Conversation.id.asc())
            .all()
        )
        return APIResponse(
            message="获取成功",
            data={
                "sessionId": session_id,
                "messages": [_message_dict(item) for item in rows],
            },
        )
    except Exception as exc:
        raise DatabaseError(f"获取对话历史失败: {exc}") from exc


@router.delete("/history/{session_id}", response_model=APIResponse, summary="清空对话历史")
async def clear_chat_history(session_id: str, db: Session = Depends(get_db)):
    try:
        deleted = (
            db.query(Conversation)
            .filter(Conversation.session_id == session_id)
            .delete(synchronize_session=False)
        )
        db.commit()
        return APIResponse(
            message="对话历史已清空",
            data={"sessionId": session_id, "deleted": deleted},
        )
    except Exception as exc:
        db.rollback()
        raise DatabaseError(f"清空对话历史失败: {exc}") from exc
