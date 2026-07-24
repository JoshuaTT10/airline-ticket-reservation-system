# AeroReserve — Airline Ticket Reservation System

AeroReserve is a full-stack airline ticket reservation web application developed with Django for the **University of Aizu Web Engineering course**.

The application allows users to search demo flight schedules between major international airports, compare fares, choose seats from an interactive seat map, reserve tickets for up to five passengers under one reservation, create accounts, and review previous bookings.

> **Important:** Airport and airline names are based on real-world entities, but flight schedules, prices, routes, seat availability, and reservations are generated demonstration data. AeroReserve is not connected to any real airline reservation system.

---

## Features

### Flight Search

- Search flights between major international airports
- 50 airport destinations in the demonstration database
- Searchable airport selectors using airport code, city, or country
- Dynamic destination filtering
- Travel dates limited to the next 14 days
- Economy and Business cabin classes
- Passenger selection from 1 to 5 passengers
- Multiple recurring daily flights on supported routes
- Only flights with enough seats for the complete group are displayed
- Per-passenger and total reservation prices

### Interactive Seat Selection

- Visual aircraft-style seat map
- Live available and occupied seat states
- Economy and Business seat separation
- Select exactly the number of seats required for the reservation
- Individual seat assignment for every passenger
- Server-side validation of all selected seats
- Database protection against duplicate seat reservations

### Multi-Passenger Reservations

One reservation can contain up to five passenger tickets.

For example:

```text
Reservation ARABC123
│
├── Passenger 1 → Seat 4A
├── Passenger 2 → Seat 4B
└── Passenger 3 → Seat 5A
```

Each reservation contains:

- One booking reference
- One flight
- One travel date
- One cabin class
- Passenger count
- Individual passenger names
- Individual seats
- Individual passenger fares
- Combined total price

### Authentication

- Account registration
- Django password hashing
- Unique email validation
- Sign in using either:
    - Username
    - Email address
- Automatic login after registration
- Secure POST logout
- Registered-user booking history
- Logged-in passenger name pre-fill

### Guest Reservations

Users are not required to create an account before booking.

Guest reservations are protected using session-based reservation references so that another browser cannot simply access another guest's confirmation page.

### Booking History

Registered users can view their reservations under **My Bookings**.

Each reservation displays:

- Booking reference
- Route
- Airline
- Flight number
- Travel date
- Cabin class
- Passenger count
- Total price

Users can open each reservation to view the complete passenger and seat information.

### HTMX

AeroReserve uses HTMX to provide dynamic interactions without requiring full page reloads.

HTMX is currently used for:

1. **Flight search**
    - Search results are inserted dynamically into the page.

2. **Destination filtering**
    - Selecting a departure airport dynamically updates the destination airport options.

### Responsive UI

The interface includes responsive layouts for:

- Desktop
- Tablet
- Mobile

The application includes:

- Navigation bar
- Hero search interface
- Flight result cards
- Airport autocomplete controls
- Interactive seat map
- Passenger forms
- Booking confirmation ticket
- Booking history
- Login and registration pages
- User feedback messages
- Empty states

---

# Technology Stack

## Backend

- Python 3.12
- Django 6
- Django ORM
- Django Forms
- Django Authentication
- Django Sessions

## Frontend

- HTML5
- CSS3
- Vanilla JavaScript
- HTMX

## Database

### Development

- SQLite

### Production

- PostgreSQL

## Development Tools

- uv
- Git
- GitHub
- Ruff
- pytest
- pytest-django
- Coverage
- pre-commit
- OpenCode
- OpenSpec

## Production

- Gunicorn
- WhiteNoise
- PostgreSQL
- Render

## Continuous Integration

- GitHub Actions

---

# Architecture

AeroReserve follows Django's standard server-side architecture.

```text
┌───────────────────────────────┐
│            Browser            │
│                               │
│ HTML / CSS / JS / HTMX        │
└──────────────┬────────────────┘
               │
               │ HTTP GET / POST
               ▼
┌───────────────────────────────┐
│          Django URLs          │
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│          Django Views         │
│                               │
│ - Search logic                │
│ - Booking logic               │
│ - Authentication              │
│ - Session handling            │
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│         Django Forms          │
│                               │
│ - Input validation            │
│ - Passenger validation        │
│ - Seat validation             │
│ - Login / Registration        │
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│          Django ORM           │
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│           Database            │
│                               │
│ SQLite      → Development     │
│ PostgreSQL  → Production      │
└───────────────────────────────┘
```

---

# Data Model

The main application entities are:

```text
User
 │
 └── Reservation
       │
       ├── booking_reference
       ├── flight
       ├── travel_date
       ├── cabin_class
       ├── total_price
       ├── currency
       │
       ├── Booking
       │     ├── passenger_name
       │     ├── seat
       │     └── price
       │
       ├── Booking
       │     ├── passenger_name
       │     ├── seat
       │     └── price
       │
       └── ...

Airline
   │
   └── Flight
        │
        ├── Departure City
        ├── Arrival City
        ├── Prices
        └── Seats

City
 ├── Departing Flights
 └── Arriving Flights
```

---

# Models

## City

Represents an airport/city.

Important fields:

```text
name
airport_code
country
latitude
longitude
```

Example:

```text
Tokyo Haneda (HND)
London Heathrow (LHR)
Singapore Changi (SIN)
```

---

## Airline

Represents an airline.

Fields:

```text
name
airline_code
```

Example:

```text
All Nippon Airways (NH)
Japan Airlines (JL)
British Airways (BA)
Singapore Airlines (SQ)
```

---

## Flight

Represents a recurring flight schedule.

Fields include:

```text
airline
departure_city
arrival_city
flight_number
departure_time
arrival_time
economy_price
business_price
currency
```

The application validates that departure and arrival airports cannot be the same.

---

## Seat

Represents a physical seat belonging to a flight.

Fields:

```text
flight
row_number
seat_letter
cabin_class
```

The demonstration aircraft contains:

```text
Rows 1–3 → Business
Rows 4–5 → Economy
```

Each row contains:

```text
A B   C D
```

Therefore each flight contains:

```text
5 rows × 4 seats = 20 seats
```

A database constraint prevents duplicate seat definitions for the same flight.

---

## Reservation

Represents the overall group reservation.

Fields:

```text
booking_reference
user
flight
travel_date
cabin_class
total_price
currency
created_at
```

A reservation can contain between one and five passenger bookings.

Example:

```text
Booking reference: ARX7K2M4
Flight: NH123
Date: July 29, 2026
Cabin: Economy
Passengers: 3
Total: $1,500
```

---

## Booking

Represents one passenger ticket within a reservation.

Fields:

```text
reservation
user
flight
seat
travel_date
passenger_name
price
currency
created_at
```

A database-level unique constraint prevents this combination from appearing twice:

```text
flight + travel_date + seat
```

This means the same seat cannot be booked twice for the same recurring flight on the same date.

---

# Booking Workflow

The main user flow is:

```text
Home
  │
  ▼
Select departure airport
  │
  ▼
Destination options update
  │
  ▼
Choose:
- Destination
- Travel date
- Cabin class
- Passenger count
  │
  ▼
Search flights
  │
  ▼
Available flights displayed
  │
  ▼
Choose flight
  │
  ▼
Interactive seat map
  │
  ▼
Select seats
  │
  ▼
Enter passenger names
  │
  ▼
Confirm reservation
  │
  ▼
Reservation + passenger bookings
created atomically
  │
  ▼
Booking confirmation
```

---

# Validation and Booking Integrity

Important booking rules are enforced on the server rather than relying on JavaScript.

## Search Validation

The server checks:

- Departure airport is valid
- Destination airport is valid
- Departure and destination differ
- Travel date is not in the past
- Travel date is no more than 14 days ahead
- Cabin class is valid
- Passenger count is between 1 and 5

---

## Flight Availability

A flight is only displayed when:

```text
available seats >= passenger count
```

For example, if a user searches for four passengers but only three Economy seats remain, that flight does not appear in the results.

---

## Seat Validation

When a booking is submitted, Django verifies:

- Correct number of seats selected
- No duplicate seats in the request
- Seats belong to the chosen flight
- Seats match the chosen cabin class
- Seats are still available
- Seats have not been booked by another reservation

---

## Transaction Safety

Reservations and passenger bookings are created inside a database transaction.

```text
BEGIN TRANSACTION

Create Reservation

Create Passenger Booking 1
Create Passenger Booking 2
Create Passenger Booking 3

COMMIT
```

If any passenger seat fails validation:

```text
ROLLBACK
```

This prevents partially completed group reservations.

---

# Authentication and Authorization

AeroReserve uses Django's built-in authentication system.

## Registration

The registration form collects:

```text
Username
Full name
Email
Password
Password confirmation
```

Passwords are stored using Django's password hashing system.

Email addresses must be unique.

---

## Login

Users may sign in using either:

```text
Username
```

or:

```text
Email address
```

The login form resolves the email address to the associated Django username before authentication.

---

## Reservation Security

### Registered reservations

A logged-in user can only view reservations belonging to their own account.

### Guest reservations

Guest reservation confirmation access is stored in the browser session.

This prevents another browser from accessing a guest reservation simply by knowing its booking reference.

---

# URL Structure

| Method | URL | Description |
|---|---|---|
| GET | `/` | Home and flight search |
| GET | `/airports/destinations/` | HTMX destination filtering |
| GET | `/flights/search/` | Search available flights |
| GET | `/flights/<flight_id>/seats/` | Seat selection |
| POST | `/flights/<flight_id>/seats/` | Create reservation |
| GET | `/bookings/` | Logged-in booking history |
| GET | `/reservations/<booking_reference>/` | Booking confirmation |
| GET / POST | `/register/` | Create an account |
| GET / POST | `/login/` | Sign in |
| POST | `/logout/` | Sign out |
| GET | `/health/` | Deployment health check |
| GET | `/admin/` | Django administration |

---

# Session Usage

The application intentionally separates temporary session data from persistent database data.

## Stored in the Database

```text
Users
Cities
Airlines
Flights
Seats
Reservations
Passenger bookings
```

## Stored in the Session

```text
Most recent flight search
Guest-accessible reservation references
Authentication session information
```

---

# Demonstration Dataset

The project includes a Django management command:

```bash
uv run python manage.py seed_airline_data
```

The seed dataset includes:

```text
50 airports
34 airlines
Hundreds of recurring flight schedules
20 seats per flight
Economy and Business cabins
Generated fares
```

The route generator creates connections using:

- Nearby airports
- International hubs
- Popular routes
- Bidirectional route creation

Configured routes receive multiple recurring daily services.

---

# Example Airports

Some included airports are:

```text
HND — Tokyo Haneda
KIX — Osaka Kansai
CTS — Sapporo New Chitose
ICN — Seoul Incheon
PEK — Beijing Capital
PVG — Shanghai Pudong
HKG — Hong Kong International
SIN — Singapore Changi
BKK — Bangkok Suvarnabhumi
DEL — Delhi Indira Gandhi
BOM — Mumbai Chhatrapati Shivaji
DXB — Dubai International
DOH — Doha Hamad International
LHR — London Heathrow
CDG — Paris Charles de Gaulle
FRA — Frankfurt
AMS — Amsterdam Schiphol
MAD — Madrid Barajas
FCO — Rome Fiumicino
JFK — New York JFK
LAX — Los Angeles
SFO — San Francisco
SYD — Sydney
MEL — Melbourne
AKL — Auckland
```

The full dataset contains 50 airports.

---

# Example Airlines

The demonstration dataset includes airlines such as:

```text
All Nippon Airways
Japan Airlines
Korean Air
Air China
China Eastern Airlines
Cathay Pacific
Singapore Airlines
Thai Airways
Air India
Emirates
Qatar Airways
British Airways
Air France
Lufthansa
KLM
Iberia
Turkish Airlines
United Airlines
Air Canada
Qantas
Air New Zealand
```

---

# Local Development Setup

## 1. Clone the Repository

```bash
git clone https://github.com/JoshuaTT10/airline-ticket-reservation-system.git
```

Enter the project:

```bash
cd airline-ticket-reservation-system
```

---

## 2. Install Dependencies

The project uses `uv`.

```bash
uv sync
```

---

## 3. Apply Database Migrations

```bash
uv run python manage.py migrate
```

---

## 4. Load Demonstration Data

For a new database:

```bash
uv run python manage.py seed_airline_data
```

To completely rebuild demonstration airline data:

```bash
uv run python manage.py seed_airline_data --reset
```

> `--reset` deletes existing reservations, bookings, flights, seats, airlines, and airport demo data before regenerating them. User accounts are preserved.

---

## 5. Create an Administrator

```bash
uv run python manage.py createsuperuser
```

---

## 6. Start the Development Server

```bash
uv run python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

Django Admin:

```text
http://127.0.0.1:8000/admin/
```

---

# Code Quality

AeroReserve uses Ruff for linting and formatting.

## Format

```bash
uv run ruff format .
```

## Lint

```bash
uv run ruff check .
```

## Django System Check

```bash
uv run python manage.py check
```

---

# Automated Tests

The application includes automated tests covering:

- Models
- Model validation
- Database seat uniqueness
- Search validation
- Flight availability
- HTMX requests
- Destination filtering
- Seat selection
- Multi-passenger reservations
- Guest reservations
- Reservation authorization
- Booking history
- Registration
- Password handling
- Username login
- Email login
- Incorrect password handling
- Health endpoint

Run the tests:

```bash
uv run pytest
```

Current test result:

```text
28 passed
```

---

# Test Coverage

Run:

```bash
uv run coverage run -m pytest
```

Then:

```bash
uv run coverage report
```

Current overall application coverage:

```text
89%
```

Example coverage result:

```text
Name                     Cover
--------------------------------
reservations/admin.py      97%
reservations/forms.py      93%
reservations/models.py     84%
reservations/views.py      82%
--------------------------------
TOTAL                      89%
```

---

# Pre-Commit Checks

The project includes pre-commit hooks for:

- Ruff linting
- Ruff formatting
- Django system checks

Install them with:

```bash
uv run pre-commit install
```

Run manually:

```bash
uv run pre-commit run --all-files
```

---

# Continuous Integration

GitHub Actions automatically checks the project when code is pushed.

The CI workflow performs:

```text
Install dependencies
        ↓
Ruff lint
        ↓
Ruff format check
        ↓
Django system check
        ↓
pytest
        ↓
Coverage
```

Workflow configuration:

```text
.github/workflows/ci.yml
```

---

# Static Files

Django serves development static files normally.

Production static files are collected using:

```bash
uv run python manage.py collectstatic --noinput
```

WhiteNoise is configured for production static-file delivery.

Generated production static files are stored under:

```text
staticfiles/
```

and are not committed to Git.

---

# Production Architecture

The production architecture is:

```text
                    Internet
                       │
                       ▼
                Render Web Service
                       │
                       ▼
                    Gunicorn
                       │
                       ▼
                     Django
                    /      \
                   /        \
                  ▼          ▼
           WhiteNoise    PostgreSQL
           Static Files    Database
```

---

# Production Environment Variables

Production uses environment variables rather than committed secrets.

Important variables include:

```text
SECRET_KEY
DATABASE_URL
DJANGO_DEBUG
RENDER_EXTERNAL_HOSTNAME
```

Production uses:

```text
DJANGO_DEBUG=False
```

The local development database remains SQLite when `DATABASE_URL` is not configured.

---

# Render Deployment

The repository contains a Render Blueprint:

```text
render.yaml
```

It defines:

```text
AeroReserve Django Web Service
+
PostgreSQL Database
```

## Deployment Process

1. Push the project to GitHub.
2. Sign in to Render.
3. Create a new **Blueprint**.
4. Connect the GitHub repository.
5. Render reads `render.yaml`.
6. PostgreSQL is provisioned.
7. Dependencies are installed.
8. Static files are collected.
9. Django migrations are applied.
10. The Django application starts using Gunicorn.
11. The deployment health endpoint verifies the application.

---

# Health Check

AeroReserve provides:

```text
/health/
```

Successful response:

```json
{
    "status": "ok"
}
```

This endpoint can be used by the production hosting platform to verify that Django is running.

---

# Project Structure

```text
airline-ticket-reservation-system/
│
├── airline_reservation/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── reservations/
│   ├── management/
│   │   └── commands/
│   │       └── seed_airline_data.py
│   │
│   ├── migrations/
│   │
│   ├── static/
│   │   └── reservations/
│   │       ├── css/
│   │       │   └── style.css
│   │       └── js/
│   │           └── app.js
│   │
│   ├── templates/
│   │   └── reservations/
│   │       ├── partials/
│   │       │   ├── destination_select.html
│   │       │   └── flight_results.html
│   │       │
│   │       ├── base.html
│   │       ├── booking_confirmation.html
│   │       ├── booking_history.html
│   │       ├── home.html
│   │       ├── login.html
│   │       ├── register.html
│   │       ├── search_results.html
│   │       └── seat_selection.html
│   │
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── .gitignore
├── .pre-commit-config.yaml
├── AGENTS.md
├── manage.py
├── pyproject.toml
├── render.yaml
├── README.md
└── uv.lock
```

---

# Course Exercise Coverage

## Exercise 1 — Project Proposal

Defined:

- Project title
- Project purpose
- Main user actions
- Initial data model
- User interface concept

---

## Exercise 2 — Application Architecture

Defined:

- Main entities
- Main user workflow
- Browser → Django → Database architecture

---

## Exercise 3 — Development Environment

Configured:

- Git
- GitHub
- uv
- Python virtual environment
- Ruff
- pytest
- Coverage
- pre-commit
- `.gitignore`
- Project documentation

---

## Exercise 4 — AI Development Tools

Used:

- OpenCode
- OpenSpec
- `AGENTS.md`

Agent instructions define:

- Project architecture
- Booking rules
- Authentication rules
- Validation requirements
- Testing requirements
- Quality commands

---

## Exercise 5 — Django and Database

Implemented:

- Django project
- Django application
- Database models
- Relationships
- Model validation
- Model string representations
- Migrations
- Seed management command
- Django Admin

---

## Exercise 6 — Views and URLs

Implemented views for:

- Home
- Flight search
- Dynamic destinations
- Seat selection
- Reservation creation
- Confirmation
- Booking history
- Registration
- Login
- Logout
- Health check

---

## Exercise 7 — Sessions and Templates

Implemented:

- Django sessions
- Guest reservation authorization
- Previous search memory
- Reusable base template
- Template inheritance
- Reusable HTMX partial templates

---

## Exercise 8 — Forms and User Input

Implemented:

- GET flight search
- POST reservation creation
- Registration forms
- Login forms
- Passenger forms
- Seat validation
- Search validation
- Django CSRF protection

---

## Exercise 9 — HTML, CSS and Responsive Design

Implemented:

- Semantic HTML
- Form labels
- Responsive navigation
- Responsive search interface
- Responsive flight cards
- Interactive seat map
- Booking confirmation UI
- Booking history
- Authentication pages
- Mobile layouts
- Accessible seat button states

---

## Exercise 10 — HTMX

Implemented two dynamic interactions:

### Dynamic Flight Search

```text
Search form
    ↓
HTMX request
    ↓
Django
    ↓
flight_results.html
    ↓
Results inserted into current page
```

### Dynamic Destination Filtering

```text
Departure selected
    ↓
HTMX request
    ↓
Django route lookup
    ↓
destination_select.html
    ↓
Destination selector replaced
```

---

# Testing Status

Current verified development status:

```text
Ruff lint                 PASS
Ruff formatting           PASS
Django system check       PASS
pytest                    28 PASS
Coverage                  89%
Multi-passenger booking   PASS
Guest booking             PASS
Username login            PASS
Email login               PASS
Booking history           PASS
HTMX search               PASS
Destination filtering     PASS
Seat validation           PASS
```

---

# Future Improvements

AeroReserve currently focuses on the requirements of the Web Engineering course.

Possible future improvements include:

- Round-trip reservations
- Connecting flights
- Flight cancellation
- Reservation modification
- Email confirmations
- QR boarding passes
- Payment integration
- Real airline APIs
- Real-time fare information
- Real airport schedule information
- Aircraft-specific cabin layouts
- Saved passenger profiles
- Advanced airport search
- Pagination and filtering for booking history

These features are intentionally outside the current course-project scope.

---

