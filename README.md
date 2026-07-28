# AeroReserve

AeroReserve is a full-stack airline reservation platform built with Django for the University of Aizu Web Engineering course.

Users can search generated flight schedules across 50 international airports, compare Economy and Business fares, reserve seats for up to five passengers, manage bookings, cancel reservations, recover forgotten passwords, and receive transactional booking notifications.

## Live Application

**Production URL:**  
https://aeroreserve-tk9e.onrender.com

**Health check:**  
https://aeroreserve-tk9e.onrender.com/health/

> Airport and airline names are based on real-world entities. Routes, schedules, fares, seat availability, and reservations are generated demonstration data and are not connected to live airline systems.

---

## Project Status

| Area | Status |
|---|---|
| Application functionality | Complete |
| Responsive interface | Complete |
| PostgreSQL deployment | Complete |
| Automated tests | 163 passing |
| Overall test coverage | 95% |
| Application tables | 6 |
| Total database tables | 16 |
| Application primary keys | 6 |
| Application foreign keys | 10 |
| Continuous integration | Configured |
| Production deployment | Live |

---

## Main Features

### Flight Search

Users can search available flights by selecting:

- Departure airport
- Destination airport
- Travel date
- Cabin class
- Passenger count

Search rules include:

- Travel dates from today through the next 14 days
- Economy and Business cabin classes
- Reservations for 1–5 passengers
- Different departure and destination airports
- Only flights with enough available seats for the complete passenger group

The airport controls support searching by:

- Airport code
- City name
- Country

Example searches:

```text
HND → LHR
Tokyo → London
Japan → United Kingdom
```

---

### Dynamic HTMX Interface

AeroReserve uses HTMX for asynchronous page updates without requiring a full page reload.

#### Destination filtering

When a departure airport is selected:

```text
Departure selected
        ↓
HTMX GET request
        ↓
Django filters valid destinations
        ↓
Partial template returned
        ↓
Destination field updated
```

#### Flight search

When the search form is submitted:

```text
Search form submitted
        ↓
HTMX request
        ↓
Django validates and searches
        ↓
Flight result cards returned
        ↓
Results inserted into the current page
```

This keeps the server-side Django architecture while providing a responsive user experience.

---

### Flight Results

Each result displays:

- Airline
- Flight number
- Departure and arrival airports
- Departure and arrival times
- Cabin class
- Available seats
- Price per passenger
- Total price for the selected group

Only flights with enough seats for all requested passengers are shown.

---

### Interactive Seat Selection

Users choose seats from an aircraft-style seat map.

The interface shows:

- Available seats
- Selected seats
- Unavailable seats
- Economy and Business seat areas
- Passenger-to-seat assignments
- Current selection progress
- Updated reservation total

The frontend prevents users from selecting the wrong number of seats, while Django repeats all validation on the server.

---

### Multi-Passenger Reservations

A single reservation can contain between one and five passengers.

```text
Reservation ARABC123
│
├── Booking 1
│   ├── Passenger: Alex Smith
│   └── Seat: 4A
│
├── Booking 2
│   ├── Passenger: Jamie Smith
│   └── Seat: 4B
│
└── Booking 3
    ├── Passenger: Taylor Smith
    └── Seat: 5A
```

A `Reservation` stores group-level information.

Each `Booking` stores:

- One passenger
- One seat
- One fare
- One flight date

This separates group-level reservation data from passenger-level ticket data.

---

### Guest Reservations

Users can complete a reservation without creating an account.

Guest users provide:

- Passenger names
- A contact email address
- Seat selections

Guest confirmation access is protected using the Django session. A guest reservation can only be opened or cancelled from the browser session that created it.

---

### User Accounts

Registered users can:

- Create an account
- Sign in with a username
- Sign in with an email address
- Reset a forgotten password
- View booking history
- Open reservation details
- Cancel eligible reservations
- Have their account name pre-filled during checkout

Django’s authentication system provides:

- Secure password hashing
- Session authentication
- CSRF protection
- Token-based password recovery
- User authorization

---

### Password Recovery

The application includes Django’s secure password-reset workflow.

```text
Forgot password
        ↓
Submit registered email
        ↓
One-time reset token generated
        ↓
Reset link created
        ↓
User chooses a new password
        ↓
Old password becomes invalid
```

Security behavior includes:

- One-time reset links
- Invalid-token rejection
- Used-token rejection
- No account-enumeration response differences
- Inactive users do not receive reset links

---

### Booking Confirmation

After a successful reservation, users receive a confirmation page containing:

- Booking reference
- Reservation status
- Airline
- Flight number
- Route
- Date
- Departure and arrival times
- Cabin class
- Passenger names
- Assigned seats
- Individual fares
- Total price

Booking references use the format:

```text
ARXXXXXX
```

---

### Reservation Cancellation

Eligible future reservations can be cancelled.

Cancellation rules include:

- Cancellation requires a POST request
- Registered reservations can only be cancelled by their owner
- Guest reservations can only be cancelled from the original session
- Cancelled reservations remain visible in booking history
- Cancelled bookings are marked inactive
- Cancelled seats become available for another reservation
- Already-cancelled reservations cannot be cancelled again
- Past reservations cannot be cancelled

The reservation is preserved rather than deleted, allowing the application to retain booking history.

---

### Booking History

Registered users can view all their reservations under **My Bookings**.

Each history card displays:

- Travel date
- Route
- Airline
- Flight number
- Booking reference
- Passenger count
- Cabin class
- Total price
- Confirmed or Cancelled status

Users can open each reservation for complete passenger and seat details.

---

### Transactional Email Workflows

The project includes email workflows for:

- Password reset
- Reservation confirmation
- Reservation cancellation

Email notifications include:

- Booking reference
- Route
- Flight details
- Passenger names
- Seat assignments
- Fare information
- Cancellation information

Email callbacks are registered using `transaction.on_commit()`, ensuring that an email is only triggered after the database transaction succeeds.

Local development defaults to Django’s console email backend.

```text
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

The production email backend is environment-configurable. The current demonstration deployment uses the console backend so email output is written to service logs without risking interruption to reservation transactions.

---

## Technology Stack

### Backend

- Python 3.12
- Django 6
- Django ORM
- Django Forms
- Django Authentication
- Django Sessions

### Frontend

- HTML5
- CSS3
- Vanilla JavaScript
- HTMX

### Databases

- SQLite for local development
- PostgreSQL for production

### Deployment

- Render
- Gunicorn
- WhiteNoise
- PostgreSQL

### Development and Quality Tools

- uv
- Git
- GitHub
- Ruff
- pytest
- pytest-django
- Coverage
- pre-commit
- GitHub Actions
- OpenCode
- OpenSpec

---

## Architecture

AeroReserve follows Django’s server-rendered architecture.

```text
┌──────────────────────────────────┐
│             Browser              │
│                                  │
│ HTML · CSS · JavaScript · HTMX   │
└────────────────┬─────────────────┘
                 │
                 │ HTTP GET / POST
                 ▼
┌──────────────────────────────────┐
│            URL Router            │
│                                  │
│ reservations/urls.py             │
└────────────────┬─────────────────┘
                 │
                 ▼
┌──────────────────────────────────┐
│              Views               │
│                                  │
│ Search logic                     │
│ Booking workflow                 │
│ Cancellation workflow            │
│ Authentication                   │
│ Session authorization            │
└────────────────┬─────────────────┘
                 │
                 ▼
┌──────────────────────────────────┐
│              Forms               │
│                                  │
│ Input validation                 │
│ Passenger validation             │
│ Seat validation                  │
│ Authentication forms             │
│ Password-reset forms             │
└────────────────┬─────────────────┘
                 │
                 ▼
┌──────────────────────────────────┐
│            Django ORM            │
└────────────────┬─────────────────┘
                 │
                 ▼
┌──────────────────────────────────┐
│             Database             │
│                                  │
│ SQLite      Development          │
│ PostgreSQL  Production           │
└──────────────────────────────────┘
```

---

## Database Overview

The database contains 16 tables in total.

### AeroReserve application tables

```text
6 application tables
```

| Model | Purpose |
|---|---|
| `City` | Stores airport and location information |
| `Airline` | Stores airline information |
| `Flight` | Stores recurring flight schedules, routes, and prices |
| `Seat` | Stores aircraft seats for each flight |
| `Reservation` | Stores group-level reservation information |
| `Booking` | Stores one passenger and seat assignment |

### Django framework tables

```text
10 Django-managed tables
```

These support:

- Authentication
- Users
- Groups
- Permissions
- Sessions
- Admin history
- Content types
- Migrations

---

## Primary Keys

Each application model has an automatically generated Django `id` primary key.

```text
City.id
Airline.id
Flight.id
Seat.id
Reservation.id
Booking.id
```

Total application primary keys:

```text
6
```

`Reservation.booking_reference` is unique but is not the primary key.

---

## Foreign Keys

The six application tables contain ten foreign-key relationships.

| Model | Foreign keys | Count |
|---|---|---:|
| `City` | None | 0 |
| `Airline` | None | 0 |
| `Flight` | `airline`, `departure_city`, `arrival_city` | 3 |
| `Seat` | `flight` | 1 |
| `Reservation` | `user`, `flight` | 2 |
| `Booking` | `reservation`, `user`, `flight`, `seat` | 4 |
| **Total** |  | **10** |

---

## Entity Relationships

```text
Airline
   │
   └── Flight
          ├── departure_city → City
          ├── arrival_city   → City
          └── Seat

User
   │
   └── Reservation
          ├── Flight
          └── Booking
                 ├── User
                 ├── Flight
                 └── Seat
```

---

## Model Details

### City

Stores airport and geographic information.

```text
id
name
airport_code
country
latitude
longitude
```

Examples:

```text
HND — Tokyo Haneda
LHR — London Heathrow
SIN — Singapore Changi
DEL — Delhi Indira Gandhi
```

---

### Airline

Stores airline information.

```text
id
name
airline_code
```

Examples:

```text
NH — All Nippon Airways
JL — Japan Airlines
BA — British Airways
SQ — Singapore Airlines
```

---

### Flight

Stores recurring flight schedule information.

```text
id
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

Validation prevents the departure and arrival airport from being the same.

---

### Seat

Stores a physical seat belonging to a flight.

```text
id
flight
row_number
seat_letter
cabin_class
```

Demo aircraft layout:

```text
Rows 1–3  Business
Rows 4–5  Economy

A B   C D
```

Each generated flight contains 20 seats.

---

### Reservation

Stores group-level reservation information.

```text
id
booking_reference
user
contact_email
flight
travel_date
cabin_class
total_price
currency
status
cancelled_at
created_at
```

Possible status values:

```text
confirmed
cancelled
```

---

### Booking

Stores one passenger ticket inside a reservation.

```text
id
reservation
user
flight
seat
travel_date
passenger_name
price
currency
is_cancelled
created_at
```

---

## Database Constraints

### Unique booking reference

Every reservation has a unique public booking reference.

```text
ARABC123
```

### Unique seat definition

A seat cannot be defined twice for the same flight, row, and seat letter.

### Active seat booking constraint

The combination below must be unique for active bookings:

```text
flight + travel_date + seat
```

This prevents two active reservations from booking the same seat on the same flight date.

The uniqueness rule is conditional:

```text
is_cancelled = False
```

Therefore, after a booking is cancelled, the same seat can be reserved again while the original cancelled record remains stored.

---

## Booking Transaction

Reservations are created atomically.

```text
BEGIN TRANSACTION

Create Reservation

Create Booking for Passenger 1
Create Booking for Passenger 2
Create Booking for Passenger 3

Register confirmation email callback

COMMIT
```

If any passenger booking fails:

```text
ROLLBACK
```

This prevents incomplete group reservations.

Example:

```text
Passenger 1 booking succeeds
Passenger 2 booking succeeds
Passenger 3 seat is unavailable
```

Without a transaction, the first two bookings could remain.

With `transaction.atomic()`, the entire operation is rolled back.

---

## Server-Side Validation

The application never relies only on browser-side validation.

### Search validation

Django verifies:

- Valid departure airport
- Valid destination airport
- Different departure and destination
- Date is not in the past
- Date is no more than 14 days ahead
- Valid cabin class
- Passenger count between 1 and 5

### Booking validation

Django verifies:

- Contact email is valid
- Exact number of seats selected
- No duplicate seats selected
- Seats belong to the selected flight
- Seats match the selected cabin
- Seats remain available
- Passenger names are provided

### Cancellation validation

Django verifies:

- Request method is POST
- Reservation exists
- User or guest session is authorized
- Reservation is confirmed
- Reservation date is not in the past

Client-side JavaScript improves usability, but the server protects the database.

---

## Session Usage

AeroReserve separates temporary browser-specific data from persistent data.

### Stored in the database

- Users
- Airports
- Airlines
- Flights
- Seats
- Reservations
- Passenger bookings
- Cancellation status

### Stored in the session

- Previous flight-search values
- Guest-accessible reservation references
- Authentication session information

---

## URL Structure

| Method | URL | Description |
|---|---|---|
| GET | `/` | Homepage and flight search |
| GET | `/airports/destinations/` | HTMX destination filtering |
| GET | `/flights/search/` | Flight search results |
| GET | `/flights/<flight_id>/seats/` | Seat-selection page |
| POST | `/flights/<flight_id>/seats/` | Create reservation |
| GET | `/reservations/<reference>/` | Reservation confirmation |
| POST | `/reservations/<reference>/cancel/` | Cancel reservation |
| GET | `/bookings/` | Logged-in booking history |
| GET / POST | `/register/` | Account registration |
| GET / POST | `/login/` | Account login |
| POST | `/logout/` | Account logout |
| GET / POST | `/password-reset/` | Request password reset |
| GET | `/password-reset/done/` | Reset-email requested page |
| GET / POST | `/reset/<uid>/<token>/` | Set a new password |
| GET | `/reset/done/` | Password-reset completion |
| GET | `/health/` | Deployment health check |
| GET | `/admin/` | Django administration |

---

## Demonstration Dataset

The application includes a Django management command:

```bash
uv run python manage.py seed_airline_data
```

The generated dataset includes:

- 50 airports
- 34 airlines
- Generated international routes
- Multiple recurring flight schedules
- Economy and Business prices
- 20 seats per flight

The route generator uses:

- Nearby airport connections
- Major international hubs
- Popular global routes
- Bidirectional route generation
- Deterministic generated prices

To rebuild all airline demo data:

```bash
uv run python manage.py seed_airline_data --reset
```

> The `--reset` option removes existing demo reservations, bookings, flights, seats, airlines, and airports. User accounts are preserved.

---

## Example Airports

```text
HND — Tokyo Haneda
KIX — Osaka Kansai
CTS — Sapporo New Chitose
FUK — Fukuoka
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
JFK — New York JFK
LAX — Los Angeles
SFO — San Francisco
SYD — Sydney
MEL — Melbourne
AKL — Auckland
```

The full generated dataset contains 50 airports.

---

## Example Airlines

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

## Local Development Setup

### 1. Clone the repository

```bash
git clone https://github.com/JoshuaTT10/airline-ticket-reservation-system.git
cd airline-ticket-reservation-system
```

### 2. Install dependencies

The project uses `uv`.

```bash
uv sync
```

### 3. Apply migrations

```bash
uv run python manage.py migrate
```

### 4. Load demonstration data

```bash
uv run python manage.py seed_airline_data
```

### 5. Create an administrator

```bash
uv run python manage.py createsuperuser
```

### 6. Start the server

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

## Environment Variables

The application reads sensitive and environment-specific configuration from environment variables.

Common production variables:

```text
SECRET_KEY
DJANGO_DEBUG
DATABASE_URL
RENDER_EXTERNAL_HOSTNAME
EMAIL_BACKEND
DEFAULT_FROM_EMAIL
```

Optional email-provider credentials depend on the selected backend.

Do not commit secrets or API keys to GitHub.

---

## Automated Tests

AeroReserve includes 163 automated tests.

The suite covers:

### Models and constraints

- Model string representations
- Cabin pricing
- Seat formatting
- Primary relationships
- Unique active-seat bookings
- Cancelled seat reuse
- Reservation cancellation eligibility

### Search forms

- Valid passenger counts
- Invalid passenger counts
- Date boundaries
- Cabin validation
- Same-airport rejection
- Airport labels

### Booking forms

- Passenger-field creation
- Contact-email normalization
- Exact seat count
- Duplicate-seat rejection
- Invalid seat IDs
- Cabin mismatch
- Occupied seats

### Authentication

- Registration
- Unique emails
- Full-name handling
- Username login
- Email login
- Case-insensitive email login
- Incorrect passwords
- Inactive accounts

### Password recovery

- Reset request page
- Registered and unknown email behavior
- Email generation
- Reset tokens
- Invalid tokens
- Used-token rejection
- Password updates
- Mismatched passwords

### Reservation workflow

- Guest reservations
- Registered reservations
- Multi-passenger bookings
- Confirmation access
- Session protection
- Booking-history access

### Cancellation

- Owner cancellation
- Guest cancellation
- Unauthorized cancellation
- POST-only enforcement
- Cancellation timestamps
- Cancelled booking state
- Seat release
- Booking-history status

### Email workflows

- Confirmation-email generation
- Cancellation-email generation
- Recipient selection
- Subject lines
- Passenger and seat information
- Transaction callbacks
- Invalid-booking email prevention

### HTMX and deployment

- HTMX partial responses
- Destination filtering
- Flight search
- Health endpoint

Run the full suite:

```bash
uv run pytest
```

Current result:

```text
163 passed
```

---

## Test Coverage

Run:

```bash
uv run coverage run -m pytest
uv run coverage report
```

Current application coverage:

```text
95%
```

Current coverage summary:

```text
Name                     Cover
--------------------------------
reservations/admin.py      97%
reservations/forms.py      94%
reservations/models.py     88%
reservations/views.py      84%
--------------------------------
TOTAL                      95%
```

---

## Code Quality

### Ruff formatting

```bash
uv run ruff format .
```

### Ruff linting

```bash
uv run ruff check .
```

### Django system check

```bash
uv run python manage.py check
```

### Pre-commit hooks

Install:

```bash
uv run pre-commit install
```

Run all hooks:

```bash
uv run pre-commit run --all-files
```

Configured hooks verify:

- Ruff linting
- Ruff formatting
- Django system checks

---

## Continuous Integration

GitHub Actions runs quality checks on pushes and pull requests.

The workflow performs:

```text
Install Python and dependencies
        ↓
Ruff lint
        ↓
Ruff format check
        ↓
Django system check
        ↓
pytest
        ↓
Coverage report
```

Workflow file:

```text
.github/workflows/ci.yml
```

---

## AI-Assisted Development Setup

The project uses an AI-assisted engineering workflow with explicit project configuration.

Files include:

```text
AGENTS.md
openspec/
.opencode/
```

The workflow defines:

- Architecture rules
- Model responsibilities
- Booking constraints
- Authentication requirements
- Testing expectations
- Quality commands
- Documentation standards

AI-generated or AI-assisted changes are validated using:

- Automated tests
- Ruff
- Django checks
- Pre-commit hooks
- GitHub Actions
- Manual browser testing

---

## Production Deployment

AeroReserve is deployed on Render.

Production architecture:

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
   ├── WhiteNoise static files
   └── PostgreSQL database
```

The repository contains:

```text
render.yaml
```

The Render deployment performs:

1. Install `uv`
2. Install production dependencies
3. Collect static files
4. Apply Django migrations
5. Seed demonstration airline data when needed
6. Start Gunicorn
7. Verify `/health/`

---

## Static Files

Production static files are collected with:

```bash
uv run python manage.py collectstatic --noinput
```

WhiteNoise serves the collected static files.

Generated files are stored in:

```text
staticfiles/
```

This directory is excluded from Git.

---

## Project Structure

```text
airline-ticket-reservation-system/
│
├── airline_reservation/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
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
│   │       ├── emails/
│   │       │   ├── reservation_confirmation_email.txt
│   │       │   └── reservation_cancellation_email.txt
│   │       │
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
│   │       ├── seat_selection.html
│   │       ├── password_reset_form.html
│   │       ├── password_reset_done.html
│   │       ├── password_reset_confirm.html
│   │       ├── password_reset_complete.html
│   │       ├── password_reset_email.txt
│   │       └── password_reset_subject.txt
│   │
│   ├── admin.py
│   ├── emails.py
│   ├── forms.py
│   ├── models.py
│   ├── tests.py
│   ├── test_validation_matrix.py
│   ├── urls.py
│   └── views.py
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── openspec/
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

## Web Engineering Course Coverage

### Project and architecture

- Defined project purpose
- Defined user workflows
- Designed application architecture
- Designed relational database schema

### Development environment

- Git and GitHub
- uv environment management
- Ruff formatting and linting
- pytest and Coverage
- pre-commit
- GitHub Actions

### Django and database

- Six application models
- Foreign-key relationships
- Database constraints
- Migrations
- Seed management command
- Django Admin

### Business logic and views

- Flight search
- Availability calculation
- Multi-passenger booking
- Transaction-safe reservation creation
- Cancellation
- Authentication
- Password recovery
- Booking history
- Email notifications

### Templates

- Reusable base layout
- Template inheritance
- Partial templates
- Separate HTML, CSS, JavaScript, and Python responsibilities

### User input

- GET search forms
- POST booking forms
- Registration
- Login
- Password reset
- Passenger data
- Email collection
- Seat selection
- Cancellation confirmation

### Rich interface

- Responsive layout
- Searchable airport fields
- HTMX destination filtering
- HTMX flight results
- Interactive seat map
- Mobile-compatible interface

### Tests, specifications, and documentation

- 163 automated tests
- 95% coverage
- README documentation
- OpenSpec files
- AGENTS.md
- Continuous integration

### Deployment

- Render Blueprint
- PostgreSQL
- Gunicorn
- WhiteNoise
- Health endpoint
- Environment-based configuration

---

