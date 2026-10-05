"""Seed realistic demo data: categories, recruiters+companies, seekers, jobs, applications."""
import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User, JobSeekerProfile
from applications.models import Application, SavedJob
from companies.models import Company
from jobs.models import Category, Job
from notifications.models import Notification

CATEGORIES = [
    ("Software Development", "💻"), ("Data Science", "📊"), ("Cybersecurity", "🛡️"),
    ("Web Development", "🌐"), ("AI / Machine Learning", "🤖"), ("Marketing", "📣"),
    ("Finance", "💰"), ("Human Resources", "🧑‍💼"),
]

COMPANIES = [
    {
        "name": "TechNova Solutions", "email": "hr@technova.com", "username": "technova_hr",
        "recruiter": "Anita Desai", "industry": "Information Technology", "location": "Bengaluru, Karnataka",
        "website": "https://technova.example.com", "size": "200-500", "founded": 2012,
        "desc": "TechNova Solutions builds scalable enterprise software and cloud platforms for global clients. We believe in developer-first culture, continuous learning and shipping products that matter.",
    },
    {
        "name": "CodeSphere Technologies", "email": "hr@codesphere.com", "username": "codesphere_hr",
        "recruiter": "Rohit Kapoor", "industry": "Software Products", "location": "Pune, Maharashtra",
        "website": "https://codesphere.example.com", "size": "50-200", "founded": 2017,
        "desc": "CodeSphere Technologies crafts modern web and mobile products for startups worldwide. Small teams, big impact, and a strong focus on mentorship.",
    },
    {
        "name": "DataBridge Labs", "email": "hr@databridge.com", "username": "databridge_hr",
        "recruiter": "Meera Iyer", "industry": "Data & Analytics", "location": "Hyderabad, Telangana",
        "website": "https://databridge.example.com", "size": "50-200", "founded": 2019,
        "desc": "DataBridge Labs helps enterprises turn raw data into decisions with ML pipelines, analytics platforms and dashboards.",
    },
    {
        "name": "CloudCore Systems", "email": "hr@cloudcore.com", "username": "cloudcore_hr",
        "recruiter": "Vikram Nair", "industry": "Cloud Infrastructure", "location": "Chennai, Tamil Nadu",
        "website": "https://cloudcore.example.com", "size": "200-500", "founded": 2015,
        "desc": "CloudCore Systems runs mission-critical cloud infrastructure and DevOps tooling for fintech and e-commerce companies.",
    },
]

SEEKERS = [
    ("Arjun Mehta", "arjun.mehta@example.com", "arjunmehta", "Full Stack Developer | Python · Django · React", "Bengaluru", 3,
     ["Python", "Django", "JavaScript", "React", "PostgreSQL", "Git"],
     [{"degree": "B.Tech Computer Science", "institution": "VIT Vellore", "year": "2022"}],
     [{"title": "Software Engineer", "company": "Infotech Labs", "duration": "Jul 2022 – Present"}]),
    ("Priya Sharma", "priya.sharma@example.com", "priyasharma", "Data Analyst | SQL · Python · Power BI", "Pune", 2,
     ["SQL", "Python", "Power BI", "Excel", "Statistics", "Pandas"],
     [{"degree": "B.Sc Statistics", "institution": "Fergusson College", "year": "2023"}],
     [{"title": "Data Analyst Intern", "company": "MarketMetrics", "duration": "Jan 2023 – Jun 2023"}]),
    ("Rahul Verma", "rahul.verma@example.com", "rahulverma", "DevOps Engineer | AWS · Docker · Kubernetes", "Hyderabad", 4,
     ["AWS", "Docker", "Kubernetes", "Linux", "Terraform", "CI/CD"],
     [{"degree": "B.E. Information Technology", "institution": "Osmania University", "year": "2021"}],
     [{"title": "DevOps Engineer", "company": "Cloudify", "duration": "Aug 2021 – Present"}]),
    ("Sneha Patil", "sneha.patil@example.com", "snehapatil", "Frontend Developer | React · TypeScript", "Mumbai", 1,
     ["JavaScript", "TypeScript", "React", "Bootstrap", "CSS3", "Figma"],
     [{"degree": "BCA", "institution": "Mumbai University", "year": "2024"}],
     []),
]

JOBS = [
    ("TechNova Solutions", "Senior Python Developer", "software-development", "Bengaluru, Karnataka", "full_time", "hybrid", "senior",
     1800000, 2800000, 3, ["Python", "Django", "REST APIs", "PostgreSQL", "AWS"],
     "We are looking for a Senior Python Developer to design and build high-performance backend services powering our enterprise platform. You will own features end-to-end, mentor junior engineers and collaborate with product and DevOps teams.",
     "Design and develop scalable backend services\nReview code and mentor junior developers\nOptimize database queries and API performance\nCollaborate with frontend and DevOps teams",
     "5+ years of Python experience\nStrong Django and REST framework knowledge\nExperience with PostgreSQL and AWS\nSolid understanding of system design",
     "Health insurance for family\nFlexible hybrid work\nAnnual learning budget\nPerformance bonus"),
    ("TechNova Solutions", "Frontend Developer (React)", "web-development", "Bengaluru, Karnataka", "full_time", "remote", "mid",
     1200000, 1800000, 2, ["React", "JavaScript", "TypeScript", "CSS3", "REST APIs"],
     "Join the frontend guild building our customer-facing dashboard used by thousands of businesses daily. You'll craft pixel-perfect, accessible UI components.",
     "Build reusable React components\nTranslate Figma designs to pixel-perfect UI\nImprove accessibility and performance\nWork with designers and backend engineers",
     "3+ years with React\nStrong JavaScript/TypeScript fundamentals\nExperience with responsive design\nEye for detail and UX",
     "Fully remote role\nHome office stipend\nQuarterly team offsites"),
    ("CodeSphere Technologies", "Django Intern", "web-development", "Pune, Maharashtra", "internship", "onsite", "fresher",
     15000, 25000, 5, ["Python", "Django", "HTML5", "CSS3", "Git"],
     "A 6-month internship for strong Python fundamentals. You'll ship real features with mentorship from senior engineers and get a pre-placement offer on good performance.",
     "Build and test Django views and templates\nFix bugs and write unit tests\nParticipate in daily standups and code reviews",
     "Final-year student or recent graduate\nSolid Python basics\nUnderstanding of HTML/CSS\nEager to learn Django",
     "Mentorship from senior engineers\nPre-placement offer opportunity\nCertificate on completion\nFree lunch"),
    ("CodeSphere Technologies", "UI/UX Designer", "software-development", "Pune, Maharashtra", "full_time", "hybrid", "junior",
     700000, 1100000, 1, ["Figma", "Wireframing", "Prototyping", "Design Systems", "User Research"],
     "Own design for our flagship product: conduct user research, create flows and prototypes, and maintain our design system.",
     "Create wireframes and high-fidelity mockups\nRun usability testing sessions\nMaintain and grow the design system\nPartner with frontend developers",
     "2+ years of product design experience\nPortfolio showcasing real products\nFluency with Figma\nStrong communication skills",
     "Hybrid schedule\nLatest MacBook Pro\nDesign conference budget"),
    ("DataBridge Labs", "Data Scientist", "data-science", "Hyderabad, Telangana", "full_time", "hybrid", "mid",
     1500000, 2400000, 2, ["Python", "Machine Learning", "SQL", "Pandas", "Scikit-learn", "Statistics"],
     "Build predictive models and experiments that directly shape product decisions. From feature engineering to production deployment, you'll own the ML lifecycle.",
     "Develop and deploy ML models\nDesign A/B experiments and analyze results\nBuild data pipelines with the data engineering team\nPresent insights to stakeholders",
     "3+ years in data science or ML\nStrong Python and SQL\nHands-on with scikit-learn or similar\nGreat storytelling with data",
     "Stock options\nHealth insurance\nRelocation support\nLearning & certification budget"),
    ("DataBridge Labs", "Business Intelligence Analyst", "data-science", "Hyderabad, Telangana", "full_time", "remote", "junior",
     600000, 900000, 4, ["SQL", "Power BI", "Excel", "Python", "Data Visualization"],
     "Turn messy data into dashboards leadership actually uses. You'll work across marketing, sales and product teams.",
     "Build and maintain Power BI dashboards\nWrite efficient SQL queries\nAutomate recurring reports\nPartner with business teams on KPIs",
     "1-3 years of BI/analytics experience\nAdvanced SQL skills\nPower BI or Tableau proficiency\nAttention to detail",
     "Remote-first company\nAnnual retreat\nInternet reimbursement"),
    ("CloudCore Systems", "DevOps Engineer", "cybersecurity", "Chennai, Tamil Nadu", "full_time", "onsite", "mid",
     1400000, 2200000, 2, ["AWS", "Kubernetes", "Terraform", "CI/CD", "Linux", "Docker"],
     "Keep our production platform fast, safe and always-on. You'll automate deployments, harden infrastructure and lead incident response.",
     "Manage Kubernetes clusters in production\nAutomate infrastructure with Terraform\nBuild and improve CI/CD pipelines\nLead incident postmortems",
     "3+ years in DevOps/SRE roles\nDeep AWS and Kubernetes knowledge\nInfrastructure-as-code experience\nOn-call mindset with calm under pressure",
     "On-site with free meals\nComprehensive insurance\nCertification sponsorship"),
    ("CloudCore Systems", "Cybersecurity Analyst", "cybersecurity", "Chennai, Tamil Nadu", "full_time", "hybrid", "junior",
     800000, 1200000, 1, ["Network Security", "SIEM", "Penetration Testing", "Linux", "Incident Response"],
     "Join our security operations center monitoring threats across a large cloud estate and responding to real incidents.",
     "Monitor SIEM alerts and triage incidents\nPerform vulnerability assessments\nHarden systems and document runbooks\nSupport compliance audits",
     "1-3 years in security operations\nKnowledge of networking and Linux\nCertification (CEH/Security+) a plus\nCuriosity and integrity",
     "Shift-flexible hybrid\nTraining budget\nInsurance for dependents"),
    ("TechNova Solutions", "AI/ML Engineer", "ai-machine-learning", "Bengaluru, Karnataka", "full_time", "hybrid", "senior",
     2200000, 3200000, 1, ["PyTorch", "NLP", "MLOps", "Python", "LLMs"],
     "Drive our applied-AI initiatives: from LLM-powered internal tools to classic ML in production, working with a dedicated research pod.",
     "Prototype and productionize ML features\nFine-tune and evaluate LLMs for internal use\nBuild MLOps pipelines for training and serving\nPublish internal best practices",
     "5+ years in ML engineering\nProduction PyTorch experience\nLLM fine-tuning a strong plus\nStrong software engineering fundamentals",
     "Top-of-market pay\nResearch conference budget\nESOPs"),
    ("DataBridge Labs", "Digital Marketing Specialist", "marketing", "Hyderabad, Telangana", "part_time", "remote", "junior",
     300000, 480000, 2, ["SEO", "Content Marketing", "Google Analytics", "Social Media", "Copywriting"],
     "Own our content engine: SEO-optimized articles, campaign landing pages and social presence for a data brand.",
     "Plan and publish SEO content\nManage social channels\nTrack campaign analytics\nCoordinate with designers",
     "1-3 years in digital marketing\nSEO best-practice knowledge\nExcellent writing skills\nAnalytics comfort",
     "Flexible part-time hours\nFully remote\nPerformance incentives"),
]

APPLICATION_STATUSES = ["applied", "under_review", "shortlisted", "interview", "selected", "rejected"]


class Command(BaseCommand):
    help = "Seed realistic demo data (idempotent: skips if data already exists)."

    def handle(self, *args, **options):
        if User.objects.filter(email__iexact="admin@jobconnect.com").exists():
            self.stdout.write(self.style.WARNING("Demo data already present — skipping."))
            return

        # ----- Admin -----
        User.objects.create_superuser(
            email="admin@jobconnect.com", password="Admin@1234", username="admin",
            full_name="Platform Admin",
        )
        self.stdout.write("[OK] Admin: admin@jobconnect.com / Admin@1234")

        # ----- Categories -----
        for name, icon in CATEGORIES:
            from django.utils.text import slugify
            Category.objects.get_or_create(name=name, defaults={"slug": slugify(name), "icon": icon})
        self.stdout.write(f"[OK] {len(CATEGORIES)} categories")

        # ----- Recruiters + companies -----
        now0 = timezone.now()
        companies = {}
        for c in COMPANIES:
            recruiter = User.objects.create_user(
                email=c["email"], password="Recruiter@1234", username=c["username"],
                full_name=c["recruiter"], role=User.Role.RECRUITER, is_verified=True,
            )
            # Backdate registration for realistic trend charts
            User.objects.filter(pk=recruiter.pk).update(created_at=now0 - timedelta(days=random.randint(200, 700)))
            companies[c["name"]] = Company.objects.create(
                recruiter=recruiter, company_name=c["name"], industry=c["industry"],
                location=c["location"], website=c["website"], size=c["size"],
                founded_year=c["founded"], description=c["desc"],
            )
        self.stdout.write(f"[OK] {len(COMPANIES)} recruiters + companies (password: Recruiter@1234)")

        # ----- Jobs -----
        jobs = []
        job_ages = {}
        now = timezone.now()
        for (company_name, title, cat_slug, location, jtype, mode, exp,
             smin, smax, openings, skills, desc, resp, qual, benefits) in JOBS:
            job = Job.objects.create(
                company=companies[company_name],
                posted_by=companies[company_name].recruiter,
                title=title, description=desc,
                responsibilities=resp, qualifications=qual, benefits=benefits,
                skills=skills, category=Category.objects.get(slug=cat_slug),
                location=location, job_type=jtype, work_mode=mode, experience=exp,
                salary_min=smin, salary_max=smax, openings=openings,
                status=Job.Status.ACTIVE,
            )
            # Spread postings over ~5 months, with some fresh ones for realism
            age = random.randint(0, 10) if random.random() < 0.3 else random.randint(3, 150)
            Job.objects.filter(pk=job.pk).update(created_at=now - timedelta(days=age))
            job_ages[job.pk] = age
            jobs.append(job)
        # one inactive job for realism
        jobs[-1].status = Job.Status.INACTIVE
        jobs[-1].save(update_fields=["status"])
        self.stdout.write(f"[OK] {len(JOBS)} jobs")

        # ----- Seekers -----
        seekers = []
        for name, email, username, headline, location, exp_years, skills, edu, exp in SEEKERS:
            seeker = User.objects.create_user(
                email=email, password="Seeker@1234", username=username,
                full_name=name, role=User.Role.SEEKER, is_verified=True,
            )
            # Backdate registration for realistic trend charts
            User.objects.filter(pk=seeker.pk).update(created_at=now0 - timedelta(days=random.randint(10, 180)))
            JobSeekerProfile.objects.create(
                user=seeker, full_name=name, headline=headline, location=location,
                experience_years=exp_years, skills=skills, education=edu, experience=exp,
                bio=f"Passionate professional focused on delivering quality work. Skills: {', '.join(skills[:4])}.",
            )
            seekers.append(seeker)
        self.stdout.write(f"[OK] {len(SEEKERS)} job seekers (password: Seeker@1234)")

        # ----- Applications (spread over last 5 months) -----
        count = 0
        for seeker in seekers:
            chosen = random.sample(jobs, k=random.randint(3, 6))
            for job in chosen:
                if Application.objects.filter(job=job, applicant=seeker).exists():
                    continue
                status = random.choice(APPLICATION_STATUSES)
                # Can't predate the job posting; ~30% applied very recently
                cap = max(0, min(140, job_ages[job.pk]))
                days_ago = random.randint(0, min(7, cap)) if random.random() < 0.3 else random.randint(0, cap)
                Application.objects.create(
                    job=job, applicant=seeker,
                    cover_letter=f"I am excited to apply for {job.title}. With my background, I believe I can contribute from day one.",
                    expected_salary=random.choice([600000, 900000, 1200000, 1600000]),
                    notice_period=random.choice(["Immediate", "1 month", "2 months"]),
                    status=status,
                )
                Application.objects.filter(job=job, applicant=seeker).update(
                    applied_at=now - timedelta(days=days_ago)
                )
                count += 1
            Notification.notify(
                seeker, "Welcome to JobConnect 🎉",
                "Your demo profile is ready. Explore jobs and apply today!",
                url="/jobs/",
            )
        SavedJob.objects.get_or_create(user=seekers[0], job=jobs[0])
        SavedJob.objects.get_or_create(user=seekers[1], job=jobs[4])
        self.stdout.write(f"[OK] {count} applications + saved jobs + notifications")
        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully."))
