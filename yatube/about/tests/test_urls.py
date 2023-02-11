from http import HTTPStatus

from django.test import TestCase, Client


class AboutURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.urls = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.urls = AboutURLTests.urls

    def test_about_url_exists_at_desired_location(self):
        """Проверка доступности адресов"""

        for url in self.urls:
            with self.subTest(url=url):
                self.assertEqual(
                    self.guest_client.get(url).status_code,
                    HTTPStatus.OK.value
                )

    def test_about_url_uses_correct_template(self):
        """Проверка шаблонов для адресов."""
        for url, template in self.urls.items():
            with self.subTest(url=url):
                self.assertTemplateUsed(
                    self.guest_client.get(url),
                    template
                )
