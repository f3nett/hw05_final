from http import HTTPStatus

from django.test import TestCase


class ViewTestClass(TestCase):
    """URL-адрес с уведомлением об ошибке 404 not fount
    использует соответствующий шаблон."""
    def test_error_page(self):
        response = self.client.get('/nonexist-page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')
