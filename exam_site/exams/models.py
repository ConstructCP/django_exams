from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models


class ApplicationUserManager(BaseUserManager):
    def create_user(self, username, password=None):
        if not username or not password:
            raise ValueError('Both username and password must be provided.')
        user = self.model(username=username)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None):
        user = self.create_user(username=username, password=password)
        user.is_admin = True
        user.save(using=self._db)
        return user


class ApplicationUser(AbstractBaseUser):
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    USERNAME_FIELD = 'username'
    objects = ApplicationUserManager()

    def __str__(self):
        return self.username + '_' + self.password

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return self.is_admin

    @property
    def is_staff(self):
        return self.is_admin


