import math
import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post, User, Follow

GROUP_POST_COUNT = 12
PROFILE_POST_COUNT = 13
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName1')
        cls.not_follower_user = User.objects.create_user(username='HasNoName2')
        cls.author = User.objects.create_user(username='Author')
        cls.group_1 = Group.objects.create(
            title='Тестовая группа 1',
            slug='test_slug_1',
            description='Тестовое описание',
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test_slug_2',
            description='Тестовое описание',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост без группы',
            image=cls.uploaded,
        )
        Post.objects.bulk_create(
            Post(
                author=cls.user,
                text=f'Тестовый пост {i} с группой 1',
                group=cls.group_1,
                image=cls.uploaded,
            ) for i in range(GROUP_POST_COUNT)
        )
        cls.templates_pages_urls = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': cls.group_1.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': cls.user.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': cls.post.pk}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': cls.post.pk}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        cls.paginator_urls = {
            reverse('posts:index'): Post.objects.count(),
            reverse(
                'posts:profile', kwargs={'username': cls.user.username}
            ): PROFILE_POST_COUNT,
            reverse(
                'posts:group_list', kwargs={'slug': cls.group_1.slug}
            ): GROUP_POST_COUNT
        }
        cls.new_post_text = 'Новый пост с группой 2'
        cls.new_comment_text = 'Новый комментарий к посту'
        cls.new_post_verifiable_urls = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': cls.group_2.slug}),
            reverse('posts:profile', kwargs={'username': cls.user.username}),
        ]

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.not_follower_user)
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for url, template in self.templates_pages_urls.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(
                    response,
                    template,
                    'Адрес не соответствует html шаблону'
                )

    def test_paginator_returns(self):
        """Пагинатор возвращает правильное количество постов."""
        for url, url_posts_count in self.paginator_urls.items():
            with self.subTest(url=url):
                paginator_page_count = math.ceil(
                    url_posts_count / settings.POSTS_COUNT
                )
                page = 1
                while page <= paginator_page_count:
                    response = self.authorized_client.get(
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

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        post_object = response.context['page_obj'][0]
        self.assertIsInstance(
            post_object,
            Post,
            'Поля из контекста не совпадают с полями модели'
        )
        self.assertIsNotNone(
            post_object.image,
            'Картинка не передается на страницу index'
        )

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group_1.slug}
        ))
        post_object = response.context['page_obj'][0]
        post_group = response.context['group']
        self.assertIsInstance(
            post_object,
            Post,
            'Поля из контекста не совпадают с полями модели'
        )
        self.assertEqual(
            post_group,
            self.group_1,
            'В контексте передается неправильная группа поста'
        )
        self.assertIsNotNone(
            post_object.image,
            'Картинка не передается на страницу group_list'
        )

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': self.user.username}
        ))
        post_object = response.context['page_obj'][0]
        posts_author = response.context['author']
        self.assertIsInstance(
            post_object,
            Post,
            'Поля из контекста не совпадают с полями модели'
        )
        self.assertEqual(
            posts_author,
            self.user,
            'В контексте передается неправильный автор поста'
        )
        self.assertIsNotNone(
            post_object.image,
            'Картинка не передается на страницу profile'
        )

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk}
        ))
        post_object = response.context['post']
        post_pk = post_object.id
        self.assertIsInstance(
            post_object,
            Post,
            'Поля из контекста не совпадают с полями модели'
        )
        self.assertEqual(
            post_pk,
            self.post.pk,
            'В контексте передается неправильный id поста'
        )
        self.assertIsNotNone(
            post_object.image,
            'Картинка не передается на страницу post_detail'
        )

    def test_edit_post_show_correct_context(self):
        """Шаблон edit_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_edit',
            kwargs={'post_id': self.post.pk}
        ))
        self.assertIn(
            'form',
            response.context,
            'Контекст для редактирования поста не содержит форму'
        )
        self.assertIsInstance(
            response.context['form'],
            PostForm,
            'Форма, передаваемая в контексте, не является формой для поста'
        )

    def test_create_post_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form = response.context['form']
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        self.assertIsInstance(
            form,
            PostForm,
            'Форма, передаваемая в контексте, не является формой для поста'
        )
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(
                    form_field,
                    expected,
                    'В форму передано поле с неправильным типом данных'
                )

    def test_create_post_relations(self):
        """Новый созданный пост доступен на шаблонах."""
        new_post = {
            'text': self.new_post_text,
            'group': self.group_2.pk
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=new_post
        )
        created_new_post = Post.objects.latest('id')
        for url in self.new_post_verifiable_urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                posts = response.context['page_obj']
                self.assertIn(
                    created_new_post,
                    posts,
                    f'Новый пост не появился на {url}'
                )

    def test_cashe(self):
        """Кеширование на странице index работает корректно."""
        start_content = self.authorized_client.get(
            reverse('posts:index')
        ).content
        Post.objects.create(
            author=self.user,
            text=self.new_post_text,
        )
        content_after_add_post = self.authorized_client.get(
            reverse('posts:index')
        ).content
        cache.clear()
        content_after_cache_clear = self.authorized_client.get(
            reverse('posts:index')
        ).content
        self.assertEqual(
            start_content,
            content_after_add_post,
            'Отсутствует кеширование страницы'
        )
        self.assertNotEqual(
            start_content,
            content_after_cache_clear,
            'Кеширование страницы работает некорректно'
        )

    def test_follow_to_author(self):
        """Авторизованный пользователь может подписываться на
        других пользователей и удалять их из подписок."""
        before_follow = Follow.objects.filter(
            user=self.user,
            author=self.author
        ).count()
        self.authorized_client.post(reverse(
            'posts:profile_follow',
            kwargs={'username': self.author.username}
        ))
        after_follow = Follow.objects.filter(
            user=self.user,
            author=self.author
        ).count()
        self.assertEqual(
            after_follow,
            before_follow + 1,
            'Подписка авторизованного пользователя на автора не работает'
        )
        self.authorized_client.post(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.author.username}
        ))
        after_unfollow = Follow.objects.filter(
            user=self.user,
            author=self.author
        ).count()
        self.assertEqual(
            after_unfollow,
            after_follow - 1,
            'Отписка авторизованного пользователя от автора не работает'
        )

    def test_view_followings(self):
        """Новая запись пользователя появляется в ленте тех, кто на
        него подписан, и не появляется в ленте тех, кто не подписан."""
        self.authorized_client.post(reverse(
            'posts:profile_follow',
            kwargs={'username': self.author.username}
        ))
        new_post = {
            'text': self.new_post_text,
            'group': self.group_2.pk
        }
        self.authorized_author.post(
            reverse('posts:post_create'),
            data=new_post
        )
        follower_response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        posts_for_follower = follower_response.context['page_obj']
        self.assertIn(
            Post.objects.latest('id'),
            posts_for_follower,
            'Новый пост автора не появляется в ленте подписчика'
        )
        not_follower_response = self.authorized_client_2.get(
            reverse('posts:follow_index')
        )
        posts_for_not_follower = not_follower_response.context['page_obj']
        self.assertNotIn(
            Post.objects.latest('id'),
            posts_for_not_follower,
            'Новый пост автора появляется в ленте не подписанного пользователя'
        )
