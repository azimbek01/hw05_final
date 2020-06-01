from django.test import TestCase, override_settings
from django.test.client import Client
from django.contrib.auth import get_user_model
from django.urls import reverse

import time
from .models import Post, Group, Follow


USER = get_user_model()(username='new_user')


def get_post_context(post, context):
    for value in context['page']:
        if post.id == value.id:
            return value
    return


class TestProfileAfterRegistration(TestCase):
    def setUp(self):
        self.user = USER
        self.user.save()
        self.client.force_login(self.user)

    def test_get_profile(self):
        url_profile = reverse(
            'profile', kwargs={'username': self.user.username})
        response = self.client.get(url_profile)
        self.assertEqual(response.status_code, 200)


class testAuthorizedUserNewPost(TestCase):
    def setUp(self):
        self.user = USER
        self.user.save()
        self.client.force_login(self.user)

    def test_new_post(self):
        url_new_post = reverse('new_post')
        data = {
            'text': 'Проверка нового поста!',
            'author': self.user,
            'group_posts': 1
        }
        self.assertEquals(Post.objects.all().count(), 0)

        response = self.client.post(url_new_post, data, follow=True)
        self.assertEquals(response.status_code, 200)
        post = Post.objects.filter(author=self.user,
                                   text=data['text']).first()
        self.assertNotEqual(post, None)


class TestNotAuthorizedUserNewPost(TestCase):
    def setUp(self):
        self.user = USER
        self.user.save()

    def test_get_new_post(self):
        url_new_post = reverse('new_post')

        response = self.client.get(url_new_post)
        self.assertEquals(response.status_code, 302)
        self.assertRedirects(response, '/auth/login/?next=/new/')


class TestPostView(TestCase):
    def setUp(self):
        self.user = USER
        self.user.save()
        self.client.force_login(self.user)

    def test_view_post(self):
        url_new_post = reverse('new_post')
        data = {
            'text': 'Пост для тестирования просмотра',
            'author': self.user,
            'group_posts': 1
        }

        response_new_post = self.client.post(url_new_post, data, follow=True)
        post = Post.objects.filter(author=self.user,
                                   text=data['text']).first()
        post_context = get_post_context(post, response_new_post.context)
        self.assertNotEquals(
            post_context, None,
            msg='Новая запись не появилась на главной странице сайта')

        url_profile = reverse(
                     'profile', kwargs={'username': self.user.username})

        response_profile = self.client.get(url_profile)
        post_context = get_post_context(post, response_profile.context)
        self.assertNotEquals(
            post_context, None,
            msg='Новая запись не появилась на странице пользователя')

        url_post = reverse(
            'post', kwargs={'username': self.user.username,
                            'post_id': post.id})

        response_post = self.client.get(url_post)
        self.assertEquals(
            response_post.context['post'].id, post.id,
            msg='Новая запись не появилась на странице просмотра поста')


class TestPostEdit(TestCase):
    def setUp(self):
        self.user = USER
        self.user.save()
        self.client.force_login(self.user)

        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='Test',
            description='Тест'
        )

        self.post = Post.objects.create(
                        text='Тестовый пост до изменения',
                        author=self.user,
                        group=self.group)

    def test_post_edit(self):
        data = {
            'text': 'Тестовый пост после изменения',
            'author': self.user,
            'group': self.group.id
        }
        post = Post.objects.filter(author=self.user,
                                   group=self.group).first()
        self.assertNotEqual(post, None)

        url_post_edit = reverse(
            'post_edit', kwargs={'username': self.user.username,
                                 'post_id': post.id})

        response_edit = self.client.post(url_post_edit, data, follow=True)

        self.assertEquals(
            response_edit.context['post'].text, data['text'],
            msg='Содержимое поста не изменилось на странице просмотра поста')

        url_profile = reverse(
            'profile', kwargs={'username': self.user.username})

        response_profile = self.client.get(url_profile)
        post_context = get_post_context(post, response_profile.context)

        self.assertNotEquals(post_context, None)
        self.assertEquals(
            post_context.text, data['text'],
            'Содержимое поста не изменилось на странице пользователя')

        response_index = self.client.get('/')
        post_context = get_post_context(post, response_index.context)

        self.assertNotEquals(post_context, None)
        self.assertEquals(
            post_context.text, data['text'],
            'Содержимое поста не изменилось на главной странице')


class TestAnswer404(TestCase):
    def test_404_if_page_was_not_found(self):
        url = 'index/code_404'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class TestPostViewHasImage(TestCase):
    def setUp(self):
        self.user = USER
        self.user.save()
        self.client.force_login(self.user)

    def test_post_view_has_image(self):
        tag = '<img'

        with open('media/posts/tolstoy.jpg', 'rb') as img:
            post = self.client.post(
                reverse('new_post'),
                {'text': 'post with image', 'image': img}
                )

        post = Post.objects.filter(author=self.user).first()

        url_post = reverse(
            'post', kwargs={
                'username': self.user.username, 'post_id': post.id
                }
            )

        response = self.client.get(url_post)
        self.assertContains(
            response, tag,
            msg_prefix=f'Тэг {tag} не найден на странице просмотра поста: '
                       f'{url_post}'
            )


class TestProfileHasImage(TestCase):
    def setUp(self):
        self.user = USER
        self.user.save()
        self.client.force_login(self.user)

        self.post = Post.objects.create(
            text='Тестовый текст',
            author=self.user
            )

    def test_profile_has_image(self):
        post = Post.objects.last()
        url_post_edit = reverse(
            'post_edit', kwargs={
                'username': self.user.username,
                'post_id': post.id
                }
            )

        with open('media/posts/tolstoy.jpg', 'rb') as img:
            self.client.post(
                url_post_edit, {'text': 'post with image', 'image': img}
                )

        url_profile = reverse(
            'profile', kwargs={'username': self.user.username}
            )

        tag = '<img'
        response = self.client.get(url_profile)
        self.assertContains(
            response, tag,
            msg_prefix=f'Тэг {tag} не найден в профиле: {url_profile}'
            )


@override_settings(
    CACHES={
        'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}
        }
    )
class TestIndexGroupHasImage(TestCase):
    def setUp(self):
        self.user = USER
        self.user.save()
        self.client.force_login(self.user)

        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='TestSlug',
            description='Тест'
        )

        self.post = Post.objects.create(
            text='Тестовый текст',
            author=self.user,
            group=self.group
            )

    def test_index_group_has_image(self):
        tag = '<img'
        url_group = f'/group/{self.group.slug}/'
        post = Post.objects.last()

        url_post_edit = reverse(
            'post_edit', kwargs={
                'username': self.user.username,
                'post_id': post.id
                }
            )

        with open('media/posts/tolstoy.jpg', 'rb') as img:
            self.client.post(
                url_post_edit, {'text': 'post with image', 'image': img}
                )

        response_index = self.client.get(reverse('index'))
        self.assertContains(
            response_index, tag,
            msg_prefix=f'Тэг {tag} не найден на главной '
                       f'странице index'
                       )

        response_group = self.client.get(url_group)
        self.assertContains(
            response_group, tag,
            msg_prefix=f'Тэг {tag} не найден на странице группы {url_group}'
            )


class TestFileTypeNonImage(TestCase):
    def setUp(self):
        self.user = USER
        self.user.save()
        self.client.force_login(self.user)

        self.post = Post.objects.create(
                        text='Тестовый текст',
                        author=self.user
                        )

    def test_file_type_non_image(self):
        post = Post.objects.last()

        url_post_edit = reverse(
            'post_edit', kwargs={
                'username': self.user.username,
                'post_id': post.id
                }
            )

        with open('media/posts/test.txt', 'rb') as img:
            response = self.client.post(
                url_post_edit, {'text': 'post with image', 'image': img}
                )

        self.assertIn('image', response.context['form'].errors)


class TestCach(TestCase):
    def setUp(self):
        self.user = USER
        self.user.save()
        self.client.force_login(self.user)

        self.post = Post.objects.create(
                        text='Test_text_1',
                        author=self.user)

    def test_cach(self):
        post = Post.objects.filter(author=self.user).first()
        url_post_edit = reverse(
            'post_edit', kwargs={
                'username': self.user.username, 'post_id': post.id
                }
            )
        response_index = self.client.get(reverse('index'))
        self.assertContains(response_index, 'Test_text_1')
        self.client.post(
            url_post_edit,
            {'text': 'Test_text_2', 'author': self.user},
            follow=True
            )
        response_index = self.client.get(reverse('index'))
        self.assertContains(response_index, 'Test_text_1')
        self.assertNotContains(response_index, 'Test_text_2')

        time.sleep(20)

        response_index = self.client.get(reverse('index'))
        self.assertContains(response_index, 'Test_text_2')
        self.assertNotContains(response_index, 'Test_text_1')


class TestAuthorizedUserSubscribeUnsubsribe(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = USER
        self.user.save()
        self.client.force_login(self.user)

        self.post = Post.objects.create(
                        text='Test_text_1',
                        author=self.user)

        self.client_2 = Client()
        self.user_2 = get_user_model()(username='new_user_2')
        self.user_2.save()
        self.client_2.force_login(self.user_2)

    def test_user_subscribe(self):
        response = self.client_2.get(f'/{self.user.username}/')
        self.assertEqual(response.status_code, 200)
        follow = Follow.objects.filter(
                  user=self.user_2, author=self.user).exists()
        self.assertFalse(follow)

        url = reverse('profile_follow', kwargs={'username': self.user})
        response = self.client_2.post(
            url, {'username': self.user}, follow=True
        )
        self.assertEqual(response.status_code, 200)
        follow = Follow.objects.filter(
            user=self.user_2, author=self.user).exists()
        self.assertTrue(follow)

    def test_user_unsubscribe(self):
        follow = Follow.objects.filter(
            user=self.user_2, author=self.user).exists()
        self.assertFalse(follow)
        follow = Follow.objects.create(
            user=self.user_2, author=self.user
        )
        self.assertTrue(follow)
        url = reverse('profile_unfollow', kwargs={'username': self.user})
        response = self.client_2.post(
            url, {'username': self.user}, follow=True
        )
        self.assertEqual(response.status_code, 200)
        follow = Follow.objects.filter(
            user=self.user_2, author=self.user).exists()
        self.assertFalse(follow)


class TestNewPostForSubscribeUnsubscribe(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = USER
        self.user.save()
        self.client.force_login(self.user)

        self.post = Post.objects.create(
                        text='Test_text_1',
                        author=self.user)

        self.client_2 = Client()
        self.user_2 = get_user_model()(username='new_user_2')
        self.user_2.save()
        self.client_2.force_login(self.user_2)

    def test_new_post_for_subscriber(self):
        response = self.client_2.get(reverse('follow_index'))
        self.assertNotContains(response, self.post.text)
        follow = Follow.objects.create(
            user=self.user_2, author=self.user
        )
        self.assertTrue(follow)
        response = self.client_2.get(reverse('follow_index'))
        self.assertContains(response, self.post.text)

    def test_new_post_for_unsubscribed_user(self):
        follow = Follow.objects.filter(
            user=self.user_2, author=self.user).exists()
        self.assertFalse(follow)
        response = self.client_2.get(reverse('follow_index'))
        self.assertNotContains(response, self.post.text)


class TestUserAddComment(TestCase):
    def setUp(self):
        self.user = USER
        self.user.save()
        self.client.force_login(self.user)

        self.post = Post.objects.create(
                        text='Test_text_1',
                        author=self.user)

    def test_authorized_user_can_comment(self):
        url = reverse(
            'add_comment', kwargs={
                'username': self.user, 'post_id': self.post.id
                }
        )
        comment = self.post.comments.filter(id=1).exists()
        self.assertFalse(comment)
        self.client.post(
            url, {
                'username': self.user, 'post_id': self.post.id,
                'text': 'Test_Comment'
                }
        )
        comment = self.post.comments.get(id=1)
        self.assertEqual(comment.text, 'Test_Comment')

    def test_not_authorized_user_cant_comment(self):
        self.client.logout()
        url = reverse(
            'add_comment', kwargs={
                'username': self.user, 'post_id': self.post.id
                }
        )
        comment = self.post.comments.filter(id=1).exists()
        self.assertFalse(comment)
        response = self.client.post(
            url, {'username': self.user, 'post_id': self.post.id,
                  'text': 'Test_Comment'}, follow=True
        )
        self.assertRedirects(
            response, '/auth/login/?next=/new_user/1/comment/'
        )
