from django.test import TestCase
from django.urls import reverse

from .models import ApplicationUser, Exam, Question, QuestionVariant


def create_exam(title):
    return Exam.objects.create(title=title)


def create_user(username, password):
    user = ApplicationUser(username=username, password=password)
    user.save()
    return user


class IndexViewTests(TestCase):

    def test_index_no_exams(self):
        response = self.client.get(reverse('exams:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No exams are available.')
        self.assertQuerysetEqual(response.context['exam_list'], [])

    def test_index_with_exams(self):
        exam1 = create_exam('test_exam1')
        exam2 = create_exam('test_exam2')
        response = self.client.get(reverse('exams:index'))
        self.assertQuerysetEqual(response.context['exam_list'], [exam1, exam2], ordered=False)


class RegistrationViewTests(TestCase):
    def test_invalid_password(self):
        username = 'test_user'
        passwords = {'skvf9': 'This password is too short. It must contain at least 6 characters.',
                     'qwerty': 'This password is too common.',
                     '197462025': 'This password is entirely numeric.'}
        for password, error in passwords.items():
            response = self.client.post(reverse('exams:register'), data={'username': username, 'password': password})
            self.assertContains(response, error)

    def test_valid_password(self):
        username = 'test_auth_user'
        password = 'aif76sdvpg86dop'
        response = self.client.post(reverse('exams:register'), data={'username': username, 'password': password})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/exams/login/')
        response = self.client.post(reverse('exams:login'), data={'username': username, 'password': password})
        self.assertEqual(response.wsgi_request.user.username, username)


class LoginLogoutViewTests(TestCase):
    def test_plain_get(self):
        response = self.client.get(reverse('exams:login'))
        self.assertEqual(response.status_code, 200)

    def test_invalid_user(self):
        response = self.client.post(reverse('exams:login'), data={'username': 'test_user_invalid', 'password': '12345'})
        self.assertContains(response, 'Please enter a correct username and password. '
                                      'Note that both fields may be case-sensitive.')

    def test_valid_user(self):
        username = 'test_login_user'
        password = 'aif76sdvpg86dop'
        response = self.client.post(reverse('exams:register'), data={'username': username, 'password': password})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/exams/login/')
        response = self.client.post(reverse('exams:login'), data={'username': username, 'password': password})
        self.assertEqual(response.wsgi_request.user.username, username)

    def test_logout(self):
        username = 'test_login_user'
        password = 'aif76sdvpg86dop'
        response = self.client.post(reverse('exams:register'), data={'username': username, 'password': password})
        response = self.client.post(reverse('exams:login'), data={'username': username, 'password': password})
        response = self.client.post(reverse('exams:logout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/exams/login/')
