from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Boolean, Enum, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from database import Base


# Enums para el sistema
class AccessLevel(enum.Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    # Nombre legible
    nombre = Column(String, nullable=True)
    # Si el usuario está activo (1) o inactivo (0)
    activo = Column(Integer, nullable=False, default=1)

    # Relaciones
    conversations = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class CustomChatbot(Base):
    __tablename__ = "custom_chatbots"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    pinecone_index_name = Column(String, nullable=False, unique=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    creator = relationship("User", foreign_keys=[created_by])
    documents = relationship("ChatbotDocument", back_populates="chatbot", cascade="all, delete-orphan")
    access_list = relationship("ChatbotAccess", back_populates="chatbot", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="chatbot")


class ChatbotAccess(Base):
    __tablename__ = "chatbot_access"

    id = Column(Integer, primary_key=True, index=True)
    chatbot_id = Column(Integer, ForeignKey("custom_chatbots.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    access_level = Column(Enum(AccessLevel), nullable=False, default=AccessLevel.READ)
    granted_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    granted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relaciones
    chatbot = relationship("CustomChatbot", back_populates="access_list")
    user = relationship("User", foreign_keys=[user_id])
    granter = relationship("User", foreign_keys=[granted_by])


class ChatbotDocument(Base):
    __tablename__ = "chatbot_documents"

    id = Column(Integer, primary_key=True, index=True)
    chatbot_id = Column(Integer, ForeignKey("custom_chatbots.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(BigInteger, nullable=False)
    file_type = Column(String, nullable=False)
    chunks_count = Column(Integer, default=0)
    is_processed = Column(Boolean, default=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relaciones
    chatbot = relationship("CustomChatbot", back_populates="documents")
    uploader = relationship("User", foreign_keys=[uploaded_by])


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    # Owner/creador de la conversación (normalmente el admin que creó)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    # Nuevo: referencia al chatbot personalizado (opcional, para conversaciones con RAG)
    chatbot_id = Column(Integer, ForeignKey("custom_chatbots.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String, nullable=False, default="Nueva conversación")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    user = relationship("User", back_populates="conversations")
    chatbot = relationship("CustomChatbot", back_populates="conversations")
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )


class ConversationParticipant(Base):
    # En la DB actual la tabla aparece como 'conversation_participant' (singular)
    __tablename__ = "conversation_participant"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String, nullable=False)
    path = Column(String, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    sender = Column(String, nullable=False)  # 'user' | 'ai'
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relaciones
    conversation = relationship("Conversation", back_populates="messages")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    report_type = Column(String, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status = Column(String, nullable=False, default="pendiente")
