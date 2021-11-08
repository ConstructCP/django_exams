from argparse import ArgumentParser
from django.core.management.base import BaseCommand, CommandError

from exams.models import Exam, Question, QuestionVariant
from exams.modules.exams import ExamCreate


class Command(BaseCommand):
    """ Django cmd command for exam data uploading """
    help = 'Upload exam questions from file'

    def add_arguments(self, parser: ArgumentParser):
        """ Adds cmd arguments to command"""
        parser.add_argument('questions_file', nargs='?', type=str, help='Name of a JSON file with questions')
        parser.add_argument('--title', action='store', help='Title of an exam')

    def handle(self, *args, **options):
        exam_title = options.get('title')
        if not exam_title:
            exam_title = input('Enter the exam name: ')
        file_name = options.get('questions_file')
        file_with_questions = open(file_name, 'r')

        exam_create = ExamCreate()
        errors = exam_create.create_exam(exam_title, file_with_questions)
        if errors:
            for error in errors:
                print(error)


