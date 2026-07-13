from app.db.database import SessionLocal
from app.models.opportunity import Opportunity, OpportunityStage
db = SessionLocal()
opp = db.query(Opportunity).first()
if opp:
    print('Current:', opp.stage)
    try:
        opp.stage = OpportunityStage.CLOSED_WON
        db.commit()
        print('Value worked')
    except Exception as e:
        print('Value failed:', e)
        db.rollback()
