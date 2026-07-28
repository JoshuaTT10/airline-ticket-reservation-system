from datetime import time, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .emails import (
    send_reservation_cancellation_email,
    send_reservation_confirmation_email,
)
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
                "contact_email": "josh@example.com",
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
                "contact_email": "guest@example.com",
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


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class PasswordResetTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="resetuser",
            email="reset@example.com",
            password="OriginalPass123!",
            first_name="Reset",
            last_name="User",
        )

        self.reset_url = reverse(
            "reservations:password_reset",
        )

        self.done_url = reverse(
            "reservations:password_reset_done",
        )

        self.complete_url = reverse(
            "reservations:password_reset_complete",
        )

    def valid_reset_url(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))

        token = default_token_generator.make_token(self.user)

        return reverse(
            "reservations:password_reset_confirm",
            kwargs={
                "uidb64": uid,
                "token": token,
            },
        )

    def test_password_reset_page_loads(self):
        response = self.client.get(self.reset_url)

        assert response.status_code == 200
        assert b"Forgot your password?" in response.content

    def test_password_reset_uses_correct_template(self):
        response = self.client.get(self.reset_url)

        self.assertTemplateUsed(
            response,
            "reservations/password_reset_form.html",
        )

    def test_login_page_contains_forgot_password_link(self):
        response = self.client.get(reverse("reservations:login"))

        assert response.status_code == 200

        assert reverse("reservations:password_reset") in response.content.decode()

        assert b"Forgot password?" in response.content

    def test_registered_email_redirects_to_done_page(self):
        response = self.client.post(
            self.reset_url,
            {
                "email": self.user.email,
            },
        )

        assert response.status_code == 302
        assert response.url == self.done_url

    def test_registered_email_sends_one_email(self):
        self.client.post(
            self.reset_url,
            {
                "email": self.user.email,
            },
        )

        assert len(mail.outbox) == 1

    def test_password_reset_email_has_correct_recipient(self):
        self.client.post(
            self.reset_url,
            {
                "email": self.user.email,
            },
        )

        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ["reset@example.com"]

    def test_password_reset_email_has_correct_subject(self):
        self.client.post(
            self.reset_url,
            {
                "email": self.user.email,
            },
        )

        assert mail.outbox[0].subject == ("Reset your AeroReserve password")

    def test_password_reset_email_contains_reset_link(self):
        self.client.post(
            self.reset_url,
            {
                "email": self.user.email,
            },
        )

        message = mail.outbox[0].body

        assert "/reset/" in message
        assert "AeroReserve" in message

    def test_password_reset_email_is_case_insensitive(self):
        response = self.client.post(
            self.reset_url,
            {
                "email": "RESET@EXAMPLE.COM",
            },
        )

        assert response.status_code == 302
        assert response.url == self.done_url
        assert len(mail.outbox) == 1

    def test_unknown_email_uses_same_success_page(self):
        response = self.client.post(
            self.reset_url,
            {
                "email": "nobody@example.com",
            },
        )

        assert response.status_code == 302
        assert response.url == self.done_url

    def test_unknown_email_does_not_send_email(self):
        self.client.post(
            self.reset_url,
            {
                "email": "nobody@example.com",
            },
        )

        assert len(mail.outbox) == 0

    def test_inactive_user_does_not_receive_reset_email(self):
        self.user.is_active = False
        self.user.save()

        response = self.client.post(
            self.reset_url,
            {
                "email": self.user.email,
            },
        )

        assert response.status_code == 302
        assert response.url == self.done_url
        assert len(mail.outbox) == 0

    def test_reset_done_page_loads(self):
        response = self.client.get(self.done_url)

        assert response.status_code == 200

        assert b"Reset link requested" in response.content

    def test_valid_reset_token_redirects_to_secure_reset_url(self):
        response = self.client.get(self.valid_reset_url())

        assert response.status_code == 302

        assert "set-password" in response.url

    def test_invalid_reset_token_is_rejected(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))

        response = self.client.get(
            reverse(
                "reservations:password_reset_confirm",
                kwargs={
                    "uidb64": uid,
                    "token": "invalid-token",
                },
            )
        )

        assert response.status_code == 200

        assert b"This reset link can't be used" in response.content

    def test_invalid_user_id_is_rejected(self):
        response = self.client.get(
            reverse(
                "reservations:password_reset_confirm",
                kwargs={
                    "uidb64": "invalid-user",
                    "token": "invalid-token",
                },
            )
        )

        assert response.status_code == 200

        assert b"This reset link can't be used" in response.content

    def test_complete_password_reset_changes_password(self):
        first_response = self.client.get(self.valid_reset_url())

        assert first_response.status_code == 302

        response = self.client.post(
            first_response.url,
            {
                "new_password1": "NewStrongPass456!",
                "new_password2": "NewStrongPass456!",
            },
        )

        assert response.status_code == 302
        assert response.url == self.complete_url

        self.user.refresh_from_db()

        assert self.user.check_password("NewStrongPass456!")

        assert not self.user.check_password("OriginalPass123!")

    def test_password_reset_rejects_mismatched_passwords(self):
        first_response = self.client.get(self.valid_reset_url())

        response = self.client.post(
            first_response.url,
            {
                "new_password1": "NewStrongPass456!",
                "new_password2": "DifferentPass456!",
            },
        )

        assert response.status_code == 200

        assert "new_password2" in response.context["form"].errors

        self.user.refresh_from_db()

        assert self.user.check_password("OriginalPass123!")

    def test_password_reset_complete_page_loads(self):
        response = self.client.get(self.complete_url)

        assert response.status_code == 200

        assert b"You're all set" in response.content

    def test_used_reset_token_cannot_reset_password_again(self):
        reset_url = self.valid_reset_url()

        first_response = self.client.get(reset_url)

        self.client.post(
            first_response.url,
            {
                "new_password1": "NewStrongPass456!",
                "new_password2": "NewStrongPass456!",
            },
        )

        response = self.client.get(reset_url)

        assert response.status_code == 200

        assert b"This reset link can't be used" in response.content


class ReservationCancellationTests(TestCase):
    def setUp(self):
        self.today = timezone.localdate()
        self.travel_date = self.today + timedelta(days=1)

        self.departure = City.objects.create(
            name="Cancellation Tokyo",
            airport_code="CTK",
            country="Japan",
        )

        self.arrival = City.objects.create(
            name="Cancellation London",
            airport_code="CLN",
            country="United Kingdom",
        )

        self.airline = Airline.objects.create(
            name="Cancellation Airways",
            airline_code="CX",
        )

        self.flight = Flight.objects.create(
            airline=self.airline,
            departure_city=self.departure,
            arrival_city=self.arrival,
            flight_number="CX100",
            departure_time=time(9, 0),
            arrival_time=time(17, 0),
            economy_price=Decimal("500.00"),
            business_price=Decimal("1200.00"),
            currency="USD",
        )

        self.seat = Seat.objects.create(
            flight=self.flight,
            row_number=4,
            seat_letter="A",
            cabin_class=Seat.CabinClass.ECONOMY,
        )

        self.second_seat = Seat.objects.create(
            flight=self.flight,
            row_number=4,
            seat_letter="B",
            cabin_class=Seat.CabinClass.ECONOMY,
        )

        self.user = User.objects.create_user(
            username="canceluser",
            email="cancel@example.com",
            password="StrongPass123!",
        )

        self.other_user = User.objects.create_user(
            username="othercanceluser",
            email="othercancel@example.com",
            password="StrongPass123!",
        )

    def create_reservation(
        self,
        *,
        user=None,
        seat=None,
        travel_date=None,
    ):
        seat = seat or self.seat
        travel_date = travel_date or self.travel_date

        reservation = Reservation.objects.create(
            user=user,
            flight=self.flight,
            travel_date=travel_date,
            cabin_class=Seat.CabinClass.ECONOMY,
            total_price=Decimal("500.00"),
            currency="USD",
        )

        booking = Booking.objects.create(
            reservation=reservation,
            user=user,
            flight=self.flight,
            seat=seat,
            travel_date=travel_date,
            passenger_name="Cancellation Passenger",
            price=Decimal("500.00"),
            currency="USD",
        )

        return reservation, booking

    def cancel_url(self, reservation):
        return reverse(
            "reservations:cancel_reservation",
            kwargs={
                "booking_reference": reservation.booking_reference,
            },
        )

    def test_confirmed_reservation_is_not_cancelled(self):
        reservation, _ = self.create_reservation(
            user=self.user,
        )

        assert reservation.status == Reservation.Status.CONFIRMED
        assert reservation.is_cancelled is False

    def test_confirmed_future_reservation_can_cancel(self):
        reservation, _ = self.create_reservation(
            user=self.user,
        )

        assert reservation.can_cancel is True

    def test_cancelled_reservation_cannot_cancel_again(self):
        reservation, _ = self.create_reservation(
            user=self.user,
        )

        reservation.status = Reservation.Status.CANCELLED
        reservation.save()

        assert reservation.can_cancel is False

    def test_past_reservation_cannot_cancel(self):
        reservation, _ = self.create_reservation(
            user=self.user,
            travel_date=self.today - timedelta(days=1),
        )

        assert reservation.can_cancel is False

    def test_cancel_endpoint_rejects_get(self):
        reservation, _ = self.create_reservation(
            user=self.user,
        )

        self.client.force_login(self.user)

        response = self.client.get(self.cancel_url(reservation))

        assert response.status_code == 405

        reservation.refresh_from_db()

        assert reservation.status == Reservation.Status.CONFIRMED

    def test_owner_can_cancel_reservation(self):
        reservation, _ = self.create_reservation(
            user=self.user,
        )

        self.client.force_login(self.user)

        response = self.client.post(self.cancel_url(reservation))

        assert response.status_code == 302

        reservation.refresh_from_db()

        assert reservation.status == Reservation.Status.CANCELLED

    def test_cancellation_sets_cancelled_timestamp(self):
        reservation, _ = self.create_reservation(
            user=self.user,
        )

        self.client.force_login(self.user)

        self.client.post(self.cancel_url(reservation))

        reservation.refresh_from_db()

        assert reservation.cancelled_at is not None

    def test_cancellation_marks_booking_cancelled(self):
        reservation, booking = self.create_reservation(
            user=self.user,
        )

        self.client.force_login(self.user)

        self.client.post(self.cancel_url(reservation))

        booking.refresh_from_db()

        assert booking.is_cancelled is True

    def test_other_user_cannot_cancel_reservation(self):
        reservation, _ = self.create_reservation(
            user=self.user,
        )

        self.client.force_login(self.other_user)

        response = self.client.post(self.cancel_url(reservation))

        assert response.status_code == 404

        reservation.refresh_from_db()

        assert reservation.status == Reservation.Status.CONFIRMED

    def test_anonymous_user_cannot_cancel_registered_reservation(self):
        reservation, _ = self.create_reservation(
            user=self.user,
        )

        response = self.client.post(self.cancel_url(reservation))

        assert response.status_code == 404

        reservation.refresh_from_db()

        assert reservation.status == Reservation.Status.CONFIRMED

    def test_guest_can_cancel_from_original_session(self):
        reservation, _ = self.create_reservation()

        session = self.client.session
        session["guest_reservation_references"] = [reservation.booking_reference]
        session.save()

        response = self.client.post(self.cancel_url(reservation))

        assert response.status_code == 302

        reservation.refresh_from_db()

        assert reservation.status == Reservation.Status.CANCELLED

    def test_guest_cannot_cancel_without_session_reference(self):
        reservation, _ = self.create_reservation()

        response = self.client.post(self.cancel_url(reservation))

        assert response.status_code == 404

        reservation.refresh_from_db()

        assert reservation.status == Reservation.Status.CONFIRMED

    def test_guest_cannot_cancel_from_different_session(self):
        reservation, _ = self.create_reservation()

        session = self.client.session
        session["guest_reservation_references"] = ["ARWRONG1"]
        session.save()

        response = self.client.post(self.cancel_url(reservation))

        assert response.status_code == 404

    def test_already_cancelled_reservation_remains_cancelled(self):
        reservation, booking = self.create_reservation(
            user=self.user,
        )

        reservation.status = Reservation.Status.CANCELLED
        reservation.cancelled_at = timezone.now()
        reservation.save()

        booking.is_cancelled = True
        booking.save()

        self.client.force_login(self.user)

        response = self.client.post(self.cancel_url(reservation))

        assert response.status_code == 302

        reservation.refresh_from_db()

        assert reservation.status == Reservation.Status.CANCELLED

    def test_cancelled_seat_can_be_booked_again(self):
        reservation, booking = self.create_reservation(
            user=self.user,
        )

        self.client.force_login(self.user)

        self.client.post(self.cancel_url(reservation))

        booking.refresh_from_db()

        assert booking.is_cancelled is True

        second_reservation = Reservation.objects.create(
            user=self.other_user,
            flight=self.flight,
            travel_date=self.travel_date,
            cabin_class=Seat.CabinClass.ECONOMY,
            total_price=Decimal("500.00"),
            currency="USD",
        )

        new_booking = Booking.objects.create(
            reservation=second_reservation,
            user=self.other_user,
            flight=self.flight,
            seat=self.seat,
            travel_date=self.travel_date,
            passenger_name="Replacement Passenger",
            price=Decimal("500.00"),
            currency="USD",
        )

        assert new_booking.pk is not None

    def test_active_seat_still_cannot_be_double_booked(self):
        self.create_reservation(
            user=self.user,
        )

        second_reservation = Reservation.objects.create(
            user=self.other_user,
            flight=self.flight,
            travel_date=self.travel_date,
            cabin_class=Seat.CabinClass.ECONOMY,
            total_price=Decimal("500.00"),
            currency="USD",
        )

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Booking.objects.create(
                    reservation=second_reservation,
                    user=self.other_user,
                    flight=self.flight,
                    seat=self.seat,
                    travel_date=self.travel_date,
                    passenger_name="Duplicate Passenger",
                    price=Decimal("500.00"),
                    currency="USD",
                )

    def test_confirmation_page_shows_cancelled_status(self):
        reservation, booking = self.create_reservation(
            user=self.user,
        )

        reservation.status = Reservation.Status.CANCELLED
        reservation.cancelled_at = timezone.now()
        reservation.save()

        booking.is_cancelled = True
        booking.save()

        self.client.force_login(self.user)

        response = self.client.get(
            reverse(
                "reservations:reservation_confirmation",
                kwargs={
                    "booking_reference": reservation.booking_reference,
                },
            )
        )

        assert response.status_code == 200
        assert b"Cancelled" in response.content

    def test_confirmation_page_shows_cancel_button_for_active_booking(self):
        reservation, _ = self.create_reservation(
            user=self.user,
        )

        self.client.force_login(self.user)

        response = self.client.get(
            reverse(
                "reservations:reservation_confirmation",
                kwargs={
                    "booking_reference": reservation.booking_reference,
                },
            )
        )

        assert response.status_code == 200
        assert b"Cancel reservation" in response.content

    def test_confirmation_page_hides_cancel_button_after_cancellation(self):
        reservation, booking = self.create_reservation(
            user=self.user,
        )

        reservation.status = Reservation.Status.CANCELLED
        reservation.cancelled_at = timezone.now()
        reservation.save()

        booking.is_cancelled = True
        booking.save()

        self.client.force_login(self.user)

        response = self.client.get(
            reverse(
                "reservations:reservation_confirmation",
                kwargs={
                    "booking_reference": reservation.booking_reference,
                },
            )
        )

        assert response.status_code == 200
        assert b"Cancel reservation" not in response.content

    def test_booking_history_keeps_cancelled_reservation(self):
        reservation, booking = self.create_reservation(
            user=self.user,
        )

        reservation.status = Reservation.Status.CANCELLED
        reservation.cancelled_at = timezone.now()
        reservation.save()

        booking.is_cancelled = True
        booking.save()

        self.client.force_login(self.user)

        response = self.client.get(reverse("reservations:booking_history"))

        content = response.content.decode()

        assert response.status_code == 200
        assert reservation.booking_reference in content
        assert "Cancelled" in content

    def test_cancel_unknown_reference_returns_404(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "reservations:cancel_reservation",
                kwargs={
                    "booking_reference": "ARXXXXXX",
                },
            )
        )

        assert response.status_code == 404


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="AeroReserve <noreply@example.com>",
)
class ReservationEmailTests(TestCase):
    def setUp(self):
        self.travel_date = timezone.localdate() + timedelta(days=2)

        self.departure = City.objects.create(
            name="Email Tokyo",
            airport_code="ETK",
            country="Japan",
        )

        self.arrival = City.objects.create(
            name="Email London",
            airport_code="ELN",
            country="United Kingdom",
        )

        self.airline = Airline.objects.create(
            name="Email Airways",
            airline_code="EA",
        )

        self.flight = Flight.objects.create(
            airline=self.airline,
            departure_city=self.departure,
            arrival_city=self.arrival,
            flight_number="EA500",
            departure_time=time(10, 30),
            arrival_time=time(18, 45),
            economy_price=Decimal("450.00"),
            business_price=Decimal("1100.00"),
            currency="USD",
        )

        self.first_seat = Seat.objects.create(
            flight=self.flight,
            row_number=4,
            seat_letter="A",
            cabin_class=Seat.CabinClass.ECONOMY,
        )

        self.second_seat = Seat.objects.create(
            flight=self.flight,
            row_number=4,
            seat_letter="B",
            cabin_class=Seat.CabinClass.ECONOMY,
        )

        self.user = User.objects.create_user(
            username="emailuser",
            email="account@example.com",
            password="StrongPass123!",
            first_name="Email",
            last_name="User",
        )

        self.other_user = User.objects.create_user(
            username="otheremailuser",
            email="other@example.com",
            password="StrongPass123!",
        )

    def create_reservation(
        self,
        *,
        contact_email="traveller@example.com",
        user=None,
        cancelled=False,
        passenger_count=2,
    ):
        reservation = Reservation.objects.create(
            user=user,
            contact_email=contact_email,
            flight=self.flight,
            travel_date=self.travel_date,
            cabin_class=Seat.CabinClass.ECONOMY,
            total_price=(Decimal("450.00") * passenger_count),
            currency="USD",
            status=(
                Reservation.Status.CANCELLED
                if cancelled
                else Reservation.Status.CONFIRMED
            ),
            cancelled_at=(timezone.now() if cancelled else None),
        )

        seats = [
            self.first_seat,
            self.second_seat,
        ]

        passenger_names = [
            "Alex Traveller",
            "Jamie Traveller",
        ]

        for index in range(passenger_count):
            Booking.objects.create(
                reservation=reservation,
                user=user,
                flight=self.flight,
                seat=seats[index],
                travel_date=self.travel_date,
                passenger_name=passenger_names[index],
                price=Decimal("450.00"),
                currency="USD",
                is_cancelled=cancelled,
            )

        return reservation

    def booking_url(self):
        return reverse(
            "reservations:seat_selection",
            kwargs={
                "flight_id": self.flight.id,
            },
        )

    def cancel_url(self, reservation):
        return reverse(
            "reservations:cancel_reservation",
            kwargs={
                "booking_reference": reservation.booking_reference,
            },
        )

    def test_confirmation_email_service_returns_one(self):
        reservation = self.create_reservation()

        result = send_reservation_confirmation_email(reservation.pk)

        assert result == 1

    def test_confirmation_email_sends_one_message(self):
        reservation = self.create_reservation()

        send_reservation_confirmation_email(reservation.pk)

        assert len(mail.outbox) == 1

    def test_confirmation_email_uses_contact_email(self):
        reservation = self.create_reservation(
            contact_email="booking@example.com",
            user=self.user,
        )

        send_reservation_confirmation_email(reservation.pk)

        assert mail.outbox[0].to == ["booking@example.com"]

    def test_confirmation_email_does_not_default_to_user_email(self):
        reservation = self.create_reservation(
            contact_email="contact@example.com",
            user=self.user,
        )

        send_reservation_confirmation_email(reservation.pk)

        assert mail.outbox[0].to != [self.user.email]

    def test_confirmation_email_uses_default_sender(self):
        reservation = self.create_reservation()

        send_reservation_confirmation_email(reservation.pk)

        assert mail.outbox[0].from_email == ("AeroReserve <noreply@example.com>")

    def test_confirmation_subject_contains_reference(self):
        reservation = self.create_reservation()

        send_reservation_confirmation_email(reservation.pk)

        assert reservation.booking_reference in (mail.outbox[0].subject)

    def test_confirmation_subject_mentions_confirmation(self):
        reservation = self.create_reservation()

        send_reservation_confirmation_email(reservation.pk)

        assert "confirmed" in (mail.outbox[0].subject.lower())

    def test_confirmation_body_contains_booking_reference(self):
        reservation = self.create_reservation()

        send_reservation_confirmation_email(reservation.pk)

        assert reservation.booking_reference in (mail.outbox[0].body)

    def test_confirmation_body_contains_route(self):
        reservation = self.create_reservation()

        send_reservation_confirmation_email(reservation.pk)

        body = mail.outbox[0].body

        assert "ETK" in body
        assert "ELN" in body
        assert "Email Tokyo" in body
        assert "Email London" in body

    def test_confirmation_body_contains_airline_and_flight(self):
        reservation = self.create_reservation()

        send_reservation_confirmation_email(reservation.pk)

        body = mail.outbox[0].body

        assert "Email Airways" in body
        assert "EA500" in body

    def test_confirmation_body_contains_all_passengers(self):
        reservation = self.create_reservation()

        send_reservation_confirmation_email(reservation.pk)

        body = mail.outbox[0].body

        assert "Alex Traveller" in body
        assert "Jamie Traveller" in body

    def test_confirmation_body_contains_all_seats(self):
        reservation = self.create_reservation()

        send_reservation_confirmation_email(reservation.pk)

        body = mail.outbox[0].body

        assert "4A" in body
        assert "4B" in body

    def test_confirmation_body_contains_total(self):
        reservation = self.create_reservation()

        send_reservation_confirmation_email(reservation.pk)

        body = mail.outbox[0].body

        assert "USD" in body
        assert "900.00" in body

    def test_blank_contact_email_sends_nothing(self):
        reservation = self.create_reservation(
            contact_email="",
        )

        result = send_reservation_confirmation_email(reservation.pk)

        assert result == 0
        assert len(mail.outbox) == 0

    def test_cancellation_email_service_returns_one(self):
        reservation = self.create_reservation(
            cancelled=True,
        )

        result = send_reservation_cancellation_email(reservation.pk)

        assert result == 1

    def test_cancellation_email_sends_one_message(self):
        reservation = self.create_reservation(
            cancelled=True,
        )

        send_reservation_cancellation_email(reservation.pk)

        assert len(mail.outbox) == 1

    def test_cancellation_subject_contains_reference(self):
        reservation = self.create_reservation(
            cancelled=True,
        )

        send_reservation_cancellation_email(reservation.pk)

        assert reservation.booking_reference in (mail.outbox[0].subject)

    def test_cancellation_subject_mentions_cancelled(self):
        reservation = self.create_reservation(
            cancelled=True,
        )

        send_reservation_cancellation_email(reservation.pk)

        assert "cancelled" in (mail.outbox[0].subject.lower())

    def test_cancellation_body_contains_passengers_and_seats(self):
        reservation = self.create_reservation(
            cancelled=True,
        )

        send_reservation_cancellation_email(reservation.pk)

        body = mail.outbox[0].body

        assert "Alex Traveller" in body
        assert "Jamie Traveller" in body
        assert "4A" in body
        assert "4B" in body

    def test_cancellation_body_says_seats_were_released(self):
        reservation = self.create_reservation(
            cancelled=True,
        )

        send_reservation_cancellation_email(reservation.pk)

        assert "released" in (mail.outbox[0].body.lower())

    def test_booking_view_sends_confirmation_after_commit(self):
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            response = self.client.post(
                self.booking_url(),
                {
                    "travel_date": self.travel_date.isoformat(),
                    "ticket_class": Seat.CabinClass.ECONOMY,
                    "passenger_count": 1,
                    "seat_ids": str(self.first_seat.id),
                    "contact_email": "guest@example.com",
                    "passenger_1_name": "Guest Passenger",
                },
            )

        assert response.status_code == 302
        assert len(callbacks) == 1
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ["guest@example.com"]

    def test_invalid_booking_does_not_send_email(self):
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            response = self.client.post(
                self.booking_url(),
                {
                    "travel_date": self.travel_date.isoformat(),
                    "ticket_class": Seat.CabinClass.ECONOMY,
                    "passenger_count": 1,
                    "seat_ids": "",
                    "contact_email": "guest@example.com",
                    "passenger_1_name": "Guest Passenger",
                },
            )

        assert response.status_code == 200
        assert len(callbacks) == 0
        assert len(mail.outbox) == 0

    def test_cancellation_view_sends_email_after_commit(self):
        reservation = self.create_reservation(
            contact_email="cancel@example.com",
            user=self.user,
        )

        self.client.force_login(self.user)

        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            response = self.client.post(self.cancel_url(reservation))

        assert response.status_code == 302
        assert len(callbacks) == 1
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ["cancel@example.com"]

    def test_unauthorized_cancellation_sends_no_email(self):
        reservation = self.create_reservation(
            user=self.user,
        )

        self.client.force_login(self.other_user)

        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            response = self.client.post(self.cancel_url(reservation))

        assert response.status_code == 404
        assert len(callbacks) == 0
        assert len(mail.outbox) == 0
