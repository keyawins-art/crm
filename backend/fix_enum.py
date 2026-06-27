from app.db.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    try:
        conn.execute(text("CREATE TYPE accounttype AS ENUM ('PROSPECT', 'CUSTOMER', 'PARTNER', 'VENDOR', 'COMPETITOR', 'OTHER');"))
        conn.commit()
    except Exception as e:
        print(f"Error creating accounttype: {e}")
        
    try:
        conn.execute(text("CREATE TYPE accountindustry AS ENUM ('TECHNOLOGY', 'FINANCE', 'HEALTHCARE', 'EDUCATION', 'MANUFACTURING', 'RETAIL', 'REAL_ESTATE', 'HOSPITALITY', 'LOGISTICS', 'OTHER');"))
        conn.commit()
    except Exception as e:
        print(f"Error creating accountindustry: {e}")
        
    try:
        conn.execute(text("CREATE TYPE auditaction AS ENUM ('CREATED', 'UPDATED', 'DELETED', 'VIEWED');"))
        conn.commit()
    except Exception as e:
        print(f"Error creating auditaction: {e}")
        
    try:
        conn.execute(text("CREATE TYPE contactsalutation AS ENUM ('MR', 'MRS', 'MS', 'DR', 'PROF');"))
        conn.commit()
    except Exception as e:
        print(f"Error creating contactsalutation: {e}")
        
    try:
        conn.execute(text("CREATE TYPE contactstatus AS ENUM ('ACTIVE', 'INACTIVE');"))
        conn.commit()
    except Exception as e:
        print(f"Error creating contactstatus: {e}")

    try:
        conn.execute(text("CREATE TYPE activitytype AS ENUM ('CALL', 'EMAIL', 'MEETING', 'DEMO', 'FOLLOW_UP', 'OTHER');"))
        conn.commit()
    except Exception as e:
        print(f"Error creating activitytype: {e}")
        
    try:
        conn.execute(text("CREATE TYPE activityoutcome AS ENUM ('INTERESTED', 'NOT_INTERESTED', 'CALLBACK', 'NO_ANSWER', 'LEFT_MESSAGE', 'OTHER');"))
        conn.commit()
    except Exception as e:
        print(f"Error creating activityoutcome: {e}")
        
    try:
        conn.execute(text("CREATE TYPE leadsourcetype AS ENUM ('WEBSITE', 'COLD_CALL', 'REFERRAL', 'SOCIAL_MEDIA', 'EMAIL_CAMPAIGN', 'TRADE_SHOW', 'ADVERTISEMENT', 'PARTNER', 'OTHER');"))
        conn.commit()
    except Exception as e:
        print(f"Error creating leadsourcetype: {e}")
        
    try:
        conn.execute(text("CREATE TYPE leadstatus AS ENUM ('NEW', 'ASSIGNED', 'IN_PROCESS', 'CONVERTED', 'RECYCLED', 'DEAD');"))
        conn.commit()
    except Exception as e:
        print(f"Error creating leadstatus: {e}")
        
    try:
        conn.execute(text("CREATE TYPE leadrating AS ENUM ('HOT', 'WARM', 'COLD');"))
        conn.commit()
    except Exception as e:
        print(f"Error creating leadrating: {e}")
        
    try:
        conn.execute(text("CREATE TYPE notificationtype AS ENUM ('INFO', 'WARNING', 'SUCCESS', 'ERROR');"))
        conn.commit()
    except Exception as e:
        print(f"Error creating notificationtype: {e}")
        
    try:
        conn.execute(text("CREATE TYPE opportunitytype AS ENUM ('NEW_BUSINESS', 'EXISTING_BUSINESS', 'RENEWAL', 'UPSELL', 'CROSS_SELL');"))
        conn.commit()
    except Exception as e:
        print(f"Error creating opportunitytype: {e}")
        
    try:
        conn.execute(text("CREATE TYPE opportunitystage AS ENUM ('PROSPECTING', 'QUALIFICATION', 'NEEDS_ANALYSIS', 'VALUE_PROPOSITION', 'ID_DECISION_MAKERS', 'PERCEPTION_ANALYSIS', 'PROPOSAL', 'NEGOTIATION', 'CLOSED_WON', 'CLOSED_LOST');"))
        conn.commit()
    except Exception as e:
        print(f"Error creating opportunitystage: {e}")
        
    try:
        conn.execute(text("CREATE TYPE productcategory AS ENUM ('SOFTWARE', 'HARDWARE', 'SERVICE', 'SUBSCRIPTION', 'CONSULTING', 'SUPPORT', 'OTHER');"))
        conn.commit()
    except Exception as e:
        print(f"Error creating productcategory: {e}")
        
    try:
        conn.execute(text("CREATE TYPE productstatus AS ENUM ('ACTIVE', 'INACTIVE', 'DISCONTINUED');"))
        conn.commit()
    except Exception as e:
        print(f"Error creating productstatus: {e}")

    try:
        conn.execute(text("CREATE TYPE quotationstatus AS ENUM ('DRAFT', 'SENT', 'ACCEPTED', 'REJECTED', 'EXPIRED', 'CANCELLED');"))
        conn.commit()
    except Exception as e:
        print(f"Error creating quotationstatus: {e}")
        
    try:
        conn.execute(text("CREATE TYPE userstatus AS ENUM ('ACTIVE', 'INACTIVE', 'SUSPENDED', 'INVITED');"))
        conn.commit()
    except Exception as e:
        print(f"Error creating userstatus: {e}")
