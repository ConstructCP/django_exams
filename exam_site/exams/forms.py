import json

from django import forms

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

    def clean_question_number(self):
        cleaned_data = super(ExamSetupForm, self).clean()
        questions_requested = int(cleaned_data['question_number'])
        total_question_number = Question.objects.get(exam_id=self.exam_id).count()
        return questions_requested <= total_question_number


class UploadForm(forms.Form):
    """ Form for uploading data of a new exams"""
    exam_title = forms.CharField(label='Exam title')
    questions_file = forms.FileField(label='File with questions')

    def save_exam_data(self, form_data: dict) -> None:
        """
        Get exam title and JSON file with questions from form.
        Parse the file, create new exam, questions and question_json answer variants
        """
        exam_title = form_data['exam_title']
        exam = Exam.objects.create(title=exam_title)
        exam.save()

        questions_file = form_data['questions_file']
        file_contents = questions_file.read().decode('utf-8')
        json_contents = json.loads(file_contents)
        if questions_file.content_type != 'application/json':
            raise ValueError('Question file must be JSON')
        for question_json in json_contents:
            question = parse_question_data(question_json, exam)
            parse_question_variants(question_json, question)


def parse_question_data(question_json: dict, exam: Exam) -> Question:
    """ Create Question object from json and save in database """
    question = Question.objects.create(
        exam=exam,
        title=question_json['title'],
        text=question_json['text'],
        answer_explanation=question_json['answer_comment']
    )
    question.save()
    return question


def parse_question_variants(question_json: dict, question: Question) -> None:
    """ Create several QuestionVariant objects from json and save in database """
    correct_answers = question_json['answer']
    for choice_letter, text in question_json['variants'].items():
        is_correct_answer = choice_letter in correct_answers
        question_variant = QuestionVariant.objects.create(
            question=question,
            choice_letter=choice_letter,
            text=text,
            is_correct_answer=is_correct_answer
        )
        question_variant.save()
