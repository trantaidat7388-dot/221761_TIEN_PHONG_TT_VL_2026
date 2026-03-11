from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    history = relationship("ConversionHistory", back_populates="owner")


class ConversionHistory(Base):
    __tablename__ = "conversion_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_id = Column(String, index=True)
    file_name = Column(String)
    template_name = Column(String)
    status = Column(String)
    file_path = Column(String, default="")   # local path to output .zip
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="history")
