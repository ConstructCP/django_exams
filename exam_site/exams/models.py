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

    def __str__(self) -> str:
        return str(self.title)


class Question(models.Model):
    """ Model for question_json in an exam """
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    title = models.CharField(max_length=1000)
    text = models.CharField(max_length=5000)
    answer_explanation = models.CharField(max_length=5000)

    def __str__(self) -> str:
        return str(self.title)


class QuestionVariant(models.Model):
    """ Model for answer variant for exam question_json """
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_letter = models.CharField(max_length=1)
    text = models.CharField(max_length=1000)
    is_correct_answer = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f'{self.choice_letter}. {self.text}'
