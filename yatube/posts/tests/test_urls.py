from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User

INDEX_URL = '/'
GROUP_URL = '/group/{group_slug}/'
PROFILE_URL = '/profile/{username}/'
POST_DETAIL_URL = '/posts/{post_id}/'
POST_EDIT_URL = '/posts/{post_id}/edit/'
POST_CREATE_URL = '/create/'
POST_COMMENT_URL = '/posts/{post_id}/comment/'
FOLLOW_POSTS_URL = '/follow/'
FOLLOW_URL = '/profile/{username}/follow/'


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
            INDEX_URL,
            GROUP_URL.format(group_slug=cls.group.slug),
            PROFILE_URL.format(username=cls.author_user.username),
            POST_DETAIL_URL.format(post_id=cls.post.pk),
        ]
        cls.private_urls_for_guest = {
            POST_CREATE_URL,
            POST_EDIT_URL.format(post_id=cls.post.pk),
            POST_COMMENT_URL.format(post_id=cls.post.pk),
            FOLLOW_URL.format(username=cls.author_user.username),
            FOLLOW_POSTS_URL,
        }
        cls.private_urls_for_user = {
            POST_CREATE_URL: False,
            POST_EDIT_URL.format(post_id=cls.post.pk): False,
            POST_COMMENT_URL.format(post_id=cls.post.pk): reverse(
                'posts:post_detail', kwargs={'post_id': cls.post.pk}
            ),
            FOLLOW_URL.format(username=cls.author_user.username): reverse(
                'posts:profile', kwargs={'username': cls.author_user.username}
            ),
            FOLLOW_POSTS_URL: False,
        }
        cls.private_urls_for_author = {
            POST_EDIT_URL.format(post_id=cls.post.pk): reverse(
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
        for address in self.private_urls_for_guest:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)
                redirect_url = reverse('users:login') + '?next=' + address
                self.assertRedirects(response, redirect_url)

    def test_url_for_auth_user_access(self):
        """Приватные страницы доступны авторизированному пользователю."""
        for address, redirect_url in self.private_urls_for_user.items():
            with self.subTest(address=address):
                response = self.author_authorized_client.get(address)
                if redirect_url is False:
                    self.assertEqual(response.status_code, HTTPStatus.OK)
                else:
                    self.assertEqual(response.status_code, HTTPStatus.FOUND)
                    self.assertRedirects(response, redirect_url)

    def test_url_for_non_author(self):
        """Приватные страницы не доступны для пользователя,
        не являющегося автором"""
        for address, redirect_url in self.private_urls_for_author.items():
            with self.subTest(address=address):
                response = self.another_authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)
                self.assertRedirects(response, redirect_url)

    def test_url_for_unexisting_page(self):
        """Запрос к несуществующей странице."""
        response = self.guest_client.get(self.unexisting_page_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
