from datetime import time, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from .forms import (
    AirportModelChoiceField,
    FlightSearchForm,
    MultiPassengerBookingForm,
    RegistrationForm,
    StyledAuthenticationForm,
)
from .models import Airline, City, Flight, Reservation, Seat

pytestmark = pytest.mark.django_db


@pytest.fixture
def core_data():
    departure = City.objects.create(
        name="Regression Tokyo",
        airport_code="RGT",
        country="Japan",
    )

    arrival = City.objects.create(
        name="Regression London",
        airport_code="RGL",
        country="United Kingdom",
    )

    airline = Airline.objects.create(
        name="Regression Airways",
        airline_code="RA",
    )

    flight = Flight.objects.create(
        airline=airline,
        departure_city=departure,
        arrival_city=arrival,
        flight_number="RA100",
        departure_time=time(9, 30),
        arrival_time=time(17, 45),
        economy_price=Decimal("500.00"),
        business_price=Decimal("1300.00"),
        currency="USD",
    )

    seat = Seat.objects.create(
        flight=flight,
        row_number=4,
        seat_letter="A",
        cabin_class=Seat.CabinClass.ECONOMY,
    )

    return {
        "departure": departure,
        "arrival": arrival,
        "airline": airline,
        "flight": flight,
        "seat": seat,
    }


def make_search_data(core_data, **overrides):
    data = {
        "departure_city": core_data["departure"].pk,
        "arrival_city": core_data["arrival"].pk,
        "travel_date": timezone.localdate().isoformat(),
        "ticket_class": Seat.CabinClass.ECONOMY,
        "passenger_count": 1,
    }

    data.update(overrides)

    return data


@pytest.mark.parametrize(
    "passenger_count",
    [1, 2, 3, 4, 5],
)
def test_search_accepts_supported_passenger_counts(
    core_data,
    passenger_count,
):
    form = FlightSearchForm(
        data=make_search_data(
            core_data,
            passenger_count=passenger_count,
        )
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["passenger_count"] == passenger_count


@pytest.mark.parametrize(
    "passenger_count",
    [0, 6, -1, "abc", ""],
)
def test_search_rejects_unsupported_passenger_counts(
    core_data,
    passenger_count,
):
    form = FlightSearchForm(
        data=make_search_data(
            core_data,
            passenger_count=passenger_count,
        )
    )

    assert not form.is_valid()
    assert "passenger_count" in form.errors


@pytest.mark.parametrize(
    ("day_offset", "expected_valid"),
    [
        (-2, False),
        (-1, False),
        (0, True),
        (1, True),
        (7, True),
        (14, True),
        (15, False),
        (30, False),
    ],
)
def test_search_travel_date_boundaries(
    core_data,
    day_offset,
    expected_valid,
):
    travel_date = timezone.localdate() + timedelta(days=day_offset)

    form = FlightSearchForm(
        data=make_search_data(
            core_data,
            travel_date=travel_date.isoformat(),
        )
    )

    assert form.is_valid() is expected_valid

    if expected_valid:
        assert form.cleaned_data["travel_date"] == travel_date
    else:
        assert "travel_date" in form.errors


@pytest.mark.parametrize(
    ("ticket_class", "expected_valid"),
    [
        (Seat.CabinClass.ECONOMY, True),
        (Seat.CabinClass.BUSINESS, True),
        ("first", False),
        ("ECONOMY", False),
        ("", False),
    ],
)
def test_search_cabin_class_validation(
    core_data,
    ticket_class,
    expected_valid,
):
    form = FlightSearchForm(
        data=make_search_data(
            core_data,
            ticket_class=ticket_class,
        )
    )

    assert form.is_valid() is expected_valid


@pytest.mark.parametrize(
    ("full_name", "expected_first", "expected_last"),
    [
        ("Joshua Toji", "Joshua", "Toji"),
        ("Madonna", "Madonna", ""),
        ("Mary Jane Watson", "Mary", "Jane Watson"),
        ("  Alex Smith  ", "Alex", "Smith"),
        ("Élodie Martin", "Élodie", "Martin"),
    ],
)
def test_registration_splits_full_name(
    full_name,
    expected_first,
    expected_last,
):
    form = RegistrationForm(
        data={
            "username": "newuser",
            "full_name": full_name,
            "email": "newuser@example.com",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        }
    )

    assert form.is_valid(), form.errors

    user = form.save()

    assert user.first_name == expected_first
    assert user.last_name == expected_last


@pytest.mark.parametrize(
    ("submitted_email", "stored_email"),
    [
        ("USER@EXAMPLE.COM", "user@example.com"),
        ("MixedCase@Example.Com", "mixedcase@example.com"),
        ("  spaces@example.com  ", "spaces@example.com"),
        ("plus+tag@EXAMPLE.COM", "plus+tag@example.com"),
    ],
)
def test_registration_normalizes_email(
    submitted_email,
    stored_email,
):
    form = RegistrationForm(
        data={
            "username": "emailuser",
            "full_name": "Email User",
            "email": submitted_email,
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        }
    )

    assert form.is_valid(), form.errors

    user = form.save()

    assert user.email == stored_email


@pytest.mark.parametrize(
    "submitted_email",
    [
        "existing@example.com",
        "EXISTING@EXAMPLE.COM",
        "  Existing@Example.com  ",
    ],
)
def test_registration_rejects_duplicate_email_case_insensitively(
    submitted_email,
):
    User.objects.create_user(
        username="existing",
        email="existing@example.com",
        password="StrongPass123!",
    )

    form = RegistrationForm(
        data={
            "username": "differentuser",
            "full_name": "Different User",
            "email": submitted_email,
            "password1": "AnotherStrongPass123!",
            "password2": "AnotherStrongPass123!",
        }
    )

    assert not form.is_valid()
    assert "email" in form.errors


@pytest.mark.parametrize(
    ("code", "name", "country", "expected_label"),
    [
        (
            "HND",
            "Tokyo Haneda",
            "Japan",
            "HND — Tokyo Haneda, Japan",
        ),
        (
            "LHR",
            "London Heathrow",
            "United Kingdom",
            "LHR — London Heathrow, United Kingdom",
        ),
        (
            "DEL",
            "Delhi Indira Gandhi",
            "India",
            "DEL — Delhi Indira Gandhi, India",
        ),
        (
            "JFK",
            "New York JFK",
            "United States",
            "JFK — New York JFK, United States",
        ),
        (
            "SIN",
            "Singapore Changi",
            "Singapore",
            "SIN — Singapore Changi, Singapore",
        ),
    ],
)
def test_airport_choice_labels(
    code,
    name,
    country,
    expected_label,
):
    city = City.objects.create(
        airport_code=code,
        name=name,
        country=country,
    )

    field = AirportModelChoiceField(queryset=City.objects.all())

    assert field.label_from_instance(city) == expected_label


@pytest.mark.parametrize(
    ("row_number", "seat_letter", "expected_number"),
    [
        (1, "A", "1A"),
        (2, "B", "2B"),
        (3, "C", "3C"),
        (4, "D", "4D"),
        (5, "A", "5A"),
        (10, "B", "10B"),
        (12, "C", "12C"),
        (20, "D", "20D"),
    ],
)
def test_seat_number_formatting(
    core_data,
    row_number,
    seat_letter,
    expected_number,
):
    seat = Seat.objects.create(
        flight=core_data["flight"],
        row_number=row_number,
        seat_letter=seat_letter,
        cabin_class=Seat.CabinClass.BUSINESS,
    )

    assert seat.seat_number == expected_number
    assert str(seat) == (f"{core_data['flight'].flight_number} - {expected_number}")


@pytest.mark.parametrize(
    ("ticket_class", "expected_price"),
    [
        (
            Seat.CabinClass.ECONOMY,
            Decimal("500.00"),
        ),
        (
            Seat.CabinClass.BUSINESS,
            Decimal("1300.00"),
        ),
    ],
)
def test_flight_price_for_cabin(
    core_data,
    ticket_class,
    expected_price,
):
    assert core_data["flight"].price_for_class(ticket_class) == expected_price


@pytest.mark.parametrize(
    ("day_offset", "status", "expected_can_cancel"),
    [
        (-1, Reservation.Status.CONFIRMED, False),
        (0, Reservation.Status.CONFIRMED, True),
        (1, Reservation.Status.CONFIRMED, True),
        (14, Reservation.Status.CONFIRMED, True),
        (1, Reservation.Status.CANCELLED, False),
        (-1, Reservation.Status.CANCELLED, False),
    ],
)
def test_reservation_cancellation_eligibility(
    core_data,
    day_offset,
    status,
    expected_can_cancel,
):
    reservation = Reservation.objects.create(
        flight=core_data["flight"],
        travel_date=(timezone.localdate() + timedelta(days=day_offset)),
        cabin_class=Seat.CabinClass.ECONOMY,
        total_price=Decimal("500.00"),
        currency="USD",
        status=status,
    )

    assert reservation.can_cancel is expected_can_cancel
    assert reservation.is_cancelled is (status == Reservation.Status.CANCELLED)


@pytest.mark.parametrize(
    "passenger_count",
    [1, 2, 3, 4, 5],
)
def test_booking_form_creates_correct_passenger_fields(
    core_data,
    passenger_count,
):
    form = MultiPassengerBookingForm(
        flight=core_data["flight"],
        travel_date=timezone.localdate() + timedelta(days=1),
        ticket_class=Seat.CabinClass.ECONOMY,
        passenger_count=passenger_count,
    )

    passenger_fields = [name for name in form.fields if name.startswith("passenger_")]

    assert len(passenger_fields) == passenger_count

    for number in range(1, passenger_count + 1):
        assert f"passenger_{number}_name" in form.fields


@pytest.mark.parametrize(
    ("submitted_email", "expected_email"),
    [
        ("GUEST@EXAMPLE.COM", "guest@example.com"),
        ("Mixed.Contact@Example.Com", "mixed.contact@example.com"),
        ("  booking@example.com  ", "booking@example.com"),
    ],
)
def test_booking_form_normalizes_contact_email(
    core_data,
    submitted_email,
    expected_email,
):
    form = MultiPassengerBookingForm(
        data={
            "seat_ids": str(core_data["seat"].pk),
            "contact_email": submitted_email,
            "passenger_1_name": "Guest Passenger",
        },
        flight=core_data["flight"],
        travel_date=timezone.localdate() + timedelta(days=1),
        ticket_class=Seat.CabinClass.ECONOMY,
        passenger_count=1,
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["contact_email"] == expected_email


@pytest.mark.parametrize(
    (
        "identifier",
        "password",
        "is_active",
        "expected_valid",
    ),
    [
        (
            "loginuser",
            "StrongPass123!",
            True,
            True,
        ),
        (
            "login@example.com",
            "StrongPass123!",
            True,
            True,
        ),
        (
            "LOGIN@EXAMPLE.COM",
            "StrongPass123!",
            True,
            True,
        ),
        (
            "loginuser",
            "WrongPassword!",
            True,
            False,
        ),
        (
            "login@example.com",
            "WrongPassword!",
            True,
            False,
        ),
        (
            "loginuser",
            "StrongPass123!",
            False,
            False,
        ),
    ],
)
def test_authentication_identifier_matrix(
    identifier,
    password,
    is_active,
    expected_valid,
):
    user = User.objects.create_user(
        username="loginuser",
        email="login@example.com",
        password="StrongPass123!",
        is_active=is_active,
    )

    form = StyledAuthenticationForm(
        request=None,
        data={
            "username": identifier,
            "password": password,
        },
    )

    assert form.is_valid() is expected_valid

    if expected_valid:
        assert form.get_user() == user
