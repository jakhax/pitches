web: gunicorn 'pitches.app:create_app()' --access-logfile - --error-logfile -
worker: celery worker -A pitches.celery_worker.celery --loglevel=info
