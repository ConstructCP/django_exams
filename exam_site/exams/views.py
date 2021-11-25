import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List

from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import QuerySet, Case, When, Value, Avg, Count
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.views import generic

from . import forms
from . import models


class IndexView(generic.ListView):
    """ View for index page of the application"""
    template_name = 'exams/index.html'
    context_object_name = 'exam_list'

    def get_queryset(self) -> QuerySet:
        """ Returns list of all exams """
        return models.Exam.objects.all()


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
        form = forms.RegistrationForm(request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            try:
                validate_password(user=username, password=password)
            except ValidationError as e:
                return render(request, 'exams/register.html', context={'form': form, 'error_message': e})
            user = models.ApplicationUser.objects.create_user(username=username, password=password)
            user.save()
            return HttpResponseRedirect(reverse('exams:login'))
    else:
        form = forms.RegistrationForm()

    return render(request, 'exams/register.html', {'form': form})


class AppAdminPermissionsCheckMixin:
    def has_permissions(self):
        return self.request.user.is_app_admin

    def dispatch(self, request, *args, **kwargs):
        if not self.has_permissions():
            raise PermissionDenied('This is application admin functionality')
        return super(AppAdminPermissionsCheckMixin, self).dispatch(request, *args, **kwargs)


class ProfileView(generic.DetailView):
    template_name = 'exams/profile.html'
    model = models.ApplicationUser

    def get(self, request, *args, **kwargs):
        exam_history = models.ExamResults.objects.filter(user=request.user).order_by('-taken_on')
        context = {'exam_history': exam_history}
        return render(request, 'exams/profile.html', context=context)


class ExamSetupView(generic.FormView):
    """ View for exam setup """
    template_name = 'exams/exam_setup.html'
    form_class = forms.ExamSetupForm
    question_number = None
    success_url = 'exams:exam_take'

    def get_context_data(self, **kwargs) -> dict:
        exam_id = self.kwargs['exam_id']
        exam = models.Exam.objects.get(id=exam_id)
        context = super().get_context_data(**kwargs)
        context['exam'] = exam
        context['question_number_preconfigs'] = self.get_question_number_preconfigs()
        return context

    @staticmethod
    def get_question_number_preconfigs() -> List:
        """ Returns list of most popular exam question numbers """
        return [5, 10, 20, 30, 50, 'All', 'Custom']

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
        exam_id = int(exam_id)
        exam = models.Exam.objects.get(id=exam_id)
        if request.POST['question_number'] == 'Custom':
            question_quantity = int(request.POST['question_quantity_custom'])
        elif request.POST['question_number'] == 'All':
            question_quantity = exam.question_number
        else:
            question_quantity = int(request.POST['question_quantity'])

        questions = models.Question.objects.filter(exam_id=exam_id)
        total_question_number = questions.count()
        if question_quantity < total_question_number:
            questions = random.sample(list(questions), question_quantity)

        for question in questions:
            question_id = question.id
            answer_variants = models.QuestionVariant.objects.filter(question__id=question_id)
            correct_answers_num = models.QuestionVariant.objects.filter(
                question__id=question_id, is_correct_answer=True).count()
            has_one_correct_answer = correct_answers_num == 1
            question.answer_variants = answer_variants
            question.has_one_correct_answer = has_one_correct_answer

        context = {'exam': exam, 'questions': questions}
        return render(request, 'exams/exam_take.html', context=context)


class ExamResultView(generic.View):
    """ View to get exam results """
    template_name = 'exams/exam_result.html'

    def get(self, request: WSGIRequest, exam_id: str, exam_record_datetime: str) -> HttpResponse:
        """ Return exam results """
        exam = models.Exam.objects.get(id=exam_id)
        exam_record = models.ExamResults.objects.get(exam=exam, unique_id=exam_record_datetime)
        # TODO Check user permissions to access this exam record
        question_records = models.QuestionRecorded.objects.filter(exam_result=exam_record)
        questions = []
        for question_record in question_records:
            question = models.Question.objects.get(id=question_record.question.id)
            is_answer_correct = True
            answer_variants = models.QuestionVariant.objects.filter(question=question)
            for answer_variant in answer_variants:
                answer_record = models.QuestionVariantAnswerRecorded.objects.get(
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
        exam = models.Exam.objects.get(id=exam_id)
        user = models.ApplicationUser.objects.get(id=request.user.id)
        exam_results = models.ExamResults.objects.create(exam=exam, user=user)
        total_questions_in_exam = len(answers)
        questions_with_correct_answers = 0
        for question in models.Question.objects.filter(id__in=answers.keys()):
            question_record = models.QuestionRecorded.objects.create(exam_result=exam_results, question=question)
            is_answer_correct = True
            for answer_variant in models.QuestionVariant.objects.filter(question__id=question.id):
                was_selected = answer_variant.choice_letter in answers[question.id]
                variant_record = models.QuestionVariantAnswerRecorded.objects.create(
                    question_variant=answer_variant, question_recorded=question_record, was_selected=was_selected)
                if answer_variant.is_correct_answer ^ variant_record.was_selected:
                    is_answer_correct = False
            if is_answer_correct:
                questions_with_correct_answers += 1
        exam_results.score = int(questions_with_correct_answers / total_questions_in_exam * 100)
        exam_results.save(update_fields=['score'])
        return redirect(reverse('exams:exam_results', kwargs={'exam_id': exam_id,
                                                              'exam_record_datetime': exam_results.taken_on_as_str}))


class UploadView(AppAdminPermissionsCheckMixin, generic.FormView):
    template_name = 'exams/upload.html'
    form_class = forms.UploadForm
    success_url = reverse_lazy('exams:index')

    def get_form_kwargs(self) -> Dict:
        """ Pass arguments to form within kwargs """
        kwargs = super(UploadView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class QuestionReportCreateView(generic.FormView):
    """ View to create question report """
    template_name = 'exams/question_report_create.html'
    form_class = forms.QuestionReportCreateUpdateForm
    success_url = reverse_lazy('exams:report_history')

    def get_context_data(self, **kwargs) -> Dict:
        """ Adds question object to from context """
        context = super(QuestionReportCreateView, self).get_context_data(**kwargs)
        question_id = self.kwargs.get('question_id')
        question = models.Question.objects.get(id=question_id)
        context['question'] = question
        return context

    def form_valid(self, form) -> HttpResponse:
        """ Save new report """
        report_text = form.cleaned_data.get('report_text')
        question_id = self.kwargs.get('question_id')
        question = models.Question.objects.get(id=question_id)
        models.QuestionReport.objects.create(question=question, reporter=self.request.user, text=report_text)
        return redirect(self.get_success_url())


class QuestionReportViewUser(generic.UpdateView):
    template_name = 'exams/question_report_details_user.html'
    model = models.QuestionReport
    form_class = forms.QuestionReportCreateUpdateForm
    context_object_name = 'report'

    def get_success_url(self):
        """ Redirect to the same page after update """
        return self.request.path


class QuestionReportViewAdmin(AppAdminPermissionsCheckMixin, generic.UpdateView):
    template_name = 'exams/question_report_details_admin.html'
    model = models.QuestionReport
    form_class = forms.QuestionReportUpdateFormAdmin
    context_object_name = 'report'

    def get_success_url(self):
        """ Redirect to the same page after update """
        return self.request.path


class QuestionReportListView(generic.ListView):
    """ View to show current user's reports """
    template_name = 'exams/question_report_list_user.html'
    context_object_name = 'question_reports'

    def get_queryset(self) -> QuerySet:
        """ Return all reports submitted by current user """
        user = self.request.user
        user_reports = models.QuestionReport.objects.filter(reporter=user)
        return user_reports


class QuestionReportListViewAdmin(AppAdminPermissionsCheckMixin, generic.ListView):
    """ View to show all reports to user """
    template_name = 'exams/question_report_list_admin.html'
    context_object_name = 'question_reports'

    def get_queryset(self) -> QuerySet:
        """ Return all reports """
        user_reports = models.QuestionReport.objects.all().order_by(
            Case(When(status=models.QuestionReport.STATUS_NEW, then=Value(0)), default=Value(1))
        )
        return user_reports


class ScoreboardUsers(generic.ListView):
    context_object_name = 'user_stats'
    template_name = 'exams/user_scoreboard.html'

    @dataclass
    class Stats:
        user: models.ApplicationUser
        exams_taken: int
        exams_taken_last_month: int
        exams_taken_last_week: int
        avg_score: float
        avg_question_number: int

    def get_queryset(self) -> List['Stats']:
        """
        Build stats for all non-superadmin and non-appadmin users,
        sort by requested paprameter (from kwargs) and return
        """
        non_admins = models.ApplicationUser.objects.filter(is_app_admin=False)
        user_stats = [self.build_user_stats(user) for user in non_admins]

        sort_by = self.kwargs.get('sort_by', 'avg_score')
        try:
            user_stats = sorted(user_stats, key=lambda user: getattr(user, sort_by))
        except AttributeError:
            user_stats = sorted(user_stats, key=lambda user: getattr(user, 'avg_score'))
        return user_stats

    def build_user_stats(self, user: models.ApplicationUser) -> 'Stats':
        """ Build and return stats for a single user """
        exam_results = models.ExamResults.objects.filter(user=user)
        exam_results = exam_results.annotate(question_num=Count('questionrecorded'))
        date_month_ago = datetime.today() - timedelta(days=30)
        date_week_ago = datetime.today() - timedelta(days=7)
        stats = self.Stats(
            user=user,
            exams_taken=exam_results.count(),
            exams_taken_last_month=exam_results.filter(
                taken_on__lte=datetime.today(), taken_on__gte=date_month_ago).count(),
            exams_taken_last_week=exam_results.filter(
                taken_on__lte=datetime.today(), taken_on__gte=date_week_ago).count(),
            avg_score=exam_results.aggregate(Avg('score'))['score__avg'],
            avg_question_number=exam_results.aggregate(Avg('question_num'))['question_num__avg']
        )
        return stats


def health_check_view(request: WSGIRequest) -> HttpResponse:
    """
    View to for application health check.
    Return 200 response with OK
    """
    return HttpResponse('OK')
