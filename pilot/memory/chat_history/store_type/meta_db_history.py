import json
import logging
from typing import List
from sqlalchemy import Column, Integer, String, Index, DateTime, func, Boolean, Text
from sqlalchemy import UniqueConstraint
from pilot.configs.config import Config
from pilot.memory.chat_history.base import BaseChatHistoryMemory
from pilot.scene.message import (
    OnceConversation,
    _conversation_to_dic,
)
from ..chat_history_db import ChatHistoryEntity, ChatHistoryDao

from pilot.memory.chat_history.base import MemoryStoreType

CFG = Config()
logger = logging.getLogger(__name__)


class DbHistoryMemory(BaseChatHistoryMemory):
    store_type: str = MemoryStoreType.DB.value

    def __init__(self, chat_session_id: str):
        self.chat_seesion_id = chat_session_id
        self.chat_history_dao = ChatHistoryDao()

    def messages(self) -> List[OnceConversation]:
        chat_history: ChatHistoryEntity = self.chat_history_dao.get_by_uid(
            self.chat_seesion_id
        )
        if chat_history:
            context = chat_history.messages
            if context:
                conversations: List[OnceConversation] = json.loads(context)
                return conversations
        return []

    def create(self, chat_mode, summary: str, user_name: str) -> None:
        try:
            chat_history: ChatHistoryEntity = ChatHistoryEntity()
            chat_history.chat_mode = chat_mode
            chat_history.summary = summary
            chat_history.user_name = user_name

            self.chat_history_dao.update(chat_history)
        except Exception as e:
            logger.error("init create conversation log error！" + str(e))

    def append(self, once_message: OnceConversation) -> None:
        logger.info("db history append:{}", once_message)
        chat_history: ChatHistoryEntity = self.chat_history_dao.get_by_uid(
            self.chat_seesion_id
        )
        conversations: List[OnceConversation] = []
        if chat_history:
            context = chat_history.messages
            if context:
                conversations = json.loads(context)
            else:
                chat_history.summary = once_message.get_user_conv().content
        else:
            chat_history: ChatHistoryEntity = ChatHistoryEntity()
            chat_history.conv_uid = self.chat_seesion_id
            chat_history.chat_mode = once_message.chat_mode
            chat_history.user_name = "default"
            chat_history.summary = once_message.get_user_conv().content

        conversations.append(_conversation_to_dic(once_message))
        chat_history.messages = json.dumps(conversations, ensure_ascii=False)

        self.chat_history_dao.update(chat_history)

    def update(self, messages: List[OnceConversation]) -> None:
        self.chat_history_dao.update_message_by_uid(
            json.dumps(messages, ensure_ascii=False), self.chat_seesion_id
        )

    def delete(self) -> bool:
        self.chat_history_dao.delete(self.chat_seesion_id)

    def conv_info(self, conv_uid: str = None) -> None:
        logger.info("conv_info:{}", conv_uid)
        chat_history = self.chat_history_dao.get_by_uid(conv_uid)
        return chat_history.__dict__

    def get_messages(self) -> List[OnceConversation]:
        # logger.info("get_messages:{}", self.chat_seesion_id)
        chat_history = self.chat_history_dao.get_by_uid(self.chat_seesion_id)
        if chat_history:
            context = chat_history.messages
            return json.loads(context)
        return []

    @staticmethod
    def conv_list(cls, user_name: str = None) -> None:
        chat_history_dao = ChatHistoryDao()
        history_list = chat_history_dao.list_last_20()
        result = []
        for history in history_list:
            result.append(history.__dict__)
        return result
