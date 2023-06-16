from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers

from .models import Follow, User


class CreateUserSerializer(UserCreateSerializer):
    '''Сериализатор создания пользователя'''
    password = serializers.CharField(style={'input_type': 'password'},
                                     label='Пароль',
                                     write_only=True)

    class Meta:
        model = User
        fields = ('email',
                  'id',
                  'username',
                  'first_name',
                  'last_name',
                  'password',)
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
            'password': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }


class CustomUserSerializer(UserSerializer):
    '''Сериализатор показа пользователей'''
    is_subscribed = serializers.BooleanField(default=False)

    class Meta:
        model = User
        fields = ('email',
                  'id',
                  'username',
                  'first_name',
                  'last_name',
                  'is_subscribed',)
