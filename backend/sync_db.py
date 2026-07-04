import sys
sys.path.insert(0, '.')

from app.db.database import engine
from app.models.base import Base
import app.models.company_settings  # Ensure model is imported so it registers with Base

print("Creating missing tables...")
Base.metadata.create_all(bind=engine)
print("Done!")
