# Blog API - Django REST Framework Project

A Django REST API project for managing a blog with user authentication, private posts, and comment notifications using Celery for asynchronous email notifications.

## Features

- **User Authentication**: Signup with email verification and login using email/password
- **Admin Panel**: Email-based login for Django admin (no username required)
- **Post Management**: Create, list, and retrieve posts with public/private visibility
- **Comment System**: Add comments to public posts with email notifications
- **Asynchronous Tasks**: Celery integration for sending email notifications
- **PostgreSQL Database**: Production-ready database setup
- **RESTful API**: Django REST Framework with class-based views
- **Comprehensive Tests**: Professional test structure with fixtures and organized test files

## Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Redis (for Celery broker)
- Virtual environment (recommended)

## Installation

### 1. Clone the repository and navigate to the project directory

```bash
cd /home/ad/django-blog-api
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv env
source env/bin/activate  
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up PostgreSQL database

Create a PostgreSQL database:

```bash
sudo -u postgres psql
CREATE DATABASE blog;
CREATE USER postgres WITH PASSWORD 'admin';
ALTER ROLE postgres SET client_encoding TO 'utf8';
ALTER ROLE postgres SET default_transaction_isolation TO 'read committed';
ALTER ROLE postgres SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE blog TO postgres;
\q
```

**Note**: The default database configuration in `config/settings.py` uses:
- Database name: `blog`
- User: `postgres`
- Password: `admin`

Update these credentials in `config/settings.py` if you use different values.

### 5. Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create a superuser (optional, for admin access)

```bash
python manage.py createsuperuser
```

**Note**: Admin panel supports email-based login. Use your email and password to login at `http://localhost:8000/admin/`

### 7. Start Redis (required for Celery)

```bash
sudo systemctl start redis-server

```

## Running the Application

### 1. Start the Django development server

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000`

### 2. Start Celery worker (in a separate terminal)

```bash
source env/bin/activate

celery -A config worker -l info
```

### 3. Start Celery beat (optional, for scheduled tasks)

```bash
celery -A config beat -l info
```

## Postman Collection

A Postman collection is included: `Blog_API.postman_collection.json`

To use it:
1. Import the collection into Postman
2. Set the `base_url` variable to `http://localhost:8000`
3. After login, copy the token and set it in the `auth_token` variable
4. Use the collection to test all endpoints

## Configuration

### Email Settings

By default, emails are sent to the console (for development). To configure SMTP:

Edit `config/settings.py`:

```python
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "your-email@gmail.com"
EMAIL_HOST_PASSWORD = "your-password"
```

### Database Configuration

Update database settings in `config/settings.py` if needed:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "blog",
        "USER": "postgres",
        "PASSWORD": "admin",
        "HOST": "localhost",
        "PORT": "5432",
    }
}
```

### Celery Configuration

Celery is configured to use Redis as the broker. Update `CELERY_BROKER_URL` in `config/settings.py` if your Redis instance is on a different host/port.

## Project Structure

```
django-blog-api/
├── blog/                    # Main application
│   ├── models.py           # Post and Comment models
│   ├── views.py            # API views (class-based)
│   ├── serializers.py      # DRF serializers
│   ├── tasks.py            # Celery tasks
│   ├── urls.py             # URL routing
│   └── admin.py            # Admin configuration (email-based login)
├── tests/                  # Test package (root level)
│   ├── __init__.py         # Test package initialization
│   ├── conftest.py         # Shared fixtures and test configuration
│   ├── test_authentication.py  # Signup & Login tests
│   ├── test_posts.py       # Post API tests
│   └── test_comments.py    # Comment API tests
├── config/                 # Project settings
│   ├── settings.py         # Django settings
│   ├── urls.py             # Root URL configuration
│   ├── celery.py           # Celery configuration
│   └── __init__.py         # Celery app initialization
├── manage.py               # Django management script
├── requirements.txt        # Python dependencies
├── pytest.ini             # Pytest configuration
├── README.md              # This file
└── Blog_API.postman_collection.json  # Postman collection
```

## Testing

The project uses a professional test structure with pytest and Django. Tests are organized in the root-level `tests/` directory with shared fixtures in `conftest.py`.

### Run all tests:
```bash
pytest tests/ -v
```

### Run tests for a specific file:
```bash
pytest tests/test_authentication.py -v
pytest tests/test_posts.py -v
pytest tests/test_comments.py -v
```

### Run tests for a specific class:
```bash
pytest tests/test_authentication.py::TestSignupView -v
pytest tests/test_authentication.py::TestLoginView -v
```

### Run a specific test:
```bash
pytest tests/test_authentication.py::TestSignupView::test_successful_signup -v
```

### Test Structure:
- **tests/conftest.py**: Contains shared fixtures (`api_client`, `create_user`, `authenticated_client`, `create_post`)
- **tests/test_authentication.py**: Tests for signup and login endpoints
- **tests/test_posts.py**: Tests for post creation and management
- **tests/test_comments.py**: Tests for comment addition with Celery task verification


## Troubleshooting

### Database Connection Issues

- Ensure PostgreSQL is running: `sudo systemctl status postgresql`
- Verify database credentials in `config/settings.py`
- Check database exists: `psql -U postgres -l`

### Celery Not Working

- Ensure Redis is running: `redis-cli ping`
- Check Celery worker is running: `celery -A config worker -l info`
- Verify Celery configuration in `config/settings.py`

### Email Not Sending

- For development, emails are sent to console by default
- Check console output when running Django server
- For production, configure SMTP settings in `config/settings.py`

## License

This project is open source and available for educational purposes.

