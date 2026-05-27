FROM python:3.11-slim

WORKDIR /app

COPY breathe_esg/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY breathe_esg/ .

ENV DJANGO_SETTINGS_MODULE=breathe_esg.settings

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]