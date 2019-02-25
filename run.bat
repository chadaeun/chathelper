START /b cmd /c venv/bin/python manage.py runserver --insecure
START /b cmd /c venv/bin/celery -A chatbot_demo worker -l info