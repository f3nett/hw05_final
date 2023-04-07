import math

from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User

GROUP_POST_COUNT = 12
PROFILE_POST_COUNT = 13


class PaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост без группы',
        )
        Post.objects.bulk_create(
            Post(
                author=cls.user,
                text=f'Тестовый пост {i} с группой',
                group=cls.group,
            ) for i in range(GROUP_POST_COUNT)
        )
        cls.paginator_urls = {
            reverse('posts:index'): Post.objects.count(),
            reverse(
                'posts:profile', kwargs={'username': cls.user.username}
            ): PROFILE_POST_COUNT,
            reverse(
                'posts:group_list', kwargs={'slug': cls.group.slug}
            ): GROUP_POST_COUNT
        }

    def setUp(self):
        self.client = Client()

    def test_paginator_returns(self):
        """Пагинатор возвращает правильное количество постов."""
        for url, url_posts_count in self.paginator_urls.items():
            with self.subTest(url=url):
                paginator_page_count = math.ceil(
                    url_posts_count / settings.POSTS_COUNT
                )
                page = 1
                while page <= paginator_page_count:
                    response = self.client.get(
                        url + f'?page={page}'
                    )
                    if page == paginator_page_count:
                        self.assertEqual(
                            len(response.context['page_obj']),
                            url_posts_count % settings.POSTS_COUNT,
                            'Пагинатор возвращает не верное количество постов'
                        )
                    else:
                        self.assertEqual(
                            len(response.context['page_obj']),
                            settings.POSTS_COUNT,
                            'Пагинатор возвращает не верное количество постов'
                        )
                    page += 1
