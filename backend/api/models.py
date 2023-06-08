from django.contrib.auth import get_user_model
from django.core import validators
from django.db import models

User = get_user_model()


class Ingredient(models.Model):
    ''' Модель ингредиента. '''
    name = models.CharField(
        verbose_name='Название ингредиента',
        max_length=200)
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=200)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name']
        constraints = [models.UniqueConstraint(
            fields=('name', 'measurement_unit'),
            name='unique_ingredient')]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}.'


class Tag(models.Model):
    ''' Модель тега. '''
    name = models.CharField(
        verbose_name='Название тега',
        unique=True,
        max_length=200)
    color = models.CharField(
        verbose_name='Цветовой HEX-код',
        max_length=7,
        unique=True)
    slug = models.SlugField(
        verbose_name='Уникальный слаг',
        max_length=200,
        unique=True)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['name']

    def __str__(self):
        return self.name


class Recipe(models.Model):
    '''Модель рецепта.'''
    author = models.ForeignKey(
        User,
        verbose_name='Автор рецепта',
        related_name='recipes',
        on_delete=models.CASCADE)
    name = models.CharField(
        verbose_name='Название рецепта',
        max_length=200)
    text = models.TextField(
        verbose_name='Описание рецепта',
        help_text='Введите описание рецепта')
    image = models.ImageField(
        verbose_name='Картинка рецепта',
        upload_to='recipes/')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientsInRecipe',
        verbose_name='Ингридиенты',
        related_name='recipes')
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги')
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        validators=(
            validators.MinValueValidator(
                1, message='Минимальное время приготовления 1 минута'),),)
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True)

    class Meta:
        ordering = ['-id']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class IngredientsInRecipe(models.Model):
    ''' Модель связи ингредиента и рецепта. '''
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe',
        verbose_name='Рецепт')
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='Ингредиент',
        related_name='ingredient',
        on_delete=models.CASCADE)
    amount = models.PositiveSmallIntegerField(
        validators=(
            validators.MinValueValidator(
                1, message='Минимальное количество ингридиентов 1'),),
        verbose_name='Количество',)

    class Meta:
        ordering = ['-id']
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='recipe_ingredient')]


class Favourite(models.Model):
    '''Модель избранных рецептов.'''
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='favorites')
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='favorites')

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favourites')]


class ShoppingCart(models.Model):
    ''' Модель корзины. '''
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='shopping_cart')
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='shopping_cart')

    class Meta:
        ordering = ['-id']
        verbose_name = 'Рецепт в корзине'
        verbose_name_plural = 'Реценты в корзине'
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='unique_shopping_cart')]
