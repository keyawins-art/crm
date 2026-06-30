import math
from typing import List, Optional
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.database import SessionLocal
from app.models.user import User
from app.models.knowledge_base import KnowledgeBaseArticle
from app.core.rbac import require_permission

from app.schemas.knowledge_base import ArticleCreate, ArticleRead, ArticleUpdate
from app.schemas.crm import PaginatedResponse

router = APIRouter(prefix="/crm/knowledge-base", tags=["Knowledge Base"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("", response_model=ArticleRead, status_code=status.HTTP_201_CREATED)
def create_article(
    payload: ArticleCreate,
    current_user: User = Depends(require_permission("kb:create")),
    db: Session = Depends(get_db)
):
    article = KnowledgeBaseArticle(
        title=payload.title,
        content=payload.content,
        category=payload.category,
        tags=payload.tags,
        is_published=payload.is_published,
        author_id=current_user.id
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


@router.get("", response_model=PaginatedResponse[ArticleRead])
def list_articles(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    is_published: Optional[bool] = None,
    current_user: User = Depends(require_permission("kb:read")),
    db: Session = Depends(get_db)
):
    query = db.query(KnowledgeBaseArticle).filter(KnowledgeBaseArticle.is_deleted == False)
    
    if category:
        query = query.filter(KnowledgeBaseArticle.category == category)
    if is_published is not None:
        query = query.filter(KnowledgeBaseArticle.is_published == is_published)
        
    total = query.count()
    items = query.order_by(KnowledgeBaseArticle.created_at.desc()).offset((page - 1) * size).limit(size).all()
    
    return {
        "items": items,
        "page": page,
        "size": size,
        "total": total,
        "pages": math.ceil(total / size) if size > 0 else 0
    }


@router.get("/{id}", response_model=ArticleRead)
def get_article(
    id: UUID,
    current_user: User = Depends(require_permission("kb:read")),
    db: Session = Depends(get_db)
):
    article = db.query(KnowledgeBaseArticle).filter(KnowledgeBaseArticle.id == id, KnowledgeBaseArticle.is_deleted == False).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.put("/{id}", response_model=ArticleRead)
def update_article(
    id: UUID,
    payload: ArticleUpdate,
    current_user: User = Depends(require_permission("kb:update")),
    db: Session = Depends(get_db)
):
    article = db.query(KnowledgeBaseArticle).filter(KnowledgeBaseArticle.id == id, KnowledgeBaseArticle.is_deleted == False).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
        
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(article, key, value)
        
    db.commit()
    db.refresh(article)
    return article


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_article(
    id: UUID,
    current_user: User = Depends(require_permission("kb:delete")),
    db: Session = Depends(get_db)
):
    article = db.query(KnowledgeBaseArticle).filter(KnowledgeBaseArticle.id == id, KnowledgeBaseArticle.is_deleted == False).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
        
    article.is_deleted = True
    article.deleted_at = datetime.now(timezone.utc)
    db.commit()
