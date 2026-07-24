from datetime import time, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import (
    FlightSearchForm,
    RegistrationForm,
)
from .models import (
    Airline,
    Booking,
    City,
    Flight,
    Reservation,
    Seat,
)


class AeroReserveTestCase(TestCase):
    def setUp(self):
        self.today = timezone.localdate()

        self.travel_date = self.today + timedelta(days=1)

        self.hnd = City.objects.create(
            name="Tokyo Haneda",
            airport_code="HND",
            country="Japan",
        )

        self.lhr = City.objects.create(
            name="London Heathrow",
            airport_code="LHR",
            country="United Kingdom",
        )

        self.icn = City.objects.create(
            name="Seoul Incheon",
            airport_code="ICN",
            country="South Korea",
        )

        self.airline = Airline.objects.create(
            name="Test Airways",
            airline_code="TA",
        )

        self.flight = Flight.objects.create(
            airline=self.airline,
            departure_city=self.hnd,
            arrival_city=self.lhr,
            flight_number="TA100",
            departure_time=time(9, 0),
            arrival_time=time(19, 0),
            economy_price=Decimal("500.00"),
            business_price=Decimal("1200.00"),
            currency="USD",
        )

        self.second_flight = Flight.objects.create(
            airline=self.airline,
            departure_city=self.hnd,
            arrival_city=self.icn,
            flight_number="TA200",
            departure_time=time(11, 0),
            arrival_time=time(14, 0),
            economy_price=Decimal("200.00"),
            business_price=Decimal("500.00"),
            currency="USD",
        )

        self.economy_seats = [
            Seat.objects.create(
                flight=self.flight,
                row_number=row,
                seat_letter=letter,
                cabin_class=(Seat.CabinClass.ECONOMY),
            )
            for row, letter in [
                (4, "A"),
                (4, "B"),
                (4, "C"),
                (4, "D"),
                (5, "A"),
                (5, "B"),
            ]
        ]

        self.business_seat = Seat.objects.create(
            flight=self.flight,
            row_number=1,
            seat_letter="A",
            cabin_class=(Seat.CabinClass.BUSINESS),
        )

        self.user = User.objects.create_user(
            username="josh",
            email="josh@example.com",
            password="StrongPass123!",
            first_name="Josh",
            last_name="Test",
        )

    def search_params(
        self,
        **overrides,
    ):
        data = {
            "departure_city": (self.hnd.id),
            "arrival_city": (self.lhr.id),
            "travel_date": (self.travel_date.isoformat()),
            "ticket_class": (Seat.CabinClass.ECONOMY),
            "passenger_count": 2,
        }

        data.update(overrides)

        return data

    def create_reservation(
        self,
        *,
        user=None,
        seat=None,
        cabin_class=(Seat.CabinClass.ECONOMY),
    ):
        seat = seat or self.economy_seats[0]

        price = self.flight.price_for_class(cabin_class)

        reservation = Reservation.objects.create(
            user=user,
            flight=self.flight,
            travel_date=(self.travel_date),
            cabin_class=(cabin_class),
            total_price=price,
            currency="USD",
        )

        booking = Booking.objects.create(
            reservation=reservation,
            user=user,
            flight=self.flight,
            seat=seat,
            travel_date=(self.travel_date),
            passenger_name=("Test Passenger"),
            price=price,
            currency="USD",
        )

        return (
            reservation,
            booking,
        )

    def test_city_string(self):
        assert str(self.hnd) == ("Tokyo Haneda (HND)")

    def test_flight_rejects_same_city(self):
        flight = Flight(
            airline=self.airline,
            departure_city=self.hnd,
            arrival_city=self.hnd,
            flight_number="TA999",
            departure_time=time(9, 0),
            arrival_time=time(10, 0),
        )

        with pytest.raises(ValidationError):
            flight.full_clean()

    def test_seat_number(self):
        assert self.economy_seats[0].seat_number == "4A"

    def test_reservation_passenger_count(self):
        reservation, _ = self.create_reservation()

        assert reservation.passenger_count == 1

    def test_duplicate_seat_same_date_blocked(
        self,
    ):
        self.create_reservation(seat=self.economy_seats[0])

        reservation = Reservation.objects.create(
            flight=self.flight,
            travel_date=(self.travel_date),
            cabin_class=(Seat.CabinClass.ECONOMY),
            total_price=Decimal("500.00"),
        )

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Booking.objects.create(
                    reservation=(reservation),
                    flight=self.flight,
                    seat=(self.economy_seats[0]),
                    travel_date=(self.travel_date),
                    passenger_name=("Other Passenger"),
                    price=Decimal("500.00"),
                )

    def test_same_seat_different_date_allowed(
        self,
    ):
        self.create_reservation(seat=self.economy_seats[0])

        next_date = self.travel_date + timedelta(days=1)

        reservation = Reservation.objects.create(
            flight=self.flight,
            travel_date=next_date,
            cabin_class=(Seat.CabinClass.ECONOMY),
            total_price=Decimal("500.00"),
        )

        Booking.objects.create(
            reservation=reservation,
            flight=self.flight,
            seat=self.economy_seats[0],
            travel_date=next_date,
            passenger_name=("Other Passenger"),
            price=Decimal("500.00"),
        )

        assert Booking.objects.count() == 2

    def test_search_same_airport_invalid(self):
        form = FlightSearchForm(data=self.search_params(arrival_city=self.hnd.id))

        assert not form.is_valid()

    def test_search_past_date_invalid(self):
        form = FlightSearchForm(
            data=self.search_params(
                travel_date=(self.today - timedelta(days=1)).isoformat()
            )
        )

        assert not form.is_valid()

    def test_search_over_fourteen_days_invalid(
        self,
    ):
        form = FlightSearchForm(
            data=self.search_params(
                travel_date=(self.today + timedelta(days=15)).isoformat()
            )
        )

        assert not form.is_valid()

    def test_regular_flight_search(self):
        response = self.client.get(
            reverse("reservations:flight_search"),
            self.search_params(),
        )

        assert response.status_code == 200

        assert "TA100" in response.content.decode()

    def test_htmx_flight_search(self):
        response = self.client.get(
            reverse("reservations:flight_search"),
            self.search_params(),
            HTTP_HX_REQUEST="true",
        )

        assert response.status_code == 200

        assert b"AVAILABLE FLIGHTS" in response.content

        assert b"<html" not in response.content.lower()

    def test_search_requires_enough_seats(
        self,
    ):
        for (
            index,
            seat,
        ) in enumerate(self.economy_seats[:5]):
            reservation = Reservation.objects.create(
                flight=self.flight,
                travel_date=(self.travel_date),
                cabin_class=(Seat.CabinClass.ECONOMY),
                total_price=Decimal("500.00"),
            )

            Booking.objects.create(
                reservation=reservation,
                flight=self.flight,
                seat=seat,
                travel_date=(self.travel_date),
                passenger_name=(f"Passenger {index}"),
                price=Decimal("500.00"),
            )

        response = self.client.get(
            reverse("reservations:flight_search"),
            self.search_params(passenger_count=2),
        )

        assert "TA100" not in response.content.decode()

    def test_destination_filter(self):
        response = self.client.get(
            reverse("reservations:destination_options"),
            {"departure_city": (self.hnd.id)},
        )

        content = response.content.decode()

        assert "London Heathrow" in content

        assert "Seoul Incheon" in content

        assert "Tokyo Haneda" not in content

    def test_invalid_destination_request_safe(
        self,
    ):
        response = self.client.get(
            reverse("reservations:destination_options"),
            {"departure_city": "abc"},
        )

        assert response.status_code == 200

    def test_seat_page_loads(self):
        response = self.client.get(
            reverse(
                "reservations:seat_selection",
                kwargs={"flight_id": (self.flight.id)},
            ),
            {
                "date": (self.travel_date.isoformat()),
                "ticket_class": (Seat.CabinClass.ECONOMY),
                "passengers": 2,
            },
        )

        assert response.status_code == 200

        assert response.context["passenger_count"] == 2
        assert b"SEAT SELECTION" in response.content

    def test_multi_passenger_booking(
        self,
    ):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "reservations:seat_selection",
                kwargs={"flight_id": (self.flight.id)},
            ),
            {
                "travel_date": (self.travel_date.isoformat()),
                "ticket_class": (Seat.CabinClass.ECONOMY),
                "passenger_count": 2,
                "seat_ids": (f"{self.economy_seats[0].id},{self.economy_seats[1].id}"),
                "passenger_1_name": ("Josh Test"),
                "passenger_2_name": ("Dev Test"),
            },
        )

        assert response.status_code == 302

        assert Reservation.objects.count() == 1

        reservation = Reservation.objects.get()

        assert reservation.passenger_count == 2

        assert reservation.total_price == Decimal("1000.00")

        assert reservation.cabin_class == Seat.CabinClass.ECONOMY

    def test_guest_booking_and_confirmation(
        self,
    ):
        response = self.client.post(
            reverse(
                "reservations:seat_selection",
                kwargs={"flight_id": (self.flight.id)},
            ),
            {
                "travel_date": (self.travel_date.isoformat()),
                "ticket_class": (Seat.CabinClass.ECONOMY),
                "passenger_count": 1,
                "seat_ids": str(self.economy_seats[0].id),
                "passenger_1_name": ("Guest Passenger"),
            },
        )

        assert response.status_code == 302

        confirmation = self.client.get(response.url)

        assert confirmation.status_code == 200

        assert b"Guest Passenger" in confirmation.content

    def test_guest_confirmation_protected(
        self,
    ):
        reservation, _ = self.create_reservation()

        response = self.client.get(
            reverse(
                "reservations:reservation_confirmation",
                kwargs={"booking_reference": (reservation.booking_reference)},
            )
        )

        assert response.status_code == 404

    def test_other_user_confirmation_protected(
        self,
    ):
        reservation, _ = self.create_reservation(user=self.user)

        other = User.objects.create_user(
            username="other",
            password=("OtherPass123!"),
        )

        self.client.force_login(other)

        response = self.client.get(
            reverse(
                "reservations:reservation_confirmation",
                kwargs={"booking_reference": (reservation.booking_reference)},
            )
        )

        assert response.status_code == 404

    def test_bookings_require_login(self):
        response = self.client.get(reverse("reservations:booking_history"))

        assert response.status_code == 302

        assert "/login/" in response.url

    def test_history_only_own_reservations(
        self,
    ):
        own_reservation, _ = self.create_reservation(user=self.user)

        other = User.objects.create_user(
            username="other2",
            password=("OtherPass123!"),
        )

        Reservation.objects.create(
            user=other,
            flight=self.flight,
            travel_date=(self.travel_date),
            cabin_class=(Seat.CabinClass.ECONOMY),
            total_price=Decimal("500.00"),
        )

        self.client.force_login(self.user)

        response = self.client.get(reverse("reservations:booking_history"))

        assert own_reservation.booking_reference in response.content.decode()

        assert response.context["reservations"].count() == 1

    def test_duplicate_email_rejected(
        self,
    ):
        form = RegistrationForm(
            data={
                "username": "newuser",
                "full_name": "New User",
                "email": ("JOSH@example.com"),
                "password1": ("AnotherStrongPass123!"),
                "password2": ("AnotherStrongPass123!"),
            }
        )

        assert not form.is_valid()

        assert "email" in form.errors

    def test_registration_password_usable(
        self,
    ):
        response = self.client.post(
            reverse("reservations:register"),
            {
                "username": "freshuser",
                "full_name": ("Fresh User"),
                "email": ("fresh@example.com"),
                "password1": ("VeryStrongPass123!"),
                "password2": ("VeryStrongPass123!"),
            },
        )

        assert response.status_code == 302

        user = User.objects.get(username="freshuser")

        assert user.has_usable_password()

        assert user.check_password("VeryStrongPass123!")

    def test_login_page_correct_template(
        self,
    ):
        response = self.client.get(reverse("reservations:login"))

        content = response.content.decode()

        assert "Sign in" in content

        assert "Your bookings" not in content

    def test_login_username(self):
        response = self.client.post(
            reverse("reservations:login"),
            {
                "username": "josh",
                "password": ("StrongPass123!"),
            },
        )

        assert response.status_code == 302

        assert "_auth_user_id" in self.client.session

    def test_login_email(self):
        response = self.client.post(
            reverse("reservations:login"),
            {
                "username": ("josh@example.com"),
                "password": ("StrongPass123!"),
            },
        )

        assert response.status_code == 302

        assert "_auth_user_id" in self.client.session

    def test_wrong_password_rejected(
        self,
    ):
        response = self.client.post(
            reverse("reservations:login"),
            {
                "username": "josh",
                "password": "wrong",
            },
        )

        assert response.status_code == 200

        assert "_auth_user_id" not in self.client.session

    def test_health_check(self):
        response = self.client.get(reverse("reservations:health_check"))

        assert response.status_code == 200

        assert response.json() == {"status": "ok"}
