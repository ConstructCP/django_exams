# syntax=docker/dockerfile:1
FROM python:3
ENV PYTHONUNBUFFERED=1
WORKDIR /django_exams
COPY requirements.txt /django_exams/
RUN pip install -r requirements.txt
COPY . /django_exams/
RUN python exam_site/manage.py migrate
