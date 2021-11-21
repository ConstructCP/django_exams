# syntax=docker/dockerfile:1
FROM python:3
ENV PYTHONUNBUFFERED=1
WORKDIR /exams_site

# Copy requirements.txt
COPY requirements.txt /exams_site

# Install requirements
RUN pip install -r requirements.txt

# Copy source code
COPY . /exams_site

# Run database migrations before running django
RUN python exam_site/manage.py migrate admin zero && python exam_site/manage.py makemigrations exams && python exam_site/manage.py migrate exams
