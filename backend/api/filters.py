from django_filters.rest_framework import FilterSet, filters
from rest_framework.filters import SearchFilter

from users.models import User
from .models import Recipe


class IngredientFilter(SearchFilter):
    '''Фильтр для ингредиентов.'''
    search_param = 'name'


class RecipeFilter(FilterSet):
    '''Фильтр для рецептов.'''
    author = filters.ModelChoiceFilter(queryset=User.objects.all())
    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = filters.BooleanFilter(method='filter_favorited',
                                         label='В избранном')
    is_in_shopping_cart = filters.BooleanFilter(method='filter_shopping_cart',
                                                label='В корзине')

    class Meta:
        model = Recipe
        fields = ('tags',
                  'author',
                  'is_favorited',
                  'is_in_shopping_cart',)

    def filter_favorited(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorites__user=user)
        return queryset

    def filter_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(shopping_cart__user=user)
        return queryset
