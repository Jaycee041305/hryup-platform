import os
from django.core.asgi import get_asgi_application
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hryup.settings.prod')
application = get_asgi_application()
