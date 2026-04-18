from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

# Override CELERY_BROKER_URL with public Redis URL before Celery reads it
custom_redis = os.getenv("CUSTOM_REDIS_URL")
if custom_redis:
    os.environ["CELERY_BROKER_URL"] = custom_redis

app = Celery("backend")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")