from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post, User


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.author = User.objects.create_user(username='Author')
        cls.post = Post.objects.create(
            author=cls.author,
            text='Пост для тестирования',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache(self):
        """Кеширование на странице index работает корректно."""
        start_content = self.authorized_client.get(
            reverse('posts:index')
        ).content
        self.post.delete()
        content_after_delete_post = self.authorized_client.get(
            reverse('posts:index')
        ).content
        cache.clear()
        content_after_cache_clear = self.authorized_client.get(
            reverse('posts:index')
        ).content
        self.assertEqual(
            start_content,
            content_after_delete_post,
            'Отсутствует кеширование страницы'
        )
        self.assertNotEqual(
            start_content,
            content_after_cache_clear,
            'Кеширование страницы работает некорректно'
        )
