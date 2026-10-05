from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from accounts.models import User, JobSeekerProfile
from companies.models import Company
from jobs.models import Category, Job
from applications.models import Application, SavedJob
import json

class JobsTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Create Seeker User
        self.seeker = User.objects.create_user(
            email="seeker@example.com",
            username="seeker_user",
            password="password123",
            role=User.Role.SEEKER
        )

        # Create Recruiter User
        self.recruiter = User.objects.create_user(
            email="recruiter@example.com",
            username="recruiter_user",
            password="password123",
            role=User.Role.RECRUITER
        )

        # Create Company for Recruiter
        self.company = Company.objects.create(
            recruiter=self.recruiter,
            company_name="Test Company",
            location="Test City"
        )

        # Create Category
        self.category = Category.objects.create(
            name="IT",
            slug="it"
        )
        self.category2 = Category.objects.create(
            name="Marketing",
            slug="marketing"
        )

        # Create Jobs
        self.active_job = Job.objects.create(
            company=self.company,
            posted_by=self.recruiter,
            title="Software Engineer",
            description="Test Description",
            category=self.category,
            location="New York",
            job_type=Job.JobType.FULL_TIME,
            work_mode=Job.WorkMode.REMOTE,
            experience=Job.Experience.MID,
            salary_min=100000,
            salary_max=150000,
            status=Job.Status.ACTIVE
        )

        self.inactive_job = Job.objects.create(
            company=self.company,
            posted_by=self.recruiter,
            title="Old Engineer Role",
            description="Test Description",
            category=self.category,
            location="Remote",
            status=Job.Status.INACTIVE
        )

    def test_job_model_methods(self):
        self.assertTrue(self.active_job.is_active)
        self.assertFalse(self.inactive_job.is_active)
        self.assertIn("LPA", self.active_job.salary_display())
        
        # Test active_jobs class method
        active_qs = Job.active_jobs()
        self.assertIn(self.active_job, active_qs)
        self.assertNotIn(self.inactive_job, active_qs)

    def test_job_list_view(self):
        url = reverse('job_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Software Engineer")
        self.assertNotContains(response, "Old Engineer Role")

    def test_job_list_filtering(self):
        url = reverse('job_list')
        
        # Filter by keyword
        response = self.client.get(url, {'keyword': 'Software'})
        self.assertContains(response, "Software Engineer")
        
        response = self.client.get(url, {'keyword': 'Manager'})
        self.assertNotContains(response, "Software Engineer")

        # Filter by location
        response = self.client.get(url, {'location': 'New York'})
        self.assertContains(response, "Software Engineer")
        
        response = self.client.get(url, {'location': 'London'})
        self.assertNotContains(response, "Software Engineer")

        # Filter by category
        response = self.client.get(url, {'category': 'it'})
        self.assertContains(response, "Software Engineer")
        
        response = self.client.get(url, {'category': 'marketing'})
        self.assertNotContains(response, "Software Engineer")
        
    def test_job_detail_view(self):
        url = reverse('job_detail', args=[self.active_job.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Software Engineer")
        self.assertContains(response, "Test Company")
        
        # Inactive job detail should return 404
        url_inactive = reverse('job_detail', args=[self.inactive_job.pk])
        response_inactive = self.client.get(url_inactive)
        self.assertEqual(response_inactive.status_code, 404)

    def test_manage_jobs_recruiter_only(self):
        url = reverse('manage_jobs')
        # Unauthenticated
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 200) # Should redirect to login or deny

        # As seeker
        self.client.login(email="seeker@example.com", password="password123")
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 200) # Seekers can't access recruiter views
        
        # As recruiter
        self.client.login(email="recruiter@example.com", password="password123")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Software Engineer")
        self.assertContains(response, "Old Engineer Role")

    def test_post_job(self):
        url = reverse('post_job')
        self.client.login(email="recruiter@example.com", password="password123")
        
        data = {
            'title': 'Data Scientist',
            'category': self.category.pk,
            'location': 'San Francisco',
            'job_type': Job.JobType.FULL_TIME,
            'work_mode': Job.WorkMode.HYBRID,
            'experience': Job.Experience.MID,
            'description': 'Data job description',
            'openings': 2
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('manage_jobs'))
        
        new_job = Job.objects.filter(title='Data Scientist').first()
        self.assertIsNotNone(new_job)
        self.assertEqual(new_job.company, self.company)
        self.assertEqual(new_job.posted_by, self.recruiter)
        
    def test_edit_job(self):
        url = reverse('edit_job', args=[self.active_job.pk])
        self.client.login(email="recruiter@example.com", password="password123")
        
        data = {
            'title': 'Senior Software Engineer',
            'category': self.category.pk,
            'location': 'New York',
            'job_type': Job.JobType.FULL_TIME,
            'work_mode': Job.WorkMode.REMOTE,
            'experience': Job.Experience.SENIOR,
            'description': 'Updated description',
            'openings': 1
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('manage_jobs'))
        
        self.active_job.refresh_from_db()
        self.assertEqual(self.active_job.title, 'Senior Software Engineer')
        self.assertEqual(self.active_job.experience, Job.Experience.SENIOR)

    def test_delete_job(self):
        url = reverse('delete_job', args=[self.inactive_job.pk])
        self.client.login(email="recruiter@example.com", password="password123")
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Job.objects.filter(pk=self.inactive_job.pk).exists())
        
    def test_toggle_job_status(self):
        url = reverse('toggle_job_status', args=[self.active_job.pk])
        self.client.login(email="recruiter@example.com", password="password123")
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.active_job.refresh_from_db()
        self.assertEqual(self.active_job.status, Job.Status.INACTIVE)

    def test_toggle_save_job(self):
        url = reverse('toggle_save_job', args=[self.active_job.pk])
        
        # Logged in as seeker
        self.client.login(email="seeker@example.com", password="password123")
        
        # Save job
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(SavedJob.objects.filter(user=self.seeker, job=self.active_job).exists())
        
        # Unsave job
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(SavedJob.objects.filter(user=self.seeker, job=self.active_job).exists())

    def test_jobs_ajax(self):
        url = reverse('jobs_ajax')
        response = self.client.get(url, {'keyword': 'Software'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn("Software Engineer", data['html'])
        self.assertEqual(data['total'], 1)
