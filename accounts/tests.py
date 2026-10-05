import json
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from accounts.models import JobSeekerProfile, OTPVerification
from companies.models import Company

User = get_user_model()


class AccountsRegistrationTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_register_seeker(self):
        data = {
            "role": "seeker",
            "full_name": "Test Seeker",
            "username": "testseeker",
            "email": "seeker@example.com",
            "password": "Password123",
            "password2": "Password123",
            "phone": "1234567890",
        }
        with patch("accounts.utils.send_mail") as mock_send:
            response = self.client.post(reverse("register"), data)
            
        self.assertRedirects(response, reverse("verify_otp"))
        user = User.objects.get(email="seeker@example.com")
        self.assertEqual(user.role, User.Role.SEEKER)
        self.assertFalse(user.is_verified)
        self.assertTrue(JobSeekerProfile.objects.filter(user=user).exists())
        self.assertTrue(OTPVerification.objects.filter(email="seeker@example.com").exists())
        self.assertEqual(self.client.session.get("pending_verify_email"), "seeker@example.com")
        mock_send.assert_called_once()

    def test_register_recruiter(self):
        data = {
            "role": "recruiter",
            "full_name": "Test Recruiter",
            "username": "testrecruiter",
            "email": "recruiter@example.com",
            "password": "Password123",
            "password2": "Password123",
            "company_name": "Test Corp"
        }
        response = self.client.post(reverse("register"), data)
        self.assertRedirects(response, reverse("verify_otp"))
        user = User.objects.get(email="recruiter@example.com")
        self.assertEqual(user.role, User.Role.RECRUITER)
        self.assertTrue(Company.objects.filter(recruiter=user, company_name="Test Corp").exists())

    def test_register_invalid_email(self):
        data = {
            "role": "seeker",
            "full_name": "Test",
            "username": "testuser",
            "email": "invalidemail",
            "password": "Password123",
            "password2": "Password123",
        }
        response = self.client.post(reverse("register"), data)
        self.assertContains(response, "Please enter a valid email address.")
        self.assertFalse(User.objects.filter(username="testuser").exists())

    def test_register_password_mismatch(self):
        data = {
            "role": "seeker",
            "full_name": "Test",
            "username": "testuser",
            "email": "test@example.com",
            "password": "Password123",
            "password2": "Password321",
        }
        response = self.client.post(reverse("register"), data)
        self.assertContains(response, "Passwords do not match.")

    def test_register_short_password(self):
        data = {
            "role": "seeker",
            "full_name": "Test",
            "username": "testuser",
            "email": "test@example.com",
            "password": "pass",
            "password2": "pass",
        }
        response = self.client.post(reverse("register"), data)
        self.assertContains(response, "Password must be at least 8 characters.")

    def test_register_existing_email(self):
        User.objects.create_user(email="test@example.com", username="testuser", password="Password123")
        data = {
            "role": "seeker",
            "full_name": "Test 2",
            "username": "testuser2",
            "email": "test@example.com",
            "password": "Password123",
            "password2": "Password123",
        }
        response = self.client.post(reverse("register"), data)
        self.assertContains(response, "An account with this email already exists.")


class OTPVerificationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="verify@example.com", username="verifyuser", password="Password123", is_verified=False
        )
        self.otp = OTPVerification.generate(email="verify@example.com", purpose=OTPVerification.Purpose.VERIFY, user=self.user)
        session = self.client.session
        session["pending_verify_email"] = "verify@example.com"
        session.save()

    def test_verify_valid_otp(self):
        data = {f"otp{i}": c for i, c in enumerate(self.otp.otp, 1)}
        response = self.client.post(reverse("verify_otp"), data)
        self.assertRedirects(response, reverse("seeker_dashboard"))  # default role is seeker
        
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_verified)
        self.otp.refresh_from_db()
        self.assertTrue(self.otp.verified)
        self.assertTrue("_auth_user_id" in self.client.session)  # user is logged in

    def test_verify_invalid_otp(self):
        data = {f"otp{i}": "0" for i in range(1, 7)}
        response = self.client.post(reverse("verify_otp"), data)
        self.assertRedirects(response, reverse("verify_otp"))
        
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_verified)
        self.otp.refresh_from_db()
        self.assertEqual(self.otp.attempts, 1)

    def test_resend_otp(self):
        response = self.client.get(reverse("resend_otp"))
        self.assertRedirects(response, reverse("verify_otp"))
        new_otp = OTPVerification.objects.filter(email="verify@example.com").order_by("-created_at").first()
        self.assertNotEqual(self.otp.otp, new_otp.otp)


class LoginLogoutTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="login@example.com", username="loginuser", password="Password123", is_verified=True, role=User.Role.SEEKER
        )
        self.unverified_user = User.objects.create_user(
            email="unverified@example.com", username="unverifieduser", password="Password123", is_verified=False
        )

    def test_login_successful(self):
        response = self.client.post(reverse("login"), {"email": "login@example.com", "password": "Password123"})
        self.assertRedirects(response, reverse("seeker_dashboard"))
        self.assertTrue("_auth_user_id" in self.client.session)

    def test_login_invalid_credentials(self):
        response = self.client.post(reverse("login"), {"email": "login@example.com", "password": "WrongPassword"})
        self.assertContains(response, "Invalid email or password.")
        self.assertFalse("_auth_user_id" in self.client.session)

    def test_login_unverified(self):
        response = self.client.post(reverse("login"), {"email": "unverified@example.com", "password": "Password123"})
        self.assertRedirects(response, reverse("verify_otp"))
        self.assertEqual(self.client.session.get("pending_verify_email"), "unverified@example.com")
        self.assertFalse("_auth_user_id" in self.client.session)

    def test_logout(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("logout"))
        self.assertRedirects(response, reverse("home"))
        self.assertFalse("_auth_user_id" in self.client.session)


class PasswordResetTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="reset@example.com", username="resetuser", password="OldPassword123", is_verified=True
        )

    def test_forgot_password_request(self):
        response = self.client.post(reverse("forgot_password"), {"email": "reset@example.com"})
        self.assertRedirects(response, reverse("reset_password"))
        self.assertEqual(self.client.session.get("reset_email"), "reset@example.com")
        self.assertTrue(OTPVerification.objects.filter(email="reset@example.com", purpose=OTPVerification.Purpose.RESET).exists())

    def test_forgot_password_invalid_email(self):
        response = self.client.post(reverse("forgot_password"), {"email": "wrong@example.com"})
        self.assertContains(response, "No account found with that email.")

    def test_reset_password_valid_otp(self):
        otp = OTPVerification.generate(email="reset@example.com", purpose=OTPVerification.Purpose.RESET, user=self.user)
        session = self.client.session
        session["reset_email"] = "reset@example.com"
        session.save()

        data = {
            "code": otp.otp,
            "password": "NewPassword123",
            "password2": "NewPassword123"
        }
        response = self.client.post(reverse("reset_password"), data)
        self.assertRedirects(response, reverse("login"))
        
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewPassword123"))

    def test_reset_password_invalid_otp(self):
        otp = OTPVerification.generate(email="reset@example.com", purpose=OTPVerification.Purpose.RESET, user=self.user)
        session = self.client.session
        session["reset_email"] = "reset@example.com"
        session.save()

        data = {
            "code": "000000",
            "password": "NewPassword123",
            "password2": "NewPassword123"
        }
        response = self.client.post(reverse("reset_password"), data)
        self.assertContains(response, "Invalid or expired code.")


class SeekerProfileTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.seeker = User.objects.create_user(
            email="seeker1@example.com", username="seeker1", password="Password123", role=User.Role.SEEKER
        )
        JobSeekerProfile.objects.create(user=self.seeker, full_name="Seeker One")
        
        self.recruiter = User.objects.create_user(
            email="recruiter1@example.com", username="recruiter1", password="Password123", role=User.Role.RECRUITER
        )
        Company.objects.create(recruiter=self.recruiter, company_name="Tech Corp")

    def test_profile_access_seeker(self):
        self.client.force_login(self.seeker)
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)

    def test_profile_access_recruiter(self):
        self.client.force_login(self.recruiter)
        response = self.client.get(reverse("profile"))
        self.assertRedirects(response, reverse("recruiter_dashboard"))

    def test_update_profile(self):
        self.client.force_login(self.seeker)
        data = {
            "full_name": "Updated Seeker",
            "phone": "9876543210",
            "location": "New York",
            "headline": "Software Engineer",
            "bio": "Hello World",
            "website": "https://example.com",
            "linkedin": "",
            "github": "",
            "experience_years": "5"
        }
        response = self.client.post(reverse("profile"), data)
        self.assertRedirects(response, reverse("profile"))
        
        self.seeker.refresh_from_db()
        profile = self.seeker.seeker_profile
        self.assertEqual(self.seeker.full_name, "Updated Seeker")
        self.assertEqual(profile.full_name, "Updated Seeker")
        self.assertEqual(profile.location, "New York")
        self.assertEqual(profile.experience_years, 5)

    def test_update_skills(self):
        self.client.force_login(self.seeker)
        data = {
            "section": "skills",
            "skills": "Python, Django, JavaScript"
        }
        response = self.client.post(reverse("profile_sections"), data)
        self.assertRedirects(response, reverse("profile_sections"))
        
        self.seeker.seeker_profile.refresh_from_db()
        profile = self.seeker.seeker_profile
        self.assertEqual(profile.skills, ["Python", "Django", "JavaScript"])

    def test_seeker_change_password(self):
        self.client.force_login(self.seeker)
        data = {
            "action": "change_password",
            "password": "NewPassword123",
            "password2": "NewPassword123"
        }
        response = self.client.post(reverse("seeker_settings"), data)
        self.assertRedirects(response, reverse("seeker_settings"))
        
        self.seeker.refresh_from_db()
        self.assertTrue(self.seeker.check_password("NewPassword123"))
