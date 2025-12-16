from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.http import HttpResponse

from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from recipes.filters import IngredientFilter, RecipeFilter
from recipes.models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    Tag,
)
from recipes.serializers import (
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    ShortRecipeSerializer,
    TagSerializer,
)
from users.models import Follow
from users.serializers import (
    SubscriptionSerializer, UserSerializer, AvatarSerializer)

from .permissions import IsAuthorOrReadOnly

User = get_user_model()


class CustomUserViewSet(DjoserUserViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        return super().get_permissions()

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def subscriptions(self, request):
        authors = (
            User.objects
            .filter(following__user=request.user)
            .annotate(recipes_count=Count('recipes'))
        )
        page = self.paginate_queryset(authors)
        serializer = SubscriptionSerializer(
            page,
            many=True,
            context={'request': request},
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, id=None):
        author = self.get_object()
        user = request.user

        if request.method == 'POST':
            if user == author:
                return Response(
                    {'errors': 'Нельзя подписаться на себя.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            follow, created = Follow.objects.get_or_create(
                user=user,
                author=author,
            )
            if not created:
                return Response(
                    {'errors': 'Уже подписаны.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            author = (
                User.objects
                .annotate(recipes_count=Count('recipes'))
                .get(id=author.id)
            )
            serializer = SubscriptionSerializer(
                author,
                context={'request': request},
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted, _ = user.following.filter(author=author).delete()
        if not deleted:
            return Response(
                {'errors': 'Подписки не было.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar',
    )
    def avatar(self, request):
        user = request.user

        if request.method == 'PUT':
            serializer = AvatarSerializer(
                user,
                data=request.data,
                context={'request': request},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        if user.avatar:
            user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filterset_class = IngredientFilter
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('name',)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in ('POST', 'PUT', 'PATCH'):
            return RecipeWriteSerializer
        return RecipeReadSerializer

    def perform_create(self, serializer):
        serializer.save()

    def _add_to(self, related_manager, recipe):
        obj, created = related_manager.get_or_create(recipe=recipe)
        if not created:
            return Response(
                {'errors': 'Уже добавлено.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = ShortRecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _remove_from(self, related_manager, recipe):
        deleted, _ = related_manager.filter(recipe=recipe).delete()
        if not deleted:
            return Response(
                {'errors': 'Не было в списке.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        if request.method == 'POST':
            return self._add_to(request.user.favorites, recipe)
        return self._remove_from(request.user.favorites, recipe)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        if request.method == 'POST':
            return self._add_to(request.user.shopping_cart, recipe)
        return self._remove_from(request.user.shopping_cart, recipe)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        ingredients = (
            RecipeIngredient.objects
            .filter(recipe__in_carts__user=request.user)
            .values(
                'ingredient__name',
                'ingredient__measurement_unit',
            )
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredient__name')
        )

        if not ingredients:
            return Response(
                {'errors': 'Список покупок пуст.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        lines = [
            f"{item['ingredient__name']} "
            f"({item['ingredient__measurement_unit']}) — "
            f"{item['total_amount']}"
            for item in ingredients
        ]
        content = '\n'.join(lines)

        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response
