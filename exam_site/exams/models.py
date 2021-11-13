from datetime import datetime

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models


class ApplicationUserManager(BaseUserManager):
    """ Class that manages user creation """

    def create_user(self, username: str, password: str = None) -> 'ApplicationUser':
        """ Creates usual application user """
        if not username or not password:
            raise ValueError('Both username and password must be provided.')
        user = self.model(username=username)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username: str, password: str = None) -> 'ApplicationUser':
        """ Creates admin user """
        user = self.create_user(username=username, password=password)
        user.is_admin = True
        user.save(using=self._db)
        return user


class ApplicationUser(AbstractBaseUser):
    """ Model for user of the application """
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    USERNAME_FIELD = 'username'
    objects = ApplicationUserManager()

    def __str__(self) -> str:
        return str(self.username)

    def has_perm(self, perm, obj=None) -> bool:
        """ User permission check. Disallow everything for usual user, allow everything to admin """
        return self.is_admin

    def has_module_perms(self, app_label) -> bool:
        """
        User permission to access models in the app.
        Disallow everything for usual user, allow everything to admin
        """
        return self.is_admin

    @property
    def is_staff(self) -> bool:
        """ is_staff is added for support of some Django basic operations, which check it """
        return self.is_admin


class Exam(models.Model):
    """ Model for exam """
    title = models.CharField(max_length=200)
    source = models.CharField(max_length=200, blank=True)
    is_user_uploaded = models.BooleanField(default=False)
    uploader = models.CharField(max_length=200, blank=True)

    def __str__(self) -> str:
        return str(self.title)

    @property
    def question_number(self) -> int:
        """ Returns number of questions in exam """
        return Question.objects.filter(exam=self).count()



class CustomDateTimeField(models.DateTimeField):
    def value_to_string(self, obj):
        val = self.value_from_object(obj)
        if val:
            val.replace(microsecond=0)
            return val.isoformat('%Y-%m-%d_%H-%M-%S')
        return ''


class ExamResults(models.Model):
    """ Model to save exam results in """
    unique_id = models.CharField(max_length=100)
    exam = models.ForeignKey(Exam, on_delete=models.DO_NOTHING)
    user = models.ForeignKey(ApplicationUser, on_delete=models.DO_NOTHING)
    taken_on = CustomDateTimeField(unique=True)
    score = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.exam.title} / user {self.user.username} ({self.taken_on})'

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.taken_on = datetime.now()
            self.unique_id = self.taken_on_as_str
        super().save(*args, **kwargs)

    @property
    def taken_on_as_str(self):
        return str(self.user) + '_' + str(self.taken_on.strftime('%Y-%M-%d_%H-%M-%S'))


class Question(models.Model):
    """ Model for single question in an exam """
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    title = models.CharField(max_length=1000)
    text = models.CharField(max_length=5000)
    answer_explanation = models.CharField(max_length=5000)
    has_one_correct_answer = models.BooleanField(default=False)

    def __str__(self) -> str:
        return str(self.title)


class QuestionRecorded(models.Model):
    """ Model for storing questions from taken exam for exam history """
    exam_result = models.ForeignKey(ExamResults, on_delete=models.DO_NOTHING)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.question} / {self.exam_result}'


class QuestionVariant(models.Model):
    """ Model for answer variant for exam question_json """
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_letter = models.CharField(max_length=1)
    text = models.CharField(max_length=1000)
    is_correct_answer = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f'{self.choice_letter}. {self.text}'


class QuestionVariantAnswerRecorded(models.Model):
    """ Model for storing chosen answer variants for exam history """
    question_variant = models.ForeignKey(QuestionVariant, on_delete=models.DO_NOTHING)
    question_recorded = models.ForeignKey(QuestionRecorded, on_delete=models.DO_NOTHING)
    was_selected = models.BooleanField()

    def __str__(self):
        return f'{self.question_variant} / {self.question_recorded}'
