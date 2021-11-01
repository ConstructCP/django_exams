import random

from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import QuerySet
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.views import generic

from .forms import RegistrationForm, UploadForm, ExamSetupForm
from .models import ApplicationUser, Exam, Question, QuestionVariant, ExamResults, QuestionRecorded, \
    QuestionVariantAnswerRecorded


class IndexView(generic.ListView):
    """ View for index page of the application"""
    template_name = 'exams/index.html'
    context_object_name = 'exam_list'

    def get_queryset(self) -> QuerySet:
        """ Returns list of all exams """
        return Exam.objects.all()


class Login(LoginView):
    """ View for login page """
    template_name = 'exams/login.html'
    redirect_authenticated_user = True
    next_page = 'exams:index'


class Logout(LogoutView):
    """ View for logout page """
    next_page = 'exams:login'


def register(request: WSGIRequest) -> HttpResponse:
    """
    View for register page.
    For GET request - display registration form
    For POST request - save user with provided name and password and redirect to login page
    """
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('exams:index'))
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            try:
                validate_password(user=username, password=password)
            except ValidationError as e:
                return render(request, 'exams/register.html', {'form': form, 'error_message': e})
            user = ApplicationUser.objects.create_user(username=username, password=password)
            user.save()
            return HttpResponseRedirect(reverse('exams:login'))
    else:
        form = RegistrationForm()

    return render(request, 'exams/register.html', {'form': form})


class ProfileView(generic.DetailView):
    template_name = 'exams/profile.html'
    model = ApplicationUser


class ExamSetupView(generic.FormView):
    """ View for exam setup """
    template_name = 'exams/exam_setup.html'
    form_class = ExamSetupForm
    question_number = None
    success_url = 'exams:exam_take'

    def get_context_data(self, **kwargs) -> dict:
        exam_id = self.kwargs['exam_id']
        exam = Exam.objects.get(id=exam_id)
        context = super().get_context_data(**kwargs)
        context['exam'] = exam
        return context

    def form_valid(self, form) -> bool:
        self.question_number = int(form.cleaned_data().get('question_number'))
        return super().form_valid(form)


class ExamTakeView(generic.View):
    """ View for exam taking """
    template_name = 'exams/exam_take.html'

    def __init__(self, *args, **kwargs):
        self._exam_id = None
        super().__init__(*args, **kwargs)

    def post(self, request: WSGIRequest, exam_id: str) -> HttpResponse:
        """
        Handle POST request. Return exam data in response. If question_quantity is less that amount of questions
        in the exam - return question_quantity of random questions.
        Adds to each question_json
            - answer variants
            - boolean indicating whether number of correct answers is 1 or more
        """
        question_quantity = int(request.POST['question_quantity'])
        exam_id = int(exam_id)
        exam = Exam.objects.get(id=exam_id)
        questions = Question.objects.filter(exam_id=exam_id)
        total_question_number = questions.count()
        if question_quantity < total_question_number:
            questions = random.sample(list(questions), question_quantity)

        for question in questions:
            question_id = question.id
            answer_variants = QuestionVariant.objects.filter(question__id=question_id)
            correct_answers_num = QuestionVariant.objects.filter(
                question__id=question_id, is_correct_answer=True).count()
            has_one_correct_answer = correct_answers_num == 1
            question.answer_variants = answer_variants
            question.has_one_correct_answer = has_one_correct_answer

        context = {'exam': exam, 'questions': questions}
        return render(request, 'exams/exam_take.html', context=context)


class ExamResultView(generic.View):
    """ View to get or save exam results """
    template_name = 'exams/exam_result.html'

    def get(self, request: WSGIRequest, exam_id: str, exam_record_datetime: str) -> HttpResponse:
        """ Show exam results """
        exam = Exam.objects.get(id=exam_id)
        exam_record = ExamResults.objects.get(exam_id=exam_id, unique_id=exam_record_datetime)
        # TODO Check user permissions to access this exam record
        question_records = QuestionRecorded.objects.filter(exam_result=exam_record)
        # question_ids = [q_record.id for q_record in question_records]
        questions = []
        for question_record in question_records:
            question = Question.objects.get(id=question_record.question.id)
            is_answer_correct = True
            answer_variants = QuestionVariant.objects.filter(question=question)
            for answer_variant in answer_variants:
                answer_record = QuestionVariantAnswerRecorded.objects.get(
                    question_recorded=question_record, question_variant=answer_variant)
                answer_variant.was_selected = answer_record.was_selected
                if answer_variant.was_selected ^ answer_variant.is_correct_answer:
                    is_answer_correct = False
            question.answer_variants = answer_variants
            question.is_answer_correct = is_answer_correct
            questions.append(question)
        context = {'exam': exam, 'exam_record': exam_record, 'questions': questions}
        return render(request, 'exams/exam_results.html', context=context)


class ExamSave(generic.View):
    """ View for exam results saving """

    def post(self, request: WSGIRequest, exam_id: str) -> HttpResponse:
        """ Get exam results, store in database and redirect to exam results view """
        answers = {int(question_id): request.POST.getlist(question_id)
                   for question_id in request.POST.keys()
                   if 'csrf' not in question_id}
        exam_results = ExamResults(exam_id=int(exam_id), user_id=request.user.id)
        exam_results.save()
        total_questions_in_exam = len(answers)
        questions_with_correct_answers = 0
        for question in Question.objects.filter(id__in=answers.keys()):
            question_record = QuestionRecorded(exam_result=exam_results, question=question)
            question_record.save()
            is_answer_correct = True
            for answer_variant in QuestionVariant.objects.filter(question__id=question.id):
                was_selected = answer_variant.choice_letter in answers[question.id]
                variant_record = QuestionVariantAnswerRecorded(
                    question_variant=answer_variant, question_recorded=question_record, was_selected=was_selected)
                variant_record.save()
                if answer_variant.is_correct_answer ^ variant_record.was_selected:
                    is_answer_correct = False
            if is_answer_correct:
                questions_with_correct_answers += 1
        exam_results.score = int(questions_with_correct_answers / total_questions_in_exam * 100)
        exam_results.save(update_fields=['score'])
        return redirect('exams:exam_results', context={'exam_id': exam_id,
                                                       'datetime_str': exam_results.taken_on_as_str})


class UploadView(generic.FormView):
    template_name = 'exams/upload.html'
    form_class = UploadForm
    success_url = reverse_lazy('exams:index')

    def form_valid(self, form) -> bool:
        form.save_exam_data(form.cleaned_data)
        return super().form_valid(form)


def health_check_view(request: WSGIRequest):
    return HttpResponse('OK')
