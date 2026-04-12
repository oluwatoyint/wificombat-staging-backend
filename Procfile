web: daphne -b 0.0.0.0 -p $PORT backend.asgi:application
worker: celery -A backend worker --loglevel=info --concurrency=2
beat: celery -A backend beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
