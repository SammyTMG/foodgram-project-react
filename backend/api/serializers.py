from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from rest_framework.exceptions import ValidationError
from rest_framework.fields import (IntegerField,
                                   SerializerMethodField,
                                   ReadOnlyField)
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer

from users.serializers import CustomUserSerializer
from users.models import Follow
from .models import (Tag, Ingredient, Favourite,
                     IngredientsInRecipe, Recipe,
                     ShoppingCart)


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
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return (Favourite.objects.filter(user=request.user, recipe=obj)
                .exists())

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return (ShoppingCart.objects.filter(user=request.user, recipe=obj)
                .exists())


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
        fields = '__all__'

    def validate_ingredients(self, value):
        ingredients = value
        if not ingredients:
            raise ValidationError({
                'ingredients': 'Должен присутствовать хотя бы один ингредиент!'
            })
        ingredients_list = []
        for i in ingredients:
            ingredient = get_object_or_404(Ingredient, id=i['id'])
            if ingredient in ingredients_list:
                raise ValidationError({
                    'ingredients': 'Ингредиенты должны быть уникальными!'
                })
            ingredients_list.append(ingredient)
        return value

    def validate_tags(self, value):
        tags = value
        if not tags:
            raise ValidationError({
                'tags': 'Нужен хотя бы один тэг для рецепта!'})
        tags_list = []
        for tag in tags:
            if tag in tags_list:
                raise ValidationError({
                    'tags': 'Теги должны быть уникальными!'})
            tags_list.append(tag)
        return value

    def create_ingredients(self, ingredients, recipe):
        for i in ingredients:
            ingredient = Ingredient.objects.get(id=i['id'])
            IngredientsInRecipe.objects.create(
                ingredient=ingredient, recipe=recipe, amount=i['amount']
            )

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
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
        if Follow.objects.filter(author=author, user=user).exists():
            raise ValidationError(
                'Вы уже подписаны на этого пользователя!')
        if user == author:
            raise ValidationError(
                'Нельзя подписываться на себя')
        return data

    def get_recipes_count(self, obj):
        return obj.recipes.count()

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
        if Favourite.objects.filter(user=user, recipe=recipe).exists():
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
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise ValidationError('Рецепт уже добавлен в корзину.')
        return obj
