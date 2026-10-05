from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User, JobSeekerProfile
from jobs.models import Category, Job
from companies.models import Company
from applications.models import Application, SavedJob
from django.core.files.uploadedfile import SimpleUploadedFile
import json

class ApplicationsTestCase(TestCase):
    def setUp(self):
        self.seeker = User.objects.create_user(
            email="seeker@example.com",
            username="seeker",
            password="password123",
            role=User.Role.SEEKER
        )
        self.seeker_profile = JobSeekerProfile.objects.create(
            user=self.seeker,
            full_name="Test Seeker"
        )
        
        self.recruiter = User.objects.create_user(
            email="recruiter@example.com",
            username="recruiter",
            password="password123",
            role=User.Role.RECRUITER
        )
        self.company = Company.objects.create(
            recruiter=self.recruiter,
            company_name="Test Company"
        )
        self.category = Category.objects.create(
            name="IT",
            slug="it"
        )
        self.job = Job.objects.create(
            company=self.company,
            posted_by=self.recruiter,
            title="Software Engineer",
            category=self.category,
            location="Remote",
            status=Job.Status.ACTIVE
        )

    def test_apply_for_job_success(self):
        self.client.login(email="seeker@example.com", password="password123")
        
        resume_file = SimpleUploadedFile(
            "resume.pdf",
            b"file_content",
            content_type="application/pdf"
        )
        response = self.client.post(reverse("apply_job", args=[self.job.pk]), {
            "resume": resume_file,
            "cover_letter": "My cover letter",
            "expected_salary": "100000.00",
            "notice_period": "30 days"
        })
        self.assertRedirects(response, reverse("applied_jobs"))
        self.assertEqual(Application.objects.count(), 1)
        app = Application.objects.first()
        self.assertEqual(app.job, self.job)
        self.assertEqual(app.applicant, self.seeker)
        self.assertEqual(app.cover_letter, "My cover letter")

    def test_apply_for_job_without_resume(self):
        self.client.login(email="seeker@example.com", password="password123")
        response = self.client.post(reverse("apply_job", args=[self.job.pk]), {
            "cover_letter": "My cover letter"
        })
        self.assertRedirects(response, reverse("apply_job", args=[self.job.pk]))
        self.assertEqual(Application.objects.count(), 0)

    def test_duplicate_application_prevention(self):
        Application.objects.create(
            job=self.job,
            applicant=self.seeker
        )
        self.client.login(email="seeker@example.com", password="password123")
        response = self.client.post(reverse("apply_job", args=[self.job.pk]), {
            "cover_letter": "Another letter"
        })
        self.assertRedirects(response, reverse("job_detail", args=[self.job.pk]))
        self.assertEqual(Application.objects.count(), 1)

    def test_application_status_update(self):
        app = Application.objects.create(
            job=self.job,
            applicant=self.seeker,
            status=Application.Status.APPLIED
        )
        self.client.login(email="recruiter@example.com", password="password123")
        response = self.client.post(reverse("update_status", args=[app.pk]), {
            "status": Application.Status.SHORTLISTED,
            "note": "Looking good"
        })
        self.assertEqual(response.status_code, 200)
        app.refresh_from_db()
        self.assertEqual(app.status, Application.Status.SHORTLISTED)
        self.assertEqual(app.recruiter_note, "Looking good")

    def test_save_unsave_job(self):
        self.client.login(email="seeker@example.com", password="password123")
        
        # Save job
        response = self.client.post(reverse("toggle_save_job", args=[self.job.pk]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["saved"])
        self.assertEqual(SavedJob.objects.count(), 1)
        
        # Unsave job
        response = self.client.post(reverse("toggle_save_job", args=[self.job.pk]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data["saved"])
        self.assertEqual(SavedJob.objects.count(), 0)
