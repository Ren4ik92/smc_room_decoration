from django.contrib.auth.models import AbstractUser, Permission, Group, PermissionsMixin
from django.db import models


class MyUser(AbstractUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('moder', 'Moderator'),
    )
    username = models.CharField(
        max_length=150,
        unique=True,
    )
    email = models.EmailField(max_length=255, unique=True, blank=False)
    first_name = models.CharField(
        max_length=150,
    )
    last_name = models.CharField(
        max_length=150,
    )
    is_active = models.BooleanField(default=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user', verbose_name='Роль')

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username