from app.db.database import engine, create_all_tables
from app.models import Base

# Ensure all models are imported (done via app.models.__init__)
print("Creating tables...")
create_all_tables()
print("Done.")
