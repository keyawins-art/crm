"""Permission-aware CRM Copilot endpoints backed by a local Ollama model."""

from __future__ import annotations

import re
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.database import get_db
from app.models import KnowledgeBaseArticle, Lead, LeadStatus, Opportunity, Ticket, TicketStatus, User, Product, CompanySettings
from app.schemas.ai import CopilotRequest, CopilotResponse, CopilotStatus
from app.services.ollama import OllamaUnavailable, chat, get_model_name, get_status, is_enabled


router = APIRouter(prefix="/ai", tags=["AI Copilot"])


def _has_permission(user: User, permission: str) -> bool:
    if not user.role:
        return False
    return permission in {item.name for item in user.role.permissions}


def _is_sales_executive(user: User) -> bool:
    return bool(user.role and user.role.name == "Sales Executive")


def _format_value(value: object) -> object:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if hasattr(value, "value"):
        return value.value
    if value is None:
        return None
    return str(value)


def _excerpt(text: str | None, length: int = 700) -> str | None:
    if not text:
        return None
    clean_text = " ".join(text.split())
    return clean_text[:length] + ("…" if len(clean_text) > length else "")


def _matching_products(db: Session, question: str) -> list[Product]:
    products = (
        db.query(Product)
        .filter(Product.is_deleted.is_(False))
        .limit(50)
        .all()
    )
    if not products:
        return []

    terms = {term for term in re.findall(r"[\w-]{3,}", question.lower())}
    if not terms:
        return products[:3]

    def relevance(prod: Product) -> int:
        haystack = f"{prod.name} {prod.code or ''} {prod.category or ''} {prod.description or ''}".lower()
        return sum(term in haystack for term in terms)

    matched = [prod for prod in sorted(products, key=relevance, reverse=True) if relevance(prod) > 0]
    return matched[:3] if matched else products[:2]


def _matching_articles(db: Session, user: User, question: str) -> list[KnowledgeBaseArticle]:
    if not _has_permission(user, "kb:read"):
        return []

    articles = (
        db.query(KnowledgeBaseArticle)
        .filter(
            KnowledgeBaseArticle.is_deleted.is_(False),
            KnowledgeBaseArticle.is_published.is_(True),
        )
        .limit(60)
        .all()
    )
    terms = {term for term in re.findall(r"[\w-]{3,}", question.lower())}
    if not terms:
        return articles[:3]

    def relevance(article: KnowledgeBaseArticle) -> int:
        haystack = f"{article.title} {article.category or ''} {' '.join(article.tags or [])} {article.content}".lower()
        return sum(term in haystack for term in terms)

    matched = [article for article in sorted(articles, key=relevance, reverse=True) if relevance(article) > 0]
    return matched[:3] if matched else articles[:2]


def _build_crm_context(db: Session, user: User, question: str) -> tuple[dict[str, object], list[str]]:
    """Build RAG context containing permitted CRM records, Products, Policies & FAQs."""
    sources = ["Your permitted CRM records"]

    lead_query = db.query(Lead).filter(Lead.is_deleted.is_(False))
    opportunity_query = db.query(Opportunity).filter(Opportunity.is_deleted.is_(False))
    ticket_query = db.query(Ticket).filter(Ticket.is_deleted.is_(False))
    if _is_sales_executive(user):
        lead_query = lead_query.filter(or_(Lead.assigned_to_id == user.id, Lead.created_by_id == user.id))
        opportunity_query = opportunity_query.filter(
            or_(Opportunity.assigned_to_id == user.id, Opportunity.created_by_id == user.id)
        )
        ticket_query = ticket_query.filter(or_(Ticket.assigned_to_id == user.id, Ticket.created_by_id == user.id))

    # For simple greetings/short queries, keep context minimal for high CPU speed
    is_greeting = len(question.strip()) < 15 or question.strip().lower() in {"hi", "hello", "hey", "help", "test"}
    lead_limit = 2 if is_greeting else 5
    opp_limit = 2 if is_greeting else 5
    ticket_limit = 2 if is_greeting else 5

    active_leads = (
        lead_query.filter(Lead.status.notin_([LeadStatus.CONVERTED, LeadStatus.DEAD]))
        .order_by(Lead.next_followup_date.asc().nullslast(), Lead.created_at.desc())
        .limit(lead_limit)
        .all()
    )
    active_opportunities = (
        opportunity_query.filter(Opportunity.stage.notin_(["closed_won", "closed_lost"]))
        .order_by(Opportunity.close_date.asc(), Opportunity.created_at.desc())
        .limit(opp_limit)
        .all()
    )
    open_tickets = (
        ticket_query.filter(Ticket.status.notin_([TicketStatus.RESOLVED, TicketStatus.CLOSED]))
        .order_by(Ticket.priority.desc(), Ticket.created_at.desc())
        .limit(ticket_limit)
        .all()
    )

    # RAG: Match Products & Pricing
    products = _matching_products(db, question)
    if products:
        sources.append("Products & Pricing Catalog")

    # RAG: Match FAQs & Policies
    articles = _matching_articles(db, user, question)
    if articles:
        sources.extend(f"Knowledge Base: {article.title}" for article in articles)

    # RAG: Company Profile Settings
    company = db.query(CompanySettings).first()

    context: dict[str, object] = {
        "today": date.today().isoformat(),
        "company_profile": {
            "company_name": company.company_name if company else "Nexus Machine Tools",
            "phone": company.phone if company else None,
            "address": company.address if company else None,
            "gst_number": company.gst_number if company else None,
        } if company else None,
        "products_catalog": [
            {
                "product_name": p.name,
                "sku_code": p.code,
                "category": _format_value(p.category),
                "list_price": f"{p.list_price} {p.currency}",
                "description": _excerpt(p.description, 250),
            }
            for p in products
        ],
        "knowledge_base_faqs": [
            {
                "title": article.title,
                "category": article.category,
                "content": _excerpt(article.content, 600),
            }
            for article in articles
        ],
        "active_leads": [
            {
                "name": lead.full_name,
                "company": lead.company,
                "status": _format_value(lead.status),
                "rating": _format_value(lead.rating),
                "next_followup_date": _format_value(lead.next_followup_date),
                "requirements": _excerpt(lead.requirements),
                "remarks": _excerpt(lead.remarks),
            }
            for lead in active_leads
        ],
        "active_opportunities": [
            {
                "name": opportunity.name,
                "account": opportunity.account.name if opportunity.account else None,
                "stage": _format_value(opportunity.stage),
                "amount": _format_value(opportunity.amount),
                "currency": opportunity.currency,
                "close_date": _format_value(opportunity.close_date),
            }
            for opportunity in active_opportunities
        ],
        "open_tickets": [
            {
                "number": ticket.ticket_number,
                "subject": ticket.subject,
                "status": _format_value(ticket.status),
                "priority": _format_value(ticket.priority),
            }
            for ticket in open_tickets
        ],
    }
    return context, sources


def _clean_answer(text: str) -> str:
    if not text:
        return ""
    # Remove <think>...</think> reasoning block
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    
    # Extract only the final response if reasoning text was generated
    if "Response:" in cleaned:
        cleaned = cleaned.split("Response:")[-1].strip()
    elif "Answer:" in cleaned:
        cleaned = cleaned.split("Answer:")[-1].strip()
    elif "\n\n" in cleaned:
        blocks = [b.strip() for b in cleaned.split("\n\n") if b.strip()]
        cleaned = blocks[-1]

    return cleaned or text.strip()


def _system_message(context: dict[str, object], user: User) -> str:
    return f"""You are NexusCRM Copilot, a fast, friendly CRM chatbot.

RULES:
- Answer directly in 1-2 short sentences. Do NOT think or analyze.
- Do NOT output internal reasoning like "Okay...", "I need to...".
- Use only this CRM context for facts: {context}
User: {user.full_name}
"""


@router.get("/status", response_model=CopilotStatus)
def copilot_status(current_user: User = Depends(get_current_user)):
    if not _has_permission(current_user, "accounts:read"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to CRM Copilot.")
    ready, detail = get_status()
    return CopilotStatus(enabled=is_enabled(), ready=ready, model=get_model_name(), detail=detail)


@router.post("/chat", response_model=CopilotResponse)
def copilot_chat(
    payload: CopilotRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not _has_permission(current_user, "accounts:read"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to CRM Copilot.")

    ready, detail = get_status()
    if not ready:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)

    context, sources = _build_crm_context(db, current_user, payload.message)
    messages = [{"role": "system", "content": _system_message(context, current_user)}]
    messages.extend({"role": item.role, "content": item.content} for item in payload.conversation[-8:])
    messages.append({"role": "user", "content": payload.message})
    try:
        raw_answer = chat(messages)
        answer = _clean_answer(raw_answer)
    except OllamaUnavailable as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    return CopilotResponse(answer=answer, model=get_model_name(), sources=sources)
