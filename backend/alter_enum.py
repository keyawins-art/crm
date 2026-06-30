from sqlalchemy import create_engine, text
engine = create_engine('postgresql://postgres:postgres@localhost:5432/crm_db')
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TYPE auditaction ADD VALUE 'logged_in'"))
        conn.commit()
        print('Enum value added successfully')
    except Exception as e:
        print(f'Enum value might already exist or error: {e}')
