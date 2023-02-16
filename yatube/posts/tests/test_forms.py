import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Post, User, Group, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsCreateFormTests(TestCase):

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
            group=cls.group,
        )

        cls.form = PostForm()

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

        Post.objects.filter().delete()

        post_count = Post.objects.count()
        self.assertEqual(post_count, 0)

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        form_data = {
            'text': 'Тестовый текст1',
            'group': self.group.id,
            'image': uploaded,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        first_object = Post.objects.first()
        self.assertEqual(first_object.text, form_data['text'])
        self.assertEqual(first_object.group.id, self.group.id)

        image = uploaded.name
        self.assertEqual(first_object.image, f'posts/{image}')

    def test_edit_post(self):
        """Валидная форма изменяет запись в Post."""
        created_post_id = self.post.id
        post_count = Post.objects.count()

        new_group = Group.objects.create(
            title='Тестовая группа2',
            slug='slug-test2',
            description='Описание группы2'
        )

        form_data = {
            'text': 'Новый текст поста',
            'group': new_group.id
        }
        self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': created_post_id}
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count)
        edit_post = Post.objects.get(id=created_post_id)
        self.assertEqual(edit_post.text, form_data['text'])
        self.assertEqual(edit_post.group.id, new_group.id)

    def test_create_post_unauthorized_user(self):
        """Валидная форма от неавторизованного
         пользователя не создает запись в Post."""

        post_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
        }
        self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count)

    def test_create_comment(self):
        """Валидная форма создает запись в comment."""
        Comment.objects.filter().delete()
        comment_count = Comment.objects.count()
        self.assertEqual(comment_count, 0)
        form_data = {
            'text': 'Текст комментария',
        }
        self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': self.post.id}
                    ),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        comment = Comment.objects.first()
        self.assertEqual(comment.text, form_data['text'])

    def test_create_comment_unauthorized_user(self):
        """Валидная форма от неавторизованного
         пользователя не создает запись в Comment."""

        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый текст',
        }
        self.guest_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': self.post.id}
                    ),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count)
