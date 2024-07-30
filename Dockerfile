FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN python -m pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

ENV PYTHONUNBUFFERED=1

RUN ["python", "api/manage.py", "makemigrations"]
RUN ["python", "api/manage.py", "migrate"]
#runserver
CMD ["python", "api/manage.py", "runserver", "0.0.0.0:8000"]