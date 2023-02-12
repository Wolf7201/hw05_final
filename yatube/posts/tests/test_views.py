from django import forms
from django.conf import settings
from django.core.paginator import Page
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from ..models import Post, User, Group
from ..forms import PostForm

import shutil
import tempfile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from http import HTTPStatus

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

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
        cls.user = User.objects.create_user(username='HasNoName')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug-test',
            description='Описание группы'
        )

        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded,
        )

        cls.index = reverse('posts:index')
        cls.group_list = reverse(
            'posts:group_list',
            kwargs={'slug': cls.group.slug}
        )
        cls.profile = reverse(
            'posts:profile',
            kwargs={'username': cls.user.username}
        )
        cls.post_detail = reverse(
            'posts:post_detail',
            kwargs={'post_id': cls.post.id}
        )
        cls.post_create = reverse('posts:post_create')
        cls.post_edit = reverse(
            'posts:post_edit',
            kwargs={'post_id': cls.post.id}
        )

        cls.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_error_page(self):
        response = self.client.get('/nonexist-page/')
        self.assertEqual(
            response.status_code,
            HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_cache_index(self):
        """Проверка хранения и очищения кэша для index."""
        response = self.authorized_client.get(reverse('posts:index'))
        posts = response.content
        Post.objects.create(
            text='Текст нового поста',
            author=self.user,
        )
        response_old = self.authorized_client.get(reverse('posts:index'))
        old_posts = response_old.content
        self.assertEqual(old_posts, posts)
        cache.clear()
        response_new = self.authorized_client.get(reverse('posts:index'))
        new_posts = response_new.content
        self.assertNotEqual(old_posts, new_posts)

    def test_page_uses_correct_template(self):
        """Проверка, что URL-адреса используют нужные шаблоны"""
        urls_template = {
            self.index: 'posts/index.html',
            self.group_list: 'posts/group_list.html',
            self.profile: 'posts/profile.html',
            self.post_detail: 'posts/post_detail.html',
            self.post_create: 'posts/create_post.html',
            self.post_edit: 'posts/create_post.html',
        }
        for reverse_name, template in urls_template.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_creation_and_appearance(self):
        test_created_post_url = [
            self.index,
            self.group_list,
            self.profile,
        ]
        created_post = Post.objects.create(
            text='Текст нового поста',
            author=self.user,
            group=self.group
        )
        for reverse_name in test_created_post_url:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                page_obj = response.context['page_obj']
                self.assertIn(created_post, page_obj)

    def method_check_post(self, context, is_page=True):
        if is_page:
            page_obj = context.get('page_obj')
            self.assertIsInstance(page_obj, Page)
            post = page_obj[0]
        else:
            post = context.get('post')

        context_text_objects = {
            post.text: self.post.text,
            post.author: self.post.author,
            post.group: self.post.group,
            post.image: self.post.image,
            post.pub_date: self.post.pub_date,
        }
        for current_value, expected_value in context_text_objects.items():
            with self.subTest(reverse_name=current_value):
                self.assertEqual(current_value, expected_value)

    def method_check_objects(self, objects):
        for current_value, expected_value in objects.items():
            with self.subTest(reverse_name=current_value):
                self.assertEqual(current_value, expected_value)

    def method_check_form(self, context, form_fields):
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form = context.get('form')
                self.assertIsInstance(form, PostForm)
                form_field = form.fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_index_groups_page_show_correct_context(self):
        """Проверяем Context страницы index"""
        context = self.authorized_client.get(self.index).context
        self.method_check_post(context)

    def test_group_list_groups_page_show_correct_context(self):
        """Проверяем Context страницы group_list"""
        context = self.authorized_client.get(self.group_list).context
        self.assertEqual(context.get('group'), self.group)
        self.method_check_post(context)

    def test_profile_groups_page_show_correct_context(self):
        """Проверяем Context страницы profile"""
        context = self.authorized_client.get(self.profile).context
        self.assertEqual(context.get('author'), self.user)
        self.method_check_post(context)

    def test_post_detail_page_show_correct_context(self):
        """Проверяем Context страницы post_detail"""
        context = self.authorized_client.get(self.post_detail).context
        self.method_check_post(context, False)

    def test_post_create_page_show_correct_context(self):
        """Проверяем Context страницы post_create"""
        context = self.authorized_client.get(self.post_create).context
        self.method_check_form(context, self.form_fields)

    def test_post_edit_page_show_correct_context(self):
        """Проверяем Context страницы post_edit"""
        context = self.authorized_client.get(self.post_edit).context
        self.method_check_form(context, self.form_fields)
        self.method_check_post(context, False)


class PaginatorViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.FIRST_PAGE_SIZE = settings.NUMBER_OF_POSTS_PER_PAGE
        cls.SECOND_PAGE_SIZE = 3

        cls.user = User.objects.create_user(username='HasNoName')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug-test',
            description='Описание группы'
        )

        objs = (Post(
            text=f'Тестовый текст{i}',
            author=cls.user,
            group=cls.group
        ) for i in range(cls.FIRST_PAGE_SIZE + cls.SECOND_PAGE_SIZE))

        Post.objects.bulk_create(objs)

        cls.templates_pages_names = [
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': cls.group.slug}
            ),

            reverse(
                'posts:profile',
                kwargs={'username': cls.user.username}
            ),
        ]

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_first_page_contains_ten_records(self):
        for reverse_name in self.templates_pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)

                self.assertEqual(
                    len(response.context['page_obj']),
                    self.FIRST_PAGE_SIZE
                )

    def test_second_page_contains_three_records(self):
        for reverse_name in self.templates_pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse('posts:index'), {'page': 2})
                self.assertEqual(
                    len(response.context['page_obj']),
                    self.SECOND_PAGE_SIZE
                )
