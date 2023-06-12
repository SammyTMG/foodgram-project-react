from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.pagination import LimitPageNumberPagination
from api.serializers import FollowSerializer
from .serializers import CustomUserSerializer
from .models import User, Follow


class CustomUserViewSet(UserViewSet):
    '''Вьюсет для юзеров и подписок. '''
    serializer_class = CustomUserSerializer
    pagination_class = LimitPageNumberPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return User.objects.all()

    @action(detail=True, methods=['POST', 'DELETE'])
    def subscribe(self, request, **kwargs):
        user = request.user
        author_id = self.kwargs.get('id')
        author = get_object_or_404(User, id=author_id)

        if request.method == 'POST':
            serializer = FollowSerializer(author, data=request.data,
                                          context={'request': request})
            serializer.is_valid(raise_exception=True)
            Follow.objects.create(user=user, author=author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            subscription = get_object_or_404(Follow, user=user, author=author)
            subscription.delete()
            response_data = {'message': 'Пользователь успешно удален.',
                             'deleted_user': {'id': author.id,
                                              'username': author.username}}
            return Response(response_data, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False)
    def subscriptions(self, request):
        user = request.user
        queryset = User.objects.filter(following__user=user)
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(pages, many=True,
                                      context={'request': request})
        return self.get_paginated_response(serializer.data)
