from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
from django.utils import timezone
import random, uuid
import string

from django.contrib.auth.models import BaseUserManager
import random
import string

class UserManager(BaseUserManager):
    def create_user(self, email, first_name=None, last_name=None, username=None, password=None, phone_number=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        if not username:
            raise ValueError('User must have a username')

        user = self.model(
            email=self.normalize_email(email),
            first_name=first_name or '',  # Ensure first_name defaults to an empty string
            last_name=last_name or '',    # Ensure last_name defaults to an empty string
            username=username,
            phone_number=phone_number,  # Include phone_number
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)


        return user

    def create_superuser(self, email, first_name=None, last_name=None, username=None, password=None, phone_number=None, **extra_fields):
        user = self.create_user(
            email=self.normalize_email(email),
            first_name=first_name,
            last_name=last_name,
            username=username,
            password=password,
            phone_number=phone_number,
            **extra_fields
        )
        user.is_admin = True
        user.is_staff = True
        user.is_superadmin = True
        user.is_active = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(max_length=100, unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    verified = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)

    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    is_superadmin = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    objects = UserManager()

    groups = models.ManyToManyField(Group, blank=True, related_name='account_user_groups')
    user_permissions = models.ManyToManyField(Permission, blank=True, related_name='account_user_permissions')

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True
    
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    dp_img = models.ImageField(upload_to='image', blank=True, null=True)
    bio = models.CharField(max_length=220, blank=True, null=True)

    def __str__(self):
        return f"Profile of {self.user.username}"
    
class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.Cascade)
    street_address = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=100)
    coutry = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.street_address}, {self.city}, {self.state} - {self.postal_code}"