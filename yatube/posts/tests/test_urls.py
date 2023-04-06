from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_user = User.objects.create_user(username='HasNoName1')
        cls.another_user = User.objects.create_user(username='HasNoName2')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author_user,
            text='Пост для тестирования',
        )
        cls.puplic_urls = [
            '/',
            f'/group/{cls.group.slug}/',
            f'/profile/{cls.author_user.username}/',
            f'/posts/{cls.post.pk}/',
        ]
        cls.private_urls_for_guest = {
            '/create/': reverse('users:login') + '?next=/create/',
            f'/posts/{cls.post.pk}/edit/':
            reverse('users:login') + f'?next=/posts/{cls.post.pk}/edit/',
            f'/posts/{cls.post.pk}/comment/':
            reverse('users:login') + f'?next=/posts/{cls.post.pk}/comment/',
            f'/profile/{cls.author_user.username}/follow/':
            reverse('users:login')
            + f'?next=/profile/{cls.author_user.username}/follow/',
            '/follow/': reverse('users:login') + '?next=/follow/',
        }
        cls.private_urls_for_user = {
            '/create/': False,
            '/follow/': False,
            f'/posts/{cls.post.pk}/edit/': reverse(
                'posts:post_detail', kwargs={'post_id': cls.post.pk}
            ),
        }
        cls.unexisting_page_url = '/unexisting_page/'

    def setUp(self):
        self.guest_client = Client()
        self.author_authorized_client = Client()
        self.author_authorized_client.force_login(self.author_user)
        self.another_authorized_client = Client()
        self.another_authorized_client.force_login(self.another_user)

    def test_url_for_guest_user_access(self):
        """Публичные страницы доступны гостевому пользователю."""
        for address in self.puplic_urls:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_for_guest_user_denied(self):
        """Приватные страницы не доступны гостевому пользователю."""
        for address, redirect_url in self.private_urls_for_guest.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)
                self.assertRedirects(response, redirect_url)

    def test_url_for_auth_user_access(self):
        """Приватные страницы доступны авторизированному пользователю."""
        for address, redirect_url in self.private_urls_for_user.items():
            with self.subTest(address=address):
                response = self.author_authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_for_non_author(self):
        """Приватные страницы не доступны для пользователя,
        не являющегося автором"""
        for address, redirect_url in self.private_urls_for_user.items():
            if redirect_url:
                with self.subTest(address=address):
                    response = self.another_authorized_client.get(address)
                    self.assertEqual(response.status_code, HTTPStatus.FOUND)
                    self.assertRedirects(response, redirect_url)

    def test_url_for_unexisting_page(self):
        """Запрос к несуществующей странице."""
        response = self.guest_client.get(self.unexisting_page_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
