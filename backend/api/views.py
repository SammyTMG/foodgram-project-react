import io

from django.db.models.aggregates import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from .filters import IngredientFilter, RecipeFilter
from .models import Favourite, Ingredient, Recipe, ShoppingCart, Tag
from .pagination import LimitPageNumberPagination
from .permissions import IsAdminOrReadOnly, IsAuthorOrReadOnly
from .serializers import (CreateRecipeSerializer, FavouriteSerializer,
                          IngredientSerializer, ReadRecipeSerializer,
                          ShoppingCartSerializer, TagSerializer)


class TagViewSet(ReadOnlyModelViewSet):
    '''Вьюсет для тегов.'''
    permission_classes = (IsAdminOrReadOnly,)
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientsViewSet(ReadOnlyModelViewSet):
    '''Вьюсет для ингредиентов.'''
    permission_classes = (IsAdminOrReadOnly,)
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (IngredientFilter,)
    search_fields = ('^name',)


class RecipeViewSet(ModelViewSet):
    '''Вьюсет для рецептов/избранное/корзина/скачивание корзины.'''
    permission_classes = (IsAuthorOrReadOnly | IsAdminOrReadOnly,)
    queryset = Recipe.objects.all()
    pagination_class = LimitPageNumberPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ReadRecipeSerializer
        return CreateRecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post'],
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, **kwargs):
        user = self.request.user
        recipe = get_object_or_404(Recipe, **kwargs)
        serializer = FavouriteSerializer(recipe, data=request.data,
                                         context={'request': request})
        serializer.is_valid(raise_exception=True)
        Favourite.objects.create(user=user, recipe=recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def del_favorite(self, request, **kwargs):
        user = self.request.user
        recipe = get_object_or_404(Recipe, **kwargs)
        get_object_or_404(Favourite, user=user,
                          recipe=recipe).delete()
        response_data = {'message': 'Рецепт удален из корзины.',
                         'deleted_recipe': {'id': recipe.id,
                                            'name': recipe.name,
                                            'author': user.username}}
        return Response(response_data,
                        status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'],
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk):
        user = self.request.user
        recipe = get_object_or_404(Recipe, id=pk)
        serializer = ShoppingCartSerializer(recipe,
                                            data={'user': request.user.id,
                                                  'recipe': recipe.id},
                                            context={'request': request})
        serializer.is_valid(raise_exception=True)
        ShoppingCart.objects.create(user=user, recipe=recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def del_shopping_cart(self, request, pk):
        user = self.request.user
        recipe = get_object_or_404(Recipe, id=pk)
        get_object_or_404(ShoppingCart, user=user,
                          recipe=recipe).delete()
        return Response('Рецепт удален',
                        status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'],
            permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        buffer = io.BytesIO()
        page = canvas.Canvas(buffer)
        pdfmetrics.registerFont(TTFont('arial', 'fronts/arial.ttf'))
        user = request.user
        if not user.shopping_cart.exists():
            return Response('Корзина пуста',
                            status=status.HTTP_400_BAD_REQUEST)
        ingredient_name = 'recipe__recipe__ingredient__name'
        ingredient_unit = 'recipe__recipe__ingredient__measurement_unit'
        recipe_amount = 'recipe__recipe__amount'
        amount_sum = 'recipe__recipe__amount__sum'
        shopping_cart = user.shopping_cart.select_related('recipe').values(
            ingredient_name, ingredient_unit
        ).annotate(Sum(recipe_amount)).order_by(ingredient_name)
        page.setFont('arial', 14)
        x_position, y_position = 50, 800
        if shopping_cart:
            page.drawString(x_position, y_position, 'Cписок покупок:')
            for num, recipe in enumerate(shopping_cart, start=1):
                page.drawString(
                    x_position, y_position - 20,
                    f'{num}. {recipe[ingredient_name]}: '
                    f'{recipe[amount_sum]} '
                    f'{recipe[ingredient_unit]}.')
                y_position -= 15
        page.save()
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True,
                            filename='shopping_cart.pdf')
