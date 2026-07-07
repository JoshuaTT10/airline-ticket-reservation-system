from datetime import date, time, timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from .models import Airline, Booking, City, Flight, Seat


@pytest.fixture
def flight():
    tokyo = City.objects.create(name="Tokyo", airport_code="TYO")
    osaka = City.objects.create(name="Osaka", airport_code="OSA")
    airline = Airline.objects.create(name="Japan Sky", airline_code="JS")

    return Flight.objects.create(
        airline=airline,
        departure_city=tokyo,
        arrival_city=osaka,
        flight_number="JS101",
        departure_time=time(9, 0),
        arrival_time=time(10, 20),
    )


@pytest.fixture
def seat(flight):
    return Seat.objects.create(
        flight=flight,
        row_number=1,
        seat_letter=Seat.SeatLetter.A,
        cabin_class=Seat.CabinClass.BUSINESS,
    )


@pytest.mark.django_db
def test_city_string_representation():
    city = City.objects.create(name="Tokyo", airport_code="TYO")

    assert str(city) == "Tokyo (TYO)"


@pytest.mark.django_db
def test_flight_cannot_have_same_departure_and_arrival_city():
    city = City.objects.create(name="Tokyo", airport_code="TYO")
    airline = Airline.objects.create(name="Japan Sky", airline_code="JS")

    flight = Flight(
        airline=airline,
        departure_city=city,
        arrival_city=city,
        flight_number="JS999",
        departure_time=time(9, 0),
        arrival_time=time(10, 0),
    )

    with pytest.raises(ValidationError):
        flight.full_clean()


@pytest.mark.django_db
def test_seat_number(flight, seat):
    assert seat.seat_number == "1A"
    assert str(seat) == "JS101 - 1A"


@pytest.mark.django_db
def test_same_seat_cannot_be_booked_twice_on_same_date(flight, seat):
    travel_date = date.today() + timedelta(days=1)

    Booking.objects.create(
        flight=flight,
        seat=seat,
        travel_date=travel_date,
        passenger_name="Josh T",
    )

    with pytest.raises(IntegrityError):
        Booking.objects.create(
            flight=flight,
            seat=seat,
            travel_date=travel_date,
            passenger_name="Another Passenger",
        )


@pytest.mark.django_db
def test_same_seat_can_be_booked_on_different_dates(flight, seat):
    first_date = date.today() + timedelta(days=1)
    second_date = date.today() + timedelta(days=2)

    Booking.objects.create(
        flight=flight,
        seat=seat,
        travel_date=first_date,
        passenger_name="Josh T",
    )

    second_booking = Booking.objects.create(
        flight=flight,
        seat=seat,
        travel_date=second_date,
        passenger_name="Another Passenger",
    )

    assert second_booking.pk is not None
