#!/usr/bin/env bash

# run django
venv/bin/python manage.py runserver 0.0.0.0:32283 --insecure &

# run celery
rabbitmq-server &
venv/bin/celery -A chatbot_demo worker -l info &
