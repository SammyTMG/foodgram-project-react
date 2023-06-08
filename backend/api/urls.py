from django.urls import include, path
from rest_framework.routers import DefaultRouter


from .views import TagViewSet, IngredientsViewSet, RecipeViewSet

app_name = 'api'

router_v1 = DefaultRouter()
router_v1.register('tags', TagViewSet)
router_v1.register('ingredients', IngredientsViewSet)
router_v1.register('recipes', RecipeViewSet)

urlpatterns = [
    path('', include(router_v1.urls)),
]
