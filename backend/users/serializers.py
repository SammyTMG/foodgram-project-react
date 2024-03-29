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
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('email',
                  'id',
                  'username',
                  'first_name',
                  'last_name',
                  'is_subscribed',)

    def get_is_subscribed(self, obj):
        user_id = obj.id
        request_user = self.context.get('request').user.id
        return Follow.objects.filter(author=user_id,
                                     user=request_user).exists()
