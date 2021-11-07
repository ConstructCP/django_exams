import json
from typing import List, Dict, IO

from django import forms
from django.core.exceptions import ValidationError

from .models import ApplicationUser, Exam, Question, QuestionVariant


class RegistrationForm(forms.ModelForm):
    """ Form for user registration """
    class Meta:
        model = ApplicationUser
        fields = ['username', 'password']
        widgets = {'password': forms.PasswordInput()}


class ExamSetupForm(forms.Form):
    question_number = forms.IntegerField(label='Question number')

    def __init__(self, *args, **kwargs):
        super(ExamSetupForm, self).__init__(*args, **kwargs)
        self.exam_id = kwargs.get('exam_id')

    def clean_question_number(self) -> bool:
        cleaned_data = super(ExamSetupForm, self).clean()
        questions_requested = int(cleaned_data['question_number'])
        total_question_number = Question.objects.get(exam_id=self.exam_id).count()
        if questions_requested > total_question_number:
            raise ValidationError('Requested number of questions exceeds number of questions in exam')
        return questions_requested


class UploadForm(forms.Form):
    """ Form for uploading data of a new exams"""
    exam_title = forms.CharField(label='Exam title')
    questions_file = forms.FileField(label='File with questions')

    def clean(self):
        """
        Get exam title and JSON file with questions from form.
        Parse the file, create new exam, questions and question_json answer variants.
        In case of exceptions raised, they should be passed to form view without saving exam data
        """
        cleaned_data = super(UploadForm, self).clean()
        exam_title = cleaned_data.get('exam_title')
        exam = Exam(title=exam_title)
        questions = []
        question_answers_variants = []

        try:
            json_contents = self.get_json_from_file(cleaned_data.get('questions_file'))
        except AttributeError:
            self.add_error(None, ValidationError('File with questions data wasn\'t provided.'))
        try:
            for question_json in json_contents:
                question = self.parse_question_data(question_json, exam)
                variants = self.parse_question_variants(question_json, question)
                questions.append(question)
                question_answers_variants.extend(variants)
        except FileParsingError as e:
            raise ValidationError(str(e))

        if not self.errors:
            exam.save()
            Question.objects.bulk_create(questions)
            QuestionVariant.objects.bulk_create(question_answers_variants)

    def get_json_from_file(self, file: IO) -> Dict:
        """ Check file format, decode and parse as JSON """
        if file.content_type != 'application/json':
            raise FileParsingError('Question file must be in JSON format')
        file_contents = file.read().decode('utf-8')
        json_contents = json.loads(file_contents)
        return json_contents

    def parse_question_data(self, question_json: dict, exam: Exam) -> Question:
        """ Create Question object from json """
        if not question_json['title']:
            self.add_error(None, FileParsingError('One of questions doesn\'t have title.'))
        if not question_json['text']:
            self.add_error(None,
                           FileParsingError(f'Question {question_json["title"]} doesn\'t have question text.'))
        question = Question(exam=exam, title=question_json['title'], text=question_json['text'],
                            answer_explanation=question_json['answer_comment'])
        return question

    def parse_question_variants(self, question_json: dict, question: Question) -> List[QuestionVariant]:
        """ Create several QuestionVariant objects from json """
        correct_answers = question_json['answer']
        if not correct_answers:
            self.add_error(None,
                           FileParsingError(f'No correct answer marked for question {question_json["title"]}'))
        if not len(question_json['variants']):
            self.add_error(None,
                           FileParsingError(f'No variants in question {question_json["title"]}'))
        answer_variants = []
        for choice_letter, text in question_json['variants'].items():
            is_correct_answer = choice_letter in correct_answers
            question_variant = QuestionVariant(question=question, choice_letter=choice_letter, text=text,
                                               is_correct_answer=is_correct_answer)
            answer_variants.append(question_variant)
        return answer_variants


class FileParsingError(Exception):
    pass
