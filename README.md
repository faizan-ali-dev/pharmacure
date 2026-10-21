# Pharmacure

A simple Django-based online pharmacy demo project.

Quick start:

1. Create virtualenv and install dependencies:

   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt

2. Run migrations and create superuser:

   python manage.py migrate
   python manage.py createsuperuser

3. Run the dev server:

   python manage.py runserver

Notes:
- Media files are stored in the `media/` directory.
- Emergency delivery charge is set in `pharmacure_project/settings.py` as `EMERGENCY_DELIVERY_CHARGE`.
