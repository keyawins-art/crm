import sys
sys.path.insert(0, r'D:\CRM\backend')
from app.main import app
print(app.title)
print([route.path for route in app.routes if hasattr(route, 'path')][:20])
