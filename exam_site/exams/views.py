from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import QuerySet
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.views import generic

from .forms import RegistrationForm
from .models import ApplicationUser, Exam, Question, QuestionVariant


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


class ExamView(generic.TemplateView):
    """ View for exam """
    template_name = 'exams/exam.html'

    def get_context_data(self, **kwargs) -> dict:
        """
        Returns context for template with exam and question of this exam.
        Adds to each question
            - answer variants
            - boolean indicating whether number of correct answers is 1 or more
        """
        exam_id = self.kwargs['exam_id']
        exam = Exam.objects.get(id=exam_id)
        questions = Question.objects.filter(exam__id=exam_id)
        for question in questions:
            question_id = question.id
            answer_variants = QuestionVariant.objects.filter(question__id=question_id)
            has_one_correct_answer = QuestionVariant.objects.filter(question__id=question_id, is_correct_answer=True).count() == 1
            question.answer_variants = answer_variants
            question.has_one_correct_answer = has_one_correct_answer

        context = super().get_context_data(**kwargs)
        context['exam'] = exam
        context['questions'] = questions
        return context


def exam_result(request: WSGIRequest, exam_id: int) -> HttpResponse:
    """
    View for exam results.
    Returns context for template with exam, question of this exam and exam score.
    Adds to each question:
        - answer variants
        - answers provided by the user
        - boolean indicating whether number of correct answers is 1 or more
        - boolean indicating whether user's answers were correct
    """
    exam = Exam.objects.get(id=exam_id)
    questions = Question.objects.filter(exam__id=exam_id)
    number_of_correct_answers = 0
    for question in questions:
        question_id = question.id
        answer_variants = QuestionVariant.objects.filter(question__id=question_id)
        given_answers = request.POST.getlist(str(question.id))
        answered_correctly = True
        for answer_variant in answer_variants:
            answer_variant.was_chosen = answer_variant.choice_letter in given_answers
            if ((answer_variant.was_chosen and not answer_variant.is_correct_answer) or
                    (not answer_variant.was_chosen and answer_variant.is_correct_answer)):
                answered_correctly = False
        if answered_correctly:
            number_of_correct_answers += 1
            question.answered_correctly = True
        else:
            question.answered_correctly = False
        question.answer_variants = answer_variants
        question.given_answers = given_answers
        question.has_one_correct_answer = QuestionVariant.objects.filter(
            question__id=question_id, is_correct_answer=True
        ).count() == 1

    score = number_of_correct_answers / len(questions)
    score_percent = int(score * 100)
    context = {'exam': exam, 'questions': questions, 'score': score_percent}
    return render(request, 'exams/exam_results.html', context=context)
