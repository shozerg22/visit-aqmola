from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
from config import settings

try:
    from pgvector.sqlalchemy import Vector
except Exception:
    Vector = None  # type: ignore


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(256), unique=True, nullable=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=True, unique=True)
    role = Column(String(50), nullable=False, default="user")  # user, admin
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Object(Base):
    __tablename__ = "objects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(300), nullable=False)
    description = Column(Text)
    lat = Column(Float)
    lon = Column(Float)
    rating = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    object_id = Column(Integer, ForeignKey("objects.id"), nullable=False)
    start_date = Column(String(50))
    end_date = Column(String(50))
    status = Column(String(50), default="pending")
    payment_order_id = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    object = relationship("Object")


class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    object_id = Column(Integer, ForeignKey("objects.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    text = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    object = relationship("Object")


class Complaint(Base):
    __tablename__ = "complaints"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    object_id = Column(Integer, ForeignKey("objects.id"), nullable=True)
    category = Column(String(100), nullable=False)
    text = Column(Text, nullable=False)
    photo_url = Column(String(500), nullable=True)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    status = Column(String(50), default="new")  # new, in_review, resolved, rejected
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    object = relationship("Object")


class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    description = Column(Text)
    start_at = Column(String(50))
    end_at = Column(String(50))
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RAGEmbedding(Base):
    __tablename__ = "rag_embeddings"
    id = Column(Integer, primary_key=True, index=True)
    doc_id = Column(String(32), unique=True, index=True, nullable=False)
    title = Column(String(300), nullable=True)
    text = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)  # comma-separated
    # Vector column only if pgvector installed
    if Vector is not None:
        embedding = Column(Vector(settings.PGVECTOR_DIM))
    else:
        embedding = Column(Text, nullable=True)  # fallback; not efficient
    created_at = Column(DateTime(timezone=True), server_default=func.now())
