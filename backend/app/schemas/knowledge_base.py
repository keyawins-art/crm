from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class ArticleBase(BaseModel):
    title: str = Field(..., max_length=255)
    content: str
    category: Optional[str] = Field(None, max_length=100)
    tags: List[str] = []
    is_published: bool = False


class ArticleCreate(ArticleBase):
    pass


class ArticleUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    content: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None
    is_published: Optional[bool] = None


class ArticleRead(ArticleBase):
    id: UUID
    author_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
