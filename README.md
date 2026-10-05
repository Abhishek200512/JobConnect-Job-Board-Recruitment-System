# JobConnect – Job Board & Recruitment Management System

## Project Overview

JobConnect is a full-stack, production-ready recruitment platform that bridges the gap between job seekers and recruiters. It features a modern, responsive UI/UX, robust role-based authentication, and a complete application tracking system.

## Features

### Job Seeker
- Registration/Login with secure OTP verification
- Comprehensive profile management (skills, education, experience)
- Resume & profile photo upload
- Advanced job search with multi-faceted filtering
- Save jobs for later review
- One-click job application
- Live application status tracking via dashboard
- Real-time notifications for application updates

### Recruiter
- Recruiter authentication & company verification
- Dedicated company profile page
- Create, edit, and delete job postings
- Review and filter applicant resumes
- Applicant pipeline management
- Update application statuses (Under Review, Shortlisted, Interview, Selected, Rejected)
- Interview management and candidate communication

### Admin
- Global user management
- Platform-wide company and job listing moderation
- Application oversight
- High-level analytics and reporting

---

## Technology Stack

**Frontend:**
- HTML5 & CSS3
- JavaScript (Vanilla / ES6+)
- Bootstrap 5 (Customized Professional UI)
- AJAX / Fetch API (for async saves/applications)
- Chart.js (Dashboard Analytics)

**Backend:**
- Python 3.x
- Django 5.x
- Django REST Framework (DRF)
- Django ORM

**Database:**
- MySQL (Production ready via `mysqlclient`)
- SQLite3 (Fallback for local testing)

**Testing:**
- Django Test Framework (Unit/Integration)
- Playwright (Headless Browser UI/Responsive QA)

---

## Project Structure

```text
JobConnect/
│
├── accounts/          # Custom User model, OTP Auth, Roles
├── applications/      # Job applications, statuses, resume uploads
├── companies/         # Company profiles and recruiter links
├── dashboard/         # Role-based dashboards (Seeker/Recruiter/Admin)
├── jobconnect_project/# Main Django settings and WSGI/ASGI configs
├── jobs/              # Job postings, categories, and search
├── notifications/     # In-app notifications
│
├── media/             # User-uploaded files (resumes, logos)
├── static/            # CSS, JS, Images (Design System)
├── templates/         # Django HTML templates
│
├── .env.example       # Example environment variables
├── .gitignore         # Git ignore rules
├── manage.py          # Django entry point
├── requirements.txt   # Python dependencies
└── README.md          # Project documentation
```

---

## Installation Guide (Windows)

1. **Clone the repository:**
   ```powershell
   git clone <repository-url>
   cd "Job Board & Recruitment Management System"
   ```

2. **Set up the virtual environment:**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Environment Configuration:**
   Copy `.env.example` to `.env` and fill in your local details (DB, Secret Key, etc.).

5. **MySQL Database Setup:**
   Ensure MySQL is running, then log in and create the database:
   ```sql
   CREATE DATABASE jobconnect_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

6. **Run Migrations:**
   ```powershell
   python manage.py migrate
   ```

7. **Create Superuser (Admin):**
   ```powershell
   python manage.py createsuperuser
   ```

8. **Start the Development Server:**
   ```powershell
   python manage.py runserver
   ```
   Open your browser and navigate to: `http://127.0.0.1:8000/`

---

## Testing Results

The project includes a comprehensive suite of automated and manual tests.

```text
Django system check: PASS
Automated backend tests: 82/82 PASS
Playwright browser QA (Desktop/Tablet/Mobile): PASS
Console errors: 0
API/AJAX errors: 0
Responsive overflow issues: 0
```

To run backend tests locally:
```powershell
python manage.py test
```

---

## Screenshots

*(Insert actual screenshots of the application here once deployed)*

- **Homepage** `[placeholder: /docs/screenshots/home.png]`
- **Job Search & Filters** `[placeholder: /docs/screenshots/jobs.png]`
- **Job Details** `[placeholder: /docs/screenshots/job-detail.png]`
- **Job Seeker Dashboard** `[placeholder: /docs/screenshots/seeker-dash.png]`
- **Recruiter Dashboard** `[placeholder: /docs/screenshots/recruiter-dash.png]`
- **Login / Register** `[placeholder: /docs/screenshots/auth.png]`

---

## Deployment Configuration

JobConnect is structurally prepared for production deployment. 

**Requirements for Production:**
- **WSGI Server:** Gunicorn or Waitress
- **Web Server:** Nginx (for Reverse Proxy and Static/Media serving)
- **Database:** MySQL
- **Security:** HTTPS/SSL certificates

**Deployment Steps Overview:**
1. Configure a production VPS (e.g., DigitalOcean, AWS EC2) or PaaS (e.g., Railway).
2. Set `DEBUG=False` in your production environment variables.
3. Configure `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` to match your domain.
4. Run `python manage.py collectstatic` to gather static files.
5. Set up an S3 bucket or local persistent block storage for the `/media/` directory to prevent uploaded resumes/logos from being lost across deployments.

**Recommended Platform:**
**Railway** or **Render** are recommended for this stack, as they provide managed MySQL instances and support persistent disk volumes necessary for Django's local `MEDIA_ROOT` file uploads. Alternatively, an inexpensive VPS (like DigitalOcean Droplet) with Nginx/Gunicorn is an excellent traditional choice.
