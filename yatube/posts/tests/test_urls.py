from http import HTTPStatus

from django.test import TestCase, Client

from ..models import Post, User, Group
from django.core.cache import cache


class PostsURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug-test',
            description='Описание группы'
        )

        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group
        )
        cls.urls_for_guest_users = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.user.username}/': 'posts/profile.html',
            f'/posts/{cls.post.id}/': 'posts/post_detail.html',

        }
        cls.urls_for_authorized_users = {
            f'/posts/{cls.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }

        cls.all_urls = {
            **cls.urls_for_guest_users,
            **cls.urls_for_authorized_users,
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_urls_exists_at_desired_location_for_guest(self):
        """Проверка доступности адресов для гостей"""
        for url in self.urls_for_guest_users:
            with self.subTest(url=url):
                self.assertEqual(
                    self.guest_client.get(url).status_code,
                    HTTPStatus.OK.value
                )

    def test_urls_exists_at_desired_location_for_authorized(self):
        """Проверка доступности адресов для авторизованных"""
        for url in self.all_urls:
            with self.subTest(url=url):
                self.assertEqual(
                    self.authorized_client.get(url).status_code,
                    HTTPStatus.OK.value
                )

    def test_urls_uses_correct_template_for_authorized(self):
        """Проверка всех шаблонов для адресов"""
        for url, template in self.all_urls.items():
            with self.subTest(url=url):
                self.assertTemplateUsed(
                    self.authorized_client.get(url),
                    template
                )

    def test_urls_redirect_for_guest(self):
        """Проверка редиректа для гостей"""
        for url in self.urls_for_authorized_users:
            with self.subTest(url=url):
                self.assertEqual(
                    self.guest_client.get(url).status_code,
                    HTTPStatus.OK.FOUND
                )

    def test_urls_redirect_for_author_another_post(self):
        """Проверка редиректа для автора не этого поста"""
        new_user = User.objects.create_user(username='NewUser')
        new_authorized_user = Client()
        new_authorized_user.force_login(new_user)

        response = new_authorized_user.get(
            f'/posts/{self.post.id}/edit/'
        ).status_code

        self.assertEqual(response, HTTPStatus.OK.FOUND)

    def test_request_to_non_existent_page(self):
        """Проверка, запрос к несуществующей странице вернёт ошибку 404,
         и перенаправит на нужную страницу"""
        response = self.client.get('/nonexist-page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')
