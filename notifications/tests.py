from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from notifications.models import Notification
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()

class NotificationModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password")

    def test_notification_creation(self):
        notification = Notification.notify(
            user=self.user,
            title="Test Title",
            message="Test Message",
            url="/test-url/"
        )
        self.assertEqual(notification.title, "Test Title")
        self.assertEqual(notification.message, "Test Message")
        self.assertEqual(notification.url, "/test-url/")
        self.assertFalse(notification.is_read)
        self.assertEqual(notification.user, self.user)

    def test_str_representation(self):
        notification = Notification.notify(
            user=self.user,
            title="Test Title",
            message="Test Message"
        )
        self.assertEqual(str(notification), f"To {self.user}: Test Title")

    def test_ago_display(self):
        notification = Notification.notify(
            user=self.user,
            title="Test Title",
            message="Test Message"
        )
        self.assertIn("ago", notification.ago_display())


class NotificationViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password")
        self.other_user = User.objects.create_user(username="otheruser", email="other@example.com", password="password")
        self.notification1 = Notification.notify(user=self.user, title="N1", message="M1")
        self.notification2 = Notification.notify(user=self.user, title="N2", message="M2")
        self.other_notification = Notification.notify(user=self.other_user, title="ON1", message="OM1")

    def test_notification_list_unauthenticated(self):
        response = self.client.get(reverse('notifications'))
        self.assertNotEqual(response.status_code, 200)

    def test_notification_list_authenticated(self):
        self.client.login(email="test@example.com", password="password")
        response = self.client.get(reverse('notifications'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/notifications.html")
        self.assertEqual(len(response.context["notifications"]), 2)

    def test_mark_read_single(self):
        self.client.login(email="test@example.com", password="password")
        url = reverse('mark_read', kwargs={'pk': self.notification1.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.notification1.refresh_from_db()
        self.assertTrue(self.notification1.is_read)
        self.notification2.refresh_from_db()
        self.assertFalse(self.notification2.is_read)

    def test_mark_read_all(self):
        self.client.login(email="test@example.com", password="password")
        url = reverse('mark_all_read')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.notification1.refresh_from_db()
        self.notification2.refresh_from_db()
        self.assertTrue(self.notification1.is_read)
        self.assertTrue(self.notification2.is_read)

    def test_notifications_count(self):
        self.client.login(email="test@example.com", password="password")
        response = self.client.get(reverse('notifications_count'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 2)


class NotificationAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password")
        self.other_user = User.objects.create_user(username="otheruser", email="other@example.com", password="password")
        self.notification1 = Notification.notify(user=self.user, title="N1", message="M1")
        self.notification2 = Notification.notify(user=self.user, title="N2", message="M2")
        self.other_notification = Notification.notify(user=self.other_user, title="ON1", message="OM1")

    def test_api_notification_list(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('api_notifications'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Assuming pagination or returning a list directly
        data = response.json()
        if isinstance(data, dict) and "results" in data:
            results = data["results"]
        else:
            results = data
        self.assertEqual(len(results), 2)
        self.assertIn("ago", results[0])

    def test_api_mark_read_single(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(reverse('api_notifications_mark_read'), {"id": self.notification1.pk}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification1.refresh_from_db()
        self.assertTrue(self.notification1.is_read)
        self.notification2.refresh_from_db()
        self.assertFalse(self.notification2.is_read)

    def test_api_mark_read_all(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(reverse('api_notifications_mark_read'), {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification1.refresh_from_db()
        self.notification2.refresh_from_db()
        self.assertTrue(self.notification1.is_read)
        self.assertTrue(self.notification2.is_read)

    def test_api_unread_count(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('api_notifications_unread_count'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["count"], 2)
