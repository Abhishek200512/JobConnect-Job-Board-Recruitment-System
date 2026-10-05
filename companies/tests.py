from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from companies.models import Company
from jobs.models import Job, Category
from rest_framework.test import APIClient

User = get_user_model()

class CompanyModelTest(TestCase):
    def setUp(self):
        self.recruiter = User.objects.create_user(
            email="recruiter@test.com", username="recruiter", password="pwd", role=User.Role.RECRUITER
        )
        self.company = Company.objects.create(
            recruiter=self.recruiter,
            company_name="Tech Innovations",
            description="Innovative tech company.",
            industry="IT"
        )

    def test_company_str(self):
        self.assertEqual(str(self.company), "Tech Innovations")

class CompanyViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.recruiter1 = User.objects.create_user(
            email="rec1@test.com", username="rec1", password="pwd", role=User.Role.RECRUITER
        )
        self.recruiter2 = User.objects.create_user(
            email="rec2@test.com", username="rec2", password="pwd", role=User.Role.RECRUITER
        )
        self.seeker = User.objects.create_user(
            email="seeker@test.com", username="seeker", password="pwd", role=User.Role.SEEKER
        )
        self.company1 = Company.objects.create(
            recruiter=self.recruiter1,
            company_name="Alpha Corp",
            industry="Software",
            location="New York"
        )
        self.company2 = Company.objects.create(
            recruiter=self.recruiter2,
            company_name="Beta LLC",
            industry="Hardware",
            location="San Francisco"
        )
        self.category = Category.objects.create(name="Engineering", slug="engineering")
        
        self.job1 = Job.objects.create(
            company=self.company1,
            posted_by=self.recruiter1,
            title="Software Dev",
            description="Code well.",
            category=self.category,
            status=Job.Status.ACTIVE
        )
        self.job2 = Job.objects.create(
            company=self.company2,
            posted_by=self.recruiter2,
            title="Hardware Tech",
            description="Fix well.",
            category=self.category,
            status=Job.Status.INACTIVE
        )

    def test_company_list_view(self):
        url = reverse("company_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.company1, response.context["companies"])
        self.assertIn(self.company2, response.context["companies"])
        self.assertIn("Software", response.context["industries"])

    def test_company_list_search(self):
        url = reverse("company_list")
        response = self.client.get(url, {"q": "Alpha"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.company1, response.context["companies"])
        self.assertNotIn(self.company2, response.context["companies"])

    def test_company_list_industry_filter(self):
        url = reverse("company_list")
        response = self.client.get(url, {"industry": "Hardware"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(self.company1, response.context["companies"])
        self.assertIn(self.company2, response.context["companies"])

    def test_company_detail_view(self):
        url = reverse("company_detail", args=[self.company1.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["company"], self.company1)
        self.assertIn(self.job1, response.context["jobs"])

    def test_company_detail_inactive_jobs_hidden(self):
        url = reverse("company_detail", args=[self.company2.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["jobs"]), 0)

    def test_company_profile_get_unauthenticated(self):
        url = reverse("company_profile")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_company_profile_get_forbidden_for_seeker(self):
        self.client.login(email="seeker@test.com", password="pwd")
        url = reverse("company_profile")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_company_profile_get_recruiter(self):
        self.client.login(email="rec1@test.com", password="pwd")
        url = reverse("company_profile")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["company"], self.company1)

    def test_company_profile_post_new_company(self):
        rec3 = User.objects.create_user(
            email="rec3@test.com", username="rec3", password="pwd", role=User.Role.RECRUITER
        )
        self.client.login(email="rec3@test.com", password="pwd")
        url = reverse("company_profile")
        response = self.client.post(url, {
            "company_name": "Gamma Inc",
            "industry": "Finance"
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Company.objects.filter(company_name="Gamma Inc").exists())

    def test_company_profile_post_missing_name(self):
        self.client.login(email="rec1@test.com", password="pwd")
        url = reverse("company_profile")
        response = self.client.post(url, {
            "company_name": "",
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Company.objects.get(pk=self.company1.pk).company_name, "Alpha Corp")

    def test_company_profile_post_duplicate_name(self):
        self.client.login(email="rec1@test.com", password="pwd")
        url = reverse("company_profile")
        response = self.client.post(url, {
            "company_name": "Beta LLC", # already belongs to rec2
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Company.objects.get(pk=self.company1.pk).company_name, "Alpha Corp")

    def test_company_profile_update(self):
        self.client.login(email="rec1@test.com", password="pwd")
        url = reverse("company_profile")
        response = self.client.post(url, {
            "company_name": "Alpha Corp Updated",
            "industry": "Software Updated"
        })
        self.assertEqual(response.status_code, 302)
        self.company1.refresh_from_db()
        self.assertEqual(self.company1.company_name, "Alpha Corp Updated")
        self.assertEqual(self.company1.industry, "Software Updated")


class CompanyAPIViewsTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.recruiter = User.objects.create_user(
            email="rec_api@test.com", username="rec_api", password="pwd", role=User.Role.RECRUITER
        )
        self.company1 = Company.objects.create(
            recruiter=self.recruiter,
            company_name="API Company 1",
            industry="API",
            location="Seattle"
        )
        self.company2 = Company.objects.create(
            recruiter=self.recruiter,
            company_name="API Company 2",
            industry="Web",
            location="Austin"
        )
        self.category = Category.objects.create(name="Tech", slug="tech")
        Job.objects.create(
            company=self.company1,
            posted_by=self.recruiter,
            title="API Dev",
            description="Code well.",
            category=self.category,
            status=Job.Status.ACTIVE
        )

    def test_api_company_list(self):
        url = reverse("api_companies")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Should return both companies
        results = response.data["results"]
        self.assertEqual(len(results), 2)
        # company1 should have 1 open job
        c1_data = next(c for c in results if c["id"] == self.company1.pk)
        self.assertEqual(c1_data["open_jobs"], 1)
        # company2 should have 0 open jobs
        c2_data = next(c for c in results if c["id"] == self.company2.pk)
        self.assertEqual(c2_data["open_jobs"], 0)

    def test_api_company_list_search(self):
        url = reverse("api_companies")
        response = self.client.get(url, {"q": "1"})
        self.assertEqual(response.status_code, 200)
        results = response.data["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], self.company1.id)

    def test_api_company_list_industry(self):
        url = reverse("api_companies")
        response = self.client.get(url, {"industry": "Web"})
        self.assertEqual(response.status_code, 200)
        results = response.data["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], self.company2.id)

    def test_api_company_detail(self):
        url = reverse("api_company_detail", args=[self.company1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["company_name"], "API Company 1")
        self.assertEqual(response.data["recruiter_email"], "rec_api@test.com")
