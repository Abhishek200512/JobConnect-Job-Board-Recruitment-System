from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from companies.models import Company
from jobs.models import Job, Category
from applications.models import Application
from dashboard.models import ContactMessage

class DashboardAccessTests(TestCase):
    def setUp(self):
        self.seeker = User.objects.create_user(
            email="seeker@example.com", username="seeker1", password="password", role=User.Role.SEEKER
        )
        self.recruiter = User.objects.create_user(
            email="recruiter@example.com", username="recruiter1", password="password", role=User.Role.RECRUITER
        )
        self.admin = User.objects.create_user(
            email="admin@example.com", username="admin1", password="password", role=User.Role.ADMIN
        )
        self.client = Client()

    def test_unauthenticated_access(self):
        # Unauthenticated users should be redirected to login for dashboards
        urls = [
            reverse("seeker_dashboard"),
            reverse("recruiter_dashboard"),
            reverse("admin_dashboard"),
            reverse("admin_users"),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)

    def test_seeker_cannot_access_recruiter_admin(self):
        self.client.login(email="seeker@example.com", password="password")
        
        # Access recruiter dashboard
        response = self.client.get(reverse("recruiter_dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("seeker_dashboard"))
        
        # Access admin dashboard
        response = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("seeker_dashboard"))

    def test_recruiter_cannot_access_admin_seeker(self):
        self.client.login(email="recruiter@example.com", password="password")
        
        # Access admin dashboard
        response = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("recruiter_dashboard"))

        # Access seeker dashboard
        response = self.client.get(reverse("seeker_dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("recruiter_dashboard"))

    def test_admin_cannot_access_seeker_recruiter(self):
        self.client.login(email="admin@example.com", password="password")
        
        # Access seeker dashboard
        response = self.client.get(reverse("seeker_dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("admin_dashboard"))

        # Access recruiter dashboard
        response = self.client.get(reverse("recruiter_dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("admin_dashboard"))


class DashboardAnalyticsTests(TestCase):
    def setUp(self):
        self.seeker = User.objects.create_user(
            email="seeker2@example.com", username="seeker2", password="password", role=User.Role.SEEKER
        )
        self.recruiter1 = User.objects.create_user(
            email="rec1@example.com", username="rec1", password="password", role=User.Role.RECRUITER
        )
        self.recruiter2 = User.objects.create_user(
            email="rec2@example.com", username="rec2", password="password", role=User.Role.RECRUITER
        )
        self.admin = User.objects.create_user(
            email="admin2@example.com", username="admin2", password="password", role=User.Role.ADMIN
        )

        self.category = Category.objects.create(name="IT", slug="it")

        self.company1 = Company.objects.create(
            recruiter=self.recruiter1, company_name="Company 1", location="City A"
        )
        self.company2 = Company.objects.create(
            recruiter=self.recruiter2, company_name="Company 2", location="City B"
        )

        self.job1 = Job.objects.create(
            company=self.company1, posted_by=self.recruiter1, title="Job 1", 
            description="desc", category=self.category, location="City A"
        )
        self.job2 = Job.objects.create(
            company=self.company2, posted_by=self.recruiter2, title="Job 2", 
            description="desc", category=self.category, location="City B"
        )

        self.app1 = Application.objects.create(
            job=self.job1, applicant=self.seeker, status=Application.Status.APPLIED
        )
        self.app2 = Application.objects.create(
            job=self.job2, applicant=self.seeker, status=Application.Status.APPLIED
        )

    def test_recruiter_manages_only_own_jobs(self):
        """Recruiter should only see their own jobs and applications in dashboard."""
        self.client.login(email="rec1@example.com", password="password")
        response = self.client.get(reverse("recruiter_dashboard"))
        self.assertEqual(response.status_code, 200)
        
        counts = response.context['counts']
        self.assertEqual(counts['total_jobs'], 1)
        self.assertEqual(counts['applicants'], 1)
        
        my_jobs = response.context['my_jobs']
        self.assertEqual(len(my_jobs), 1)
        self.assertEqual(my_jobs[0], self.job1)

        recent_applications = response.context['recent_applications']
        self.assertEqual(len(recent_applications), 1)
        self.assertEqual(recent_applications[0], self.app1)

    def test_admin_dashboard_analytics_access(self):
        """Admin dashboard should show overall analytics."""
        self.client.login(email="admin2@example.com", password="password")
        response = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(response.status_code, 200)
        
        counts = response.context['counts']
        self.assertEqual(counts['users'], 4)  # 1 seeker + 2 recruiters + 1 admin
        self.assertEqual(counts['seekers'], 1)
        self.assertEqual(counts['recruiters'], 2)
        self.assertEqual(counts['companies'], 2)
        self.assertEqual(counts['jobs'], 2)
        self.assertEqual(counts['applications'], 2)

    def test_admin_reports_access(self):
        self.client.login(email="admin2@example.com", password="password")
        response = self.client.get(reverse("admin_reports"))
        self.assertEqual(response.status_code, 200)
        self.assertIn('jobs_by_cat', response.context)
        self.assertIn('apps_by_month', response.context)


class AdminActionTests(TestCase):
    def setUp(self):
        self.seeker = User.objects.create_user(
            email="seeker3@example.com", username="seeker3", password="password", role=User.Role.SEEKER
        )
        self.admin = User.objects.create_user(
            email="admin3@example.com", username="admin3", password="password", role=User.Role.ADMIN
        )
        self.recruiter = User.objects.create_user(
            email="rec3@example.com", username="rec3", password="password", role=User.Role.RECRUITER
        )
        self.company = Company.objects.create(
            recruiter=self.recruiter, company_name="Company 3"
        )
        self.category = Category.objects.create(name="HR", slug="hr")
        self.job = Job.objects.create(
            company=self.company, posted_by=self.recruiter, title="Job 3", 
            description="desc", category=self.category, location="City C"
        )

    def test_admin_toggle_user_requires_admin(self):
        self.client.login(email="seeker3@example.com", password="password")
        response = self.client.post(reverse("admin_toggle_user", args=[self.seeker.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"], "Unauthorized")

    def test_admin_toggle_user_success(self):
        self.client.login(email="admin3@example.com", password="password")
        self.assertTrue(self.seeker.is_active)
        
        # Toggle off
        response = self.client.post(reverse("admin_toggle_user", args=[self.seeker.pk]))
        self.assertEqual(response.status_code, 200)
        self.seeker.refresh_from_db()
        self.assertFalse(self.seeker.is_active)
        
        # Toggle on
        response = self.client.post(reverse("admin_toggle_user", args=[self.seeker.pk]))
        self.assertEqual(response.status_code, 200)
        self.seeker.refresh_from_db()
        self.assertTrue(self.seeker.is_active)

    def test_admin_toggle_job(self):
        self.client.login(email="admin3@example.com", password="password")
        self.assertEqual(self.job.status, Job.Status.ACTIVE)
        
        response = self.client.post(reverse("admin_toggle_job", args=[self.job.pk]))
        self.assertEqual(response.status_code, 200)
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, Job.Status.INACTIVE)

    def test_admin_delete_company(self):
        self.client.login(email="admin3@example.com", password="password")
        company_id = self.company.pk
        response = self.client.post(reverse("admin_delete_company", args=[company_id]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Company.objects.filter(pk=company_id).exists())


class PublicPagesTests(TestCase):
    def test_home_page(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

    def test_about_page(self):
        response = self.client.get(reverse("about"))
        self.assertEqual(response.status_code, 200)

    def test_contact_page(self):
        response = self.client.get(reverse("contact"))
        self.assertEqual(response.status_code, 200)

    def test_contact_form_submission(self):
        data = {
            "name": "Test User",
            "email": "test@example.com",
            "subject": "Hello",
            "message": "This is a test message."
        }
        response = self.client.post(reverse("contact"), data)
        self.assertEqual(response.status_code, 302)  # Redirects back to contact
        self.assertEqual(ContactMessage.objects.count(), 1)
        msg = ContactMessage.objects.first()
        self.assertEqual(msg.email, "test@example.com")
