import logging
from uuid import UUID
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.workflow import WorkflowRule, WorkflowActionType
from app.models.task import Task
from app.api.notifications import send_notification
from app.models.audit import NotificationType
from app.core.email import send_email

logger = logging.getLogger(__name__)

def execute_workflows(entity_type: str, event: str, entity_id: UUID, current_user_id: UUID = None):
    """
    Background job to execute workflows for a given entity and event.
    Note: We instantiate a fresh DB session since this runs in a background thread.
    """
    db = SessionLocal()
    try:
        # Find active rules
        rules = db.query(WorkflowRule).filter(
            WorkflowRule.trigger_entity == entity_type,
            WorkflowRule.trigger_event == event,
            WorkflowRule.is_active == True
        ).all()

        if not rules:
            return

        # Fetch the entity from DB dynamically based on entity_type
        # We need to import the models mapping here to avoid circular imports
        from app.models.lead import Lead
        from app.models.opportunity import Opportunity
        from app.models.account import Account
        from app.models.contact import Contact
        
        models_map = {
            "Lead": Lead,
            "Opportunity": Opportunity,
            "Account": Account,
            "Contact": Contact
        }
        
        ModelClass = models_map.get(entity_type)
        if not ModelClass:
            logger.error(f"Workflow execution failed: Unknown entity type '{entity_type}'")
            return
            
        entity = db.query(ModelClass).filter(ModelClass.id == entity_id, ModelClass.is_deleted == False).first()
        if not entity:
            logger.error(f"Workflow execution failed: Entity '{entity_id}' not found")
            return

        for rule in rules:
            logger.info(f"Executing workflow rule '{rule.name}' for {entity_type} {entity_id}")
            for action in rule.actions:
                try:
                    params = action.action_params
                    
                    if action.action_type == WorkflowActionType.ASSIGN_USER:
                        target_user_id = params.get("user_id")
                        if target_user_id and hasattr(entity, 'assigned_to_id'):
                            entity.assigned_to_id = target_user_id
                            db.commit()
                            db.refresh(entity)
                            logger.info(f"Action: Assigned {entity_type} to user {target_user_id}")
                            
                    elif action.action_type == WorkflowActionType.CREATE_TASK:
                        # Find assignment
                        assigned_to = params.get("assigned_to_id") or getattr(entity, 'assigned_to_id', None) or current_user_id
                        
                        task = Task(
                            title=params.get("title", f"Follow up with {entity_type}"),
                            description=params.get("description", "Auto-generated task from workflow rule."),
                            assigned_to_id=assigned_to,
                            due_date=datetime.now(timezone.utc) + timedelta(days=int(params.get("due_in_days", 1))),
                            created_by_id=current_user_id
                        )
                        # Link to entity
                        if entity_type == "Lead":
                            task.lead_id = entity.id
                        elif entity_type == "Opportunity":
                            task.opportunity_id = entity.id
                        elif entity_type == "Contact":
                            task.contact_id = entity.id
                        elif entity_type == "Account":
                            task.account_id = entity.id
                            
                        db.add(task)
                        db.commit()
                        logger.info(f"Action: Created Task '{task.title}'")

                    elif action.action_type == WorkflowActionType.SEND_EMAIL:
                        to_email = params.get("to_email")
                        if not to_email and hasattr(entity, 'email'):
                            to_email = entity.email
                            
                        if to_email:
                            subject = params.get("subject", "Hello from CRM")
                            # Simple template replacement
                            body = params.get("body", "").replace("{{first_name}}", getattr(entity, 'first_name', 'Customer'))
                            
                            send_email(
                                to_email=to_email,
                                subject=subject,
                                body=body,
                                sender_id=current_user_id,
                                lead_id=entity_id if entity_type == "Lead" else None,
                                opportunity_id=entity_id if entity_type == "Opportunity" else None,
                                contact_id=entity_id if entity_type == "Contact" else None
                            )
                            logger.info(f"Action: Sent email to {to_email}")

                    elif action.action_type == WorkflowActionType.NOTIFY_USER:
                        target_user_id = params.get("user_id") or getattr(entity, 'assigned_to_id', None)
                        if target_user_id:
                            send_notification(
                                db=db,
                                user_id=target_user_id,
                                title=params.get("title", "Workflow Notification"),
                                message=params.get("message", f"A workflow was triggered for {entity_type}."),
                                type=NotificationType.INFO
                            )
                            logger.info(f"Action: Notified user {target_user_id}")

                except Exception as e:
                    logger.error(f"Error executing action {action.action_type} for rule {rule.id}: {e}")
                    db.rollback()

    finally:
        db.close()
