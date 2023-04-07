import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.group = Group.objects.create(
            title='Тестовая группа 1',
            slug='test_slug_1',
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
            text='Пост с максимально заполненными атрибутами для тестирования',
            group=cls.group,
            image=cls.uploaded,
        )
        cls.templates_pages_urls = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': cls.group.slug}
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
        cls.new_post_text = 'Новый пост с группой 2'
        cls.new_post_verifiable_urls = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': cls.group.slug}),
            reverse('posts:profile', kwargs={'username': cls.user.username}),
        ]

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
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
            'posts:group_list', kwargs={'slug': self.group.slug}
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
            self.group,
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
        self.assertTrue(
            response.context['is_edit'],
            'Признак возможности редактирования не передан в контексте'
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
            'group': self.group.pk
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
