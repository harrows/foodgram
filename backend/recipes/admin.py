from django.contrib import admin
from django.db.models import Count

from .models import (
    Favorite, Ingredient, Recipe, RecipeIngredient,
    ShoppingCart, Tag,
)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'color')
    search_fields = ('name', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author', 'favorites_count')
    list_filter = ('author', 'tags')
    search_fields = ('name', 'author__username')
    inlines = (RecipeIngredientInline,)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_favorites_count=Count('favorite_for'))

    @admin.display(description='В избранном')
    def favorites_count(self, obj):
        return obj._favorites_count


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
