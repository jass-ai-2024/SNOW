from pathlib import Path

from sqlalchemy import Column, Integer, String, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from app.core.config import settings

Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    content = Column(String)
    doc_metadata = Column(JSON)
    download_url = Column(Text, nullable=True)
    children = relationship("Document")
