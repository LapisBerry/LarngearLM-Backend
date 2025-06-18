from sqlalchemy import Column, Integer, String, BigInteger, DateTime

from .database import Base

class FileMetadata(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    bucket_name = Column(String, nullable=False)
    object_name = Column(String, nullable=False, unique=True)
    content_type = Column(String, nullable=False)
    size = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default="now()")
