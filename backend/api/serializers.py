from django.db import transaction
from django.db.models import Count
from drf_extra_fields.fields import Base64ImageField
from rest_framework.exceptions import ValidationError
from rest_framework.fields import (IntegerField, ReadOnlyField,
                                   SerializerMethodField)
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer

from users.serializers import CustomUserSerializer

from .models import Ingredient, IngredientsInRecipe, Recipe, Tag


class TagSerializer(ModelSerializer):
    '''Сериализатор показа Тегов.'''
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(ModelSerializer):
    '''Сериализатор показа Ингредиентов.'''
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientsInRecipeSerializer(ModelSerializer):
    '''Сериализатор, соединяющий ингредиенты и рецепты.'''
    id = ReadOnlyField(source='ingredient.id')
    name = ReadOnlyField(source='ingredient.name')
    measurement_unit = ReadOnlyField(source='ingredient.measurement_unit')

    class Meta:
        model = IngredientsInRecipe
        fields = ('id',
                  'name',
                  'measurement_unit',
                  'amount')


class ReadRecipeSerializer(ModelSerializer):
    '''Сериализатор для чтения рецептов (GET).'''
    tags = TagSerializer(read_only=True, many=True)
    ingredients = SerializerMethodField()
    author = CustomUserSerializer(read_only=True)
    image = Base64ImageField()
    is_favorited = SerializerMethodField(read_only=True)
    is_in_shopping_cart = SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id',
                  'tags',
                  'author',
                  'ingredients',
                  'is_favorited',
                  'is_in_shopping_cart',
                  'name',
                  'image',
                  'text',
                  'cooking_time')

    def get_ingredients(self, obj):
        ingredients = IngredientsInRecipe.objects.filter(recipe=obj)
        return IngredientsInRecipeSerializer(ingredients, many=True).data

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        return Recipe.objects.filter(favorite__user=user,
                                     id=obj.id).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        return user.shopping_cart.filter(recipe=obj.id).exists()


class AddIngredientInRecipeSerializer(ModelSerializer):
    '''Сериализатор для добавления ингредиента.'''

    id = IntegerField()
    amount = IntegerField()

    class Meta:
        model = IngredientsInRecipe
        fields = ('id',
                  'amount')


class CreateRecipeSerializer(ModelSerializer):
    '''Сериализатор для создания рецептов.'''
    tags = PrimaryKeyRelatedField(queryset=Tag.objects.all(),
                                  many=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = AddIngredientInRecipeSerializer(many=True)
    image = Base64ImageField(max_length=None,
                             use_url=True)

    class Meta:
        model = Recipe
        fields = ('id',
                  'tags',
                  'author',
                  'ingredients',
                  'name',
                  'image',
                  'text',
                  'cooking_time')

    def validate_ingredients(self, value):
        if not value:
            raise ValidationError(
                'Должен присутствовать хотя бы один ингредиент!')
        ingredients_list = []
        for i in value:
            if i['id'] in ingredients_list:
                raise ValidationError(
                    'Ингредиенты должны быть уникальными!')
            ingredients_list.append(i['id'])
            if int(i['amount']) <= 0:
                raise ValidationError(
                    'Количество не может быть меньше 1!')
            return value

    def validate_tags(self, data):
        tags_list = []
        for tag in data:
            if not tag:
                raise ValidationError(
                    'Нужен хотя бы один тэг для рецепта!')
            if tag in tags_list:
                raise ValidationError(
                    'Теги должны быть уникальными!')
            tags_list.append(tag)
        return data

    def create_ingredients(self, ingredients, recipe):
        recipe_ingredients = []
        for ingredient in ingredients:
            recipe_ingredients.append(
                IngredientsInRecipe(recipe=recipe,
                                    ingredient_id=ingredient.get('id'),
                                    amount=ingredient.get('amount')))
        IngredientsInRecipe.objects.bulk_create(recipe_ingredients)

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.image = validated_data.get('image', instance.image)
        tags = validated_data.pop('tags')
        instance.tags.clear()
        IngredientsInRecipe.objects.filter(recipe=instance).all().delete()
        instance.tags.set(tags)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get('cooking_time',
                                                   instance.cooking_time)
        self.create_ingredients(ingredients=validated_data.get('ingredients'),
                                recipe=instance)
        instance.save()
        return instance

    def to_representation(self, instance):
        return ReadRecipeSerializer(instance, context={
            'request': self.context.get('request')}).data


class ShortRecipeSerializer(ModelSerializer):
    '''Сериализатор короткой версии рецептов.'''
    class Meta:
        model = Recipe
        fields = ('id',
                  'name',
                  'image',
                  'cooking_time')
        read_only_fields = ('id',
                            'name',
                            'image',
                            'cooking_time')


class FollowSerializer(CustomUserSerializer):
    '''Сериализатор для подписок.'''
    recipes = SerializerMethodField()
    recipes_count = SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        fields = ('email',
                  'id',
                  'username',
                  'first_name',
                  'last_name',
                  'is_subscribed',
                  'recipes',
                  'recipes_count')
        read_only_fields = ('email',
                            'username',
                            'first_name',
                            'last_name',)

    def validate(self, data):
        author = self.instance
        user = self.context.get('request').user
        if user.follower.filter(author=author).exists():
            raise ValidationError(
                'Вы уже подписаны на этого пользователя!')
        if user == author:
            raise ValidationError(
                'Нельзя подписываться на себя')
        return data

    def get_recipes_count(self, obj):
        amount = (obj.recipes.aggregate(count=Count('id')))
        return amount['count']

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        serializer = ShortRecipeSerializer(recipes, many=True, read_only=True)
        return serializer.data


class FavouriteSerializer(ModelSerializer):
    '''Сериализатор для избранного.'''
    class Meta:
        model = Recipe
        fields = ('id',
                  'name',
                  'image',
                  'cooking_time')
        read_only_fields = ('id',
                            'name',
                            'image',
                            'cooking_time')

    def validate(self, obj):
        recipe = self.instance
        user = self.context['request'].user
        if recipe.favorites.filter(user=user).exists():
            raise ValidationError('Рецепт уже добавлен в избранное.')
        return obj


class ShoppingCartSerializer(ModelSerializer):
    '''Сериализатор для корзины.'''
    class Meta:
        model = Recipe
        fields = ('id',
                  'name',
                  'image',
                  'cooking_time')
        read_only_fields = ('id',
                            'name',
                            'image',
                            'cooking_time')

    def validate(self, obj):
        recipe = self.instance
        user = self.context['request'].user
        if recipe.shopping_cart.filter(user=user).exists():
            raise ValidationError('Рецепт уже добавлен в корзину.')
        return obj
