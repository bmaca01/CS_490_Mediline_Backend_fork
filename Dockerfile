# syntax=docker/dockerfile:1

FROM python:3.10.12-slim-bullseye

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080 9000
COPY . work/
WORKDIR /work/

CMD ["celery", "-A", "flaskr.main", "worker", "-l", "INFO", "-Q", "prescription_queue"]

