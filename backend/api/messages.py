"""消息相关API"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from backend.core.database import Message, get_db


router = APIRouter()


class MessageResponse(BaseModel):
    """消息响应模型"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    platform: str
    sender_name: Optional[str] = None
    sender_title: Optional[str] = None
    company: Optional[str] = None
    content: str
    job_title: Optional[str] = None
    is_read: bool
    is_replied: bool
    suggested_reply: Optional[str] = None
    received_at: Optional[str] = None


class MessageListResponse(BaseModel):
    """消息列表响应"""
    total: int
    unread: int
    items: List[MessageResponse]


class ReplyRequest(BaseModel):
    """回复请求"""
    content: str


@router.get("", response_model=MessageListResponse)
async def list_messages(
    unread_only: bool = Query(False, description="仅显示未读"),
    platform: Optional[str] = Query(None, description="按平台过滤"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """获取消息列表"""
    query = db.query(Message)

    if unread_only:
        query = query.filter(Message.is_read == False)

    if platform:
        query = query.filter(Message.platform == platform)

    total = query.count()
    unread = db.query(Message).filter(Message.is_read == False).count()

    items = query.order_by(Message.received_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return MessageListResponse(
        total=total,
        unread=unread,
        items=[
            MessageResponse(
                id=item.id,
                platform=item.platform,
                sender_name=item.sender_name,
                sender_title=item.sender_title,
                company=item.company,
                content=item.content,
                job_title=item.job_title,
                is_read=item.is_read,
                is_replied=item.is_replied,
                suggested_reply=item.suggested_reply,
                received_at=item.received_at.isoformat() if item.received_at else None,
            )
            for item in items
        ],
    )


@router.post("/{message_id}/read")
async def mark_as_read(
    message_id: int,
    db: Session = Depends(get_db),
):
    """标记消息为已读"""
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    message.is_read = True
    db.commit()

    return {"message": "Marked as read"}


@router.post("/{message_id}/reply")
async def reply_message(
    message_id: int,
    request: ReplyRequest,
    db: Session = Depends(get_db),
):
    """回复消息"""
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # TODO: 实际发送回复
    message.is_replied = True
    message.reply_content = request.content
    db.commit()

    return {"message": "Reply sent"}


@router.post("/{message_id}/auto-reply")
async def auto_reply(
    message_id: int,
    db: Session = Depends(get_db),
):
    """使用AI自动回复"""
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    if not message.suggested_reply:
        raise HTTPException(status_code=400, detail="No suggested reply available")

    # TODO: 实际发送回复
    message.is_replied = True
    message.reply_content = message.suggested_reply
    db.commit()

    return {"message": "Auto reply sent", "content": message.suggested_reply}


@router.post("/check-new")
async def check_new_messages(
    db: Session = Depends(get_db),
):
    """检查新消息"""
    from backend.services import get_orchestrator
    from backend.adapters import Platform

    try:
        orchestrator = await get_orchestrator(use_ai=False)
        messages = await orchestrator.check_messages([Platform.BOSS, Platform.LIEPIN])

        return {
            "new_count": len(messages),
            "messages": [
                {
                    "sender": m.sender_name,
                    "company": m.company,
                    "preview": m.content[:50] + "..." if len(m.content) > 50 else m.content,
                }
                for m in messages
            ],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))