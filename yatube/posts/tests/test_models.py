from django.conf import settings
from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
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
            text='Пост для тестирования',
        )
        cls.post_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации поста',
            'author': 'Автор поста',
            'group': 'Группа',
        }
        cls.group_verboses = {
            'title': 'Название группы',
            'slug': 'Код группы',
            'description': 'Описание группы',
        }
        cls.post_help_texts = {
            'text': 'Введите текст поста',
            'pub_date': 'Дата, в которую пост был опубликован',
            'author': 'Пользователь, создавший пост',
            'group': 'Выберите группу',
        }
        cls.group_help_texts = {
            'title': 'Название группы',
            'slug': 'Код группы',
            'description': 'Описание группы',
        }

    def test_post_model_have_correct_object_name(self):
        """У модели post корректно работает __str__."""
        post = PostModelTest.post
        post_str = post.text[:settings.POST_CHAR_COUNT]
        self.assertEqual(str(post), post_str)

    def test_post_model_have_correct_object_name(self):
        """У модели group корректно работает __str__."""
        group = PostModelTest.group
        group_str = group.title
        self.assertEqual(str(group), group_str)

    def test_post_verbose_name(self):
        """verbose_name в полях поста совпадают с ожидаемыми."""
        post = PostModelTest.post
        for field, expected_value in self.post_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value)

    def test_group_verbose_name(self):
        """verbose_name в полях группы совпадают с ожидаемыми."""
        group = PostModelTest.group
        for field, expected_value in self.group_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).verbose_name, expected_value)

    def test_post_help_text(self):
        """help_text в полях поста совпадают с ожидаемыми."""
        post = PostModelTest.post
        for field, expected_value in self.post_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value)

    def test_group_help_text(self):
        """help_text в полях группы совпадают с ожидаемыми."""
        group = PostModelTest.group
        for field, expected_value in self.group_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).help_text, expected_value)
