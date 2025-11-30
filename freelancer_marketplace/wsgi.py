"""
WSGI config for freelancer_marketplace project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freelancer_marketplace.settings')

application = get_wsgi_application()

