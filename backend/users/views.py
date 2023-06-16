from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.serializers import FollowSerializer

from .models import Follow, User
from .serializers import (CustomUserSerializer,
                          CreateUserSerializer)


class CustomUserViewSet(UserViewSet):
    '''Вьюсет для юзеров и подписок. '''
    queryset = User.objects.all()
    permission_classes = (IsAuthenticated, )

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateUserSerializer
        return CustomUserSerializer

    @action(detail=True, methods=['POST', 'DELETE'],
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, **kwargs):
        user = self.request.user
        pk = kwargs.get('id',)
        author = get_object_or_404(User, pk=pk)
        if request.method == 'POST':
            serializer = FollowSerializer(author, data=request.data,
                                          context={'request': request})
            if serializer.is_valid():
                follow = Follow.objects.create(user=user, author=author)
                follow.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        if request.method == 'DELETE':
            subscription = get_object_or_404(Follow, user=user, author=author)
            subscription.delete()
            response_data = {'message': 'Пользователь успешно удален.',
                             'deleted_user': {'id': author.id,
                                              'username': author.username}}
            return Response(response_data, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=('GET',),
            permission_classes=(IsAuthenticated,))
    def subscriptions(self, request, *args, **kwargs):
        user = request.user
        queryset = User.objects.filter(following__user=user)
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(pages, many=True,
                                      context={'request': request})
        return self.get_paginated_response(serializer.data)
