from django import forms
from django.core.exceptions import ValidationError

from .models import ApplicationUser, Question, QuestionReport
from .modules.exams import ExamCreate


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
        """ Verify requested question number is less or equal total number of questions in exam """
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
    exam_source = forms.CharField(label='Source of exam', required=False)

    def __init__(self, *args, **kwargs):
        self.uploader = kwargs.pop('user', None)
        super(UploadForm, self).__init__(*args, **kwargs)

    def clean(self):
        """
        Get exam title and JSON file with questions from form.
        Parse the file, create new exam, questions and question_json answer variants.
        In case of exceptions raised, they should be passed to form view without saving exam data.
        """
        cleaned_data = super(UploadForm, self).clean()
        exam_title = cleaned_data.get('exam_title')
        exam_source = cleaned_data.get('exam_source', None)
        try:
            file = cleaned_data.get('questions_file')
            if file.content_type != 'application/json':
                raise ValidationError('Question file must be in JSON format')
            exam_create = ExamCreate()
            parsing_errors = exam_create.create_exam(exam_title, file, exam_source, is_user_uploaded=True,
                                                     uploader=self.uploader)
            if parsing_errors:
                for error in parsing_errors:
                    self.add_error(None, error)
        except AttributeError:
            self.add_error(None, ValidationError('File with questions data wasn\'t provided.'))


class QuestionReportCreateUpdateForm(forms.ModelForm):
    """ Form for filling or updating exam question report """

    class Meta:
        model = QuestionReport
        fields = ['text']

    text = forms.CharField(label='Report text')


class QuestionReportUpdateFormAdmin(forms.ModelForm):
    """ Form for updating report as admin """

    class Meta:
        model = QuestionReport
        fields = ['resolution', 'status']

    resolution = forms.CharField(label='Report text')
    status = forms.CharField(label='Status')
