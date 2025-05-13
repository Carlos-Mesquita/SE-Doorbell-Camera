import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from .message_type import MessageType

class Message(BaseModel):
    msg_type: MessageType
    payload: Optional[Dict[str, Any]] = None
    msg_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    reply_to: Optional[str] = None

    @classmethod
    def create_response(
            cls,
            original_msg: 'Message',
            msg_type: MessageType,
            payload: Optional[Dict[str, Any]] = None
    ) -> 'Message':
        return cls(
            msg_type=msg_type,
            payload=payload,
            reply_to=original_msg.msg_id
        )
