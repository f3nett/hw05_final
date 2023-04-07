import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Comment, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.form = PostForm()
        cls.post = Post.objects.create(
            author=cls.user,
            text='Пост для тестирования',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.new_post_text = 'Новый пост в БД'
        cls.new_comment_text = 'Новый комментарий к посту'
        cls.change_post_text = 'Новый пост в БД'
        cls.form_list = ['text', 'group']
        cls.posts_image_folder = 'posts/'

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='small_1.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': self.new_post_text,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            )
        )
        self.assertEqual(
            Post.objects.count(),
            posts_count + 1,
            'После создания нового поста количество постов в БД не увеличилось'
        )
        self.assertTrue(
            Post.objects.filter(
                author=self.user,
                text=self.new_post_text,
                image=self.posts_image_folder + uploaded.name
            ).exists(),
            'Созданный пост не найден в БД'
        )

    def test_edit_post(self):
        """Валидная форма изменяет запись в Post."""
        uploaded = SimpleUploadedFile(
            name='small_2.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': self.change_post_text,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.pk}
        ))
        self.post.refresh_from_db()
        self.assertEqual(
            self.post.text,
            self.change_post_text,
            'Текст поста не изменился'
        )
        self.assertEqual(
            self.post.image,
            self.posts_image_folder + uploaded.name,
            'Картинка к посту не добавлена'
        )

    def test_add_comment_by_auth_client(self):
        """Валидная форма добавляет комментарий к посту."""
        comments_count = Comment.objects.count()
        new_comment_data = {
            'text': self.new_comment_text,
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=new_comment_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.pk}
        ))
        self.assertEqual(
            Comment.objects.count(),
            comments_count + 1,
            'После добавления комментария их количество не увеличилось'
        )
        self.assertTrue(
            Comment.objects.filter(
                post=self.post.pk,
                text=new_comment_data['text'],
                author=self.user,
            ).exists(),
            'Добавленный комментарий не найден'
        )

    def test_post_form_label(self):
        """Для формы указаны labels."""
        for form in self.form_list:
            with self.subTest(form=form):
                label = self.form.fields[form].label
                self.assertIsNotNone(label)

    def test_post_form_help_text(self):
        """Для формы указаны help_texts."""
        for form in self.form_list:
            with self.subTest(form=form):
                help_text = self.form.fields[form].help_text
                self.assertIsNotNone(help_text)
