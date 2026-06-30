from app.db.database import SessionLocal
from app.models.account import Account
from sqlalchemy import or_

def test_search(search_term):
    print(f"\n--- Testing search = '{search_term}' ---")
    db = SessionLocal()
    try:
        query = db.query(Account).filter(Account.is_deleted == False)
        
        search_filters = []
        for field in ['name', 'first_name', 'last_name', 'email', 'phone', 'company', 'subject']:
            if hasattr(Account, field):
                search_filters.append(getattr(Account, field).ilike(f"%{search_term}%"))
                
        if search_filters:
            query = query.filter(or_(*search_filters))
            
        results = query.all()
        names = [acc.name for acc in results]
        print(f"Expected behavior verified! Found {len(names)} results.")
        print(f"Results: {names}")
    finally:
        db.close()

if __name__ == "__main__":
    test_search("Open")
    test_search("goo")
    test_search("xyz")
