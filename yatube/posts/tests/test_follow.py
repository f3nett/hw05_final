from django.test import Client, TestCase
from django.urls import reverse

from ..models import Follow, Post, User


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Author')
        cls.follower = User.objects.create_user(username='HasNoName1')
        cls.not_follower = User.objects.create_user(username='HasNoName2')
        cls.post = Post.objects.create(
            author=cls.author,
            text='Пост от автора для тестирования подписок',
        )

    def setUp(self):
        self.follower_client = Client()
        self.follower_client.force_login(self.follower)
        self.not_follower_client = Client()
        self.not_follower_client.force_login(self.not_follower)
        Follow.objects.all().delete()

    def test_follow_author(self):
        """Пользователь может подписываться на автора."""
        before_follow = Follow.objects.filter(
            user=self.follower,
            author=self.author
        ).count()
        self.follower_client.post(reverse(
            'posts:profile_follow',
            kwargs={'username': self.author.username}
        ))
        after_follow = Follow.objects.filter(
            user=self.follower,
            author=self.author
        ).count()
        self.assertEqual(
            after_follow,
            before_follow + 1,
            'Подписка авторизованного пользователя на автора не работает'
        )

    def test_unfollow_author(self):
        """Пользователь может отписаться от автора."""
        self.follower_client.post(reverse(
            'posts:profile_follow',
            kwargs={'username': self.author.username}
        ))
        before_unfollow = Follow.objects.filter(
            user=self.follower,
            author=self.author
        ).count()
        self.follower_client.post(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.author.username}
        ))
        after_unfollow = Follow.objects.filter(
            user=self.follower,
            author=self.author
        ).count()
        self.assertEqual(
            after_unfollow,
            before_unfollow - 1,
            'Отписка авторизованного пользователя от автора не работает'
        )

    def test_view_follower(self):
        """Пост появляется в ленте подписанных пользователей."""
        self.follower_client.post(reverse(
            'posts:profile_follow',
            kwargs={'username': self.author.username}
        ))
        follower_response = self.follower_client.get(
            reverse('posts:follow_index')
        )
        posts_for_follower = follower_response.context['page_obj']
        self.assertIn(
            self.post,
            posts_for_follower,
            'Новый пост автора не появляется в ленте подписчика'
        )

    def test_view_not_follower(self):
        """Пост не появляется в ленте неподписанных пользователей."""
        not_follower_response = self.not_follower_client.get(
            reverse('posts:follow_index')
        )
        posts_for_not_follower = not_follower_response.context['page_obj']
        self.assertNotIn(
            self.post,
            posts_for_not_follower,
            'Новый пост автора появляется в ленте не подписанного пользователя'
        )
