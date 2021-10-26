# syntax=docker/dockerfile:1
FROM python:3
ENV PYTHONUNBUFFERED=1
WORKDIR /django_exams

# Get code from repository
RUN wget https://github.com/ConstructCP/django_exams/archive/refs/heads/main.zip && unzip main.zip && mv django_exams-main/* ./

# Install requirements
RUN pip install -r requirements.txt

# Run database migrations before running django
RUN python exam_site/manage.py makemigrations exams && python exam_site/manage.py migrate exams
