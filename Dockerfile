# syntax=docker/dockerfile:1

FROM python:3.11-slim-buster

ENV PYTHONUNBUFFERED=1
ENV TZ=Europe/Rome

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .

CMD ["python3", "bot.py"]
