# Airline Ticket Reservation System

## Overview

A Django web application where users can search flights, select a ticket class and seat, and reserve airline tickets. Registered users will be able to log in and view their booking history.

## Technology Stack

* Python 3.12
* Django
* Django HTMX
* SQLite for local development
* uv for dependency and virtual-environment management
* Ruff for linting and formatting
* Pytest and pytest-django for testing
* Coverage for test-coverage reports
* Pre-commit for local quality checks
* Git and GitHub
* IntelliJ IDEA

## Setup

Clone the repository and enter the project directory:

```powershell
git clone <repository-url>
cd AirlineTicketReservation
```

Install the locked dependencies:

```powershell
uv sync
```

Apply Django migrations:

```powershell
uv run python manage.py migrate
```

Start the development server:

```powershell
uv run python manage.py runserver
```

Open the application at:

```text
http://127.0.0.1:8000/
```

## Quality Checks

Run linting:

```powershell
uv run ruff check .
```

Check formatting:

```powershell
uv run ruff format --check .
```

Run tests:

```powershell
uv run pytest
```

Generate a coverage report:

```powershell
uv run coverage run -m pytest
uv run coverage report
```

Run Django configuration checks:

```powershell
uv run python manage.py check
```

## Project Structure

```text
airline_reservation/     Django project configuration
reservations/            Main airline-booking application
templates/               Shared and application templates
static/                  CSS, JavaScript, and images
pyproject.toml           Dependencies and tool configuration
uv.lock                  Locked dependency versions
AGENTS.md                Instructions for coding agents
```

## Planned Features

* User registration and login
* Flight search by route, date, and ticket class
* Airline and flight selection
* Interactive seat selection
* Booking confirmation
* Booking-history page for logged-in users
* HTMX updates for available flights and seats
