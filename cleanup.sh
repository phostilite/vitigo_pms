#!/bin/bash

echo "Starting Django project cleanup..."

# Kill any running Django server
pkill -f runserver

# Delete migrations and cache files
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -name "__pycache__" -type d -exec rm -r {} +
find . -name "db.sqlite3" -delete

# Deactivate and remove virtual environment
deactivate 2>/dev/null
rm -rf .venv

# Create new virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install requirements
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "Warning: requirements.txt not found"
    exit 1
fi

# Django commands with error handling
python manage.py makemigrations || { echo "Makemigrations failed"; exit 1; }
python manage.py migrate || { echo "Migration failed"; exit 1; }

# Create superuser non-interactively
echo "Creating superuser..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
try:
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created successfully')
except Exception as e:
    print(f'Failed to create superuser: {str(e)}')
EOF

# Run custom management commands (example)
echo "Running custom management commands..."
python manage.py collectstatic --noinput || { echo "Collectstatic failed"; exit 1; }

echo "Cleanup completed successfully!"