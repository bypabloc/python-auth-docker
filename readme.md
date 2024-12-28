# Python Authentication Service

A modern authentication service built with Django REST Framework featuring JWT tokens, email verification, and Multi-Factor Authentication (MFA).

## Prerequisites

Before you begin, ensure you have installed:

- Python 3.12+ ([Download](https://www.python.org/downloads/))
- PostgreSQL 16+ ([Download](https://www.postgresql.org/download/))
- pip (comes with Python)
- VS Code (recommended) ([Download](https://code.visualstudio.com/))

### VS Code Extensions

Install these extensions for the best development experience:

- [Black Formatter](https://marketplace.visualstudio.com/items?itemName=ms-python.black-formatter)
- [Ruff](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff)

## Installation Without Docker

1. Clone the repository:

```bash
git clone <repository-url>
cd python-auth-docker
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install development dependencies:

```bash
pip install -r requirements/local.in
```

4. Create a local PostgreSQL database:

```bash
createdb app_db
```

5. Set up your local environment variables. Create a `.env` file in the root directory:

```bash
DEBUG=1
SECRET_KEY='your-secret-key'
DB_NAME=app_db
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
ALLOWED_HOSTS=localhost,127.0.0.1
ENVIRONMENT=local
SEND_VERIFICATION_CODE_IN_RESPONSE=1
```

6. Apply migrations:

```bash
python manage.py migrate
```

7. Create a superuser:

```bash
python manage.py createsuperuser
```

8. Run the development server:

```bash
python manage.py runserver
```

## Development Setup

1. Install pre-commit hooks:

```bash
pre-commit install
```

2. Configure VS Code settings (`settings.json`):

```json
{
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.fixAll": "explicit",
        "source.organizeImports": "explicit"
    },
    "[python]": {
        "editor.defaultFormatter": "ms-python.black-formatter",
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.fixAll": "explicit",
            "source.organizeImports": "explicit"
        }
    },
    "ruff.organizeImports": true,
    "ruff.fixAll": true,
    "black-formatter.args": ["--line-length", "88"]
}
```

## Docker Installation (Alternative)

If you prefer using Docker, refer to the [Docker README](docker/readme.md) for installation instructions.

## Features

- JWT Authentication
- Email Verification
- Multi-Factor Authentication (MFA)
  - Time-based One-Time Password (TOTP)
  - Email Verification
- Session Management
- Pre-commit Hooks
- Code Formatting with Black
- Linting with Ruff

## Development Tools

- **Black**: Python code formatter
- **Ruff**: An extremely fast Python linter
- **pre-commit**: Git hook scripts
- **pytest**: Testing framework
- **mypy**: Static type checking
- **django-debug-toolbar**: Django debugging
- **django-extensions**: Development tools for Django

## API Endpoints

- `/api/register/` - User registration
- `/api/login/` - User login
- `/api/logout/` - User logout
- `/api/verify-code/` - Email verification
- `/api/resend-code/` - Resend verification code
- `/api/mfa/methods/` - List available MFA methods
- `/api/mfa/configure/` - Configure MFA
- `/api/mfa/verify/` - Verify MFA code

## License

[MIT License](LICENSE)
