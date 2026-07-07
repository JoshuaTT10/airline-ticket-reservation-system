# AGENTS.md

## Project

Airline Ticket Reservation System — a Django web application for searching flights, selecting seats, and making reservations.

## Technology Stack

* Python 3.12
* Django
* django-htmx
* SQLite for development
* uv
* Ruff
* pytest-django
* coverage
* IntelliJ IDEA

## Important Commands

```powershell
uv sync
uv run python manage.py runserver
uv run python manage.py makemigrations
uv run python manage.py migrate
uv run python manage.py check
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv run coverage run -m pytest
uv run coverage report
```

## Coding Rules

* Use Django’s built-in User model for login and registration.
* Keep booking-related code inside the `reservations` app.
* Use Django models and migrations for all database changes.
* Use Django forms for user input and validation.
* Use the Django ORM instead of raw SQL.
* Keep business logic out of templates.
* Use template inheritance with `base.html`.
* Use HTMX only for focused updates, such as refreshing flight options or available seats.
* Do not commit `.env`, `.venv`, `db.sqlite3`, or IDE files.

## Airline Booking Rules

* A booking links a passenger, flight, travel date, and seat.
* The same seat cannot be booked twice on the same flight and date.
* The first three rows are Business class.
* Remaining rows are Economy class.
* Flights run on recurring daily schedules.
* Reservations are only allowed for the next 14 days.

## Quality Checklist

Before finishing any feature:

1. Run `uv run ruff check .`
2. Run `uv run ruff format --check .`
3. Run `uv run python manage.py check`
4. Run `uv run pytest`
5. Run `uv run coverage run -m pytest`
6. Run `uv run coverage report`
7. Add or update tests for changed behavior.
