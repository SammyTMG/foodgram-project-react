from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import UniqueConstraint


class User(AbstractUser):
    '''Модель пользователя.'''
    email = models.EmailField('Email',
                              max_length=200,
                              unique=True,)
    first_name = models.CharField('Имя',
                                  max_length=150)
    last_name = models.CharField('Фамилия',
                                 max_length=150)

    class Meta:
        ordering = ['id']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'#{self.id}-{self.username}'


class Follow(models.Model):
    '''Модель подписок.'''
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             verbose_name='Подписчик',
                             related_name='follower',)
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               verbose_name='Автор',
                               related_name='following',)

    class Meta:
        ordering = ['-id']
        constraints = [UniqueConstraint(
            fields=['user', 'author'],
            name='unique_follow'), ]

    def __str__(self):
        return f'Пользователь {self.user} - автор {self.author}'
