import secrets
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

BOOKING_REFERENCE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def generate_booking_reference():
    random_part = "".join(secrets.choice(BOOKING_REFERENCE_ALPHABET) for _ in range(6))
    return f"AR{random_part}"


class City(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
    )

    airport_code = models.CharField(
        max_length=3,
        unique=True,
    )

    country = models.CharField(
        max_length=100,
        default="Unknown",
    )

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        default=0,
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        default=0,
    )

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "cities"

    def __str__(self):
        return f"{self.name} ({self.airport_code})"


class Airline(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
    )

    airline_code = models.CharField(
        max_length=2,
        unique=True,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.airline_code})"


class Flight(models.Model):
    airline = models.ForeignKey(
        Airline,
        on_delete=models.CASCADE,
        related_name="flights",
    )

    departure_city = models.ForeignKey(
        City,
        on_delete=models.CASCADE,
        related_name="departing_flights",
    )

    arrival_city = models.ForeignKey(
        City,
        on_delete=models.CASCADE,
        related_name="arriving_flights",
    )

    flight_number = models.CharField(
        max_length=10,
        unique=True,
    )

    departure_time = models.TimeField()
    arrival_time = models.TimeField()

    economy_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    business_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    currency = models.CharField(
        max_length=3,
        default="USD",
    )

    class Meta:
        ordering = [
            "departure_city",
            "arrival_city",
            "departure_time",
        ]

    def __str__(self):
        return (
            f"{self.flight_number}: "
            f"{self.departure_city.airport_code} → "
            f"{self.arrival_city.airport_code}"
        )

    def clean(self):
        if (
            self.departure_city_id
            and self.arrival_city_id
            and self.departure_city_id == self.arrival_city_id
        ):
            raise ValidationError("Departure city and arrival city must be different.")

    def price_for_class(self, cabin_class):
        if cabin_class == Seat.CabinClass.BUSINESS:
            return self.business_price

        return self.economy_price


class Seat(models.Model):
    class CabinClass(models.TextChoices):
        BUSINESS = "business", "Business"
        ECONOMY = "economy", "Economy"

    class SeatLetter(models.TextChoices):
        A = "A", "A"
        B = "B", "B"
        C = "C", "C"
        D = "D", "D"

    flight = models.ForeignKey(
        Flight,
        on_delete=models.CASCADE,
        related_name="seats",
    )

    row_number = models.PositiveSmallIntegerField()

    seat_letter = models.CharField(
        max_length=1,
        choices=SeatLetter.choices,
    )

    cabin_class = models.CharField(
        max_length=10,
        choices=CabinClass.choices,
    )

    class Meta:
        ordering = [
            "flight",
            "row_number",
            "seat_letter",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "flight",
                    "row_number",
                    "seat_letter",
                ],
                name="unique_seat_per_flight",
            )
        ]

    def __str__(self):
        return f"{self.flight.flight_number} - {self.seat_number}"

    @property
    def seat_number(self):
        return f"{self.row_number}{self.seat_letter}"


class Reservation(models.Model):
    booking_reference = models.CharField(
        max_length=8,
        unique=True,
        default=generate_booking_reference,
        editable=False,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="reservations",
        null=True,
        blank=True,
    )

    flight = models.ForeignKey(
        Flight,
        on_delete=models.CASCADE,
        related_name="reservations",
    )

    travel_date = models.DateField()

    cabin_class = models.CharField(
        max_length=10,
        choices=Seat.CabinClass.choices,
        default=Seat.CabinClass.ECONOMY,
    )

    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    currency = models.CharField(
        max_length=3,
        default="USD",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = [
            "-travel_date",
            "-created_at",
        ]

    def __str__(self):
        return (
            f"{self.booking_reference} - "
            f"{self.flight.flight_number} - "
            f"{self.travel_date}"
        )

    @property
    def passenger_count(self):
        return self.passenger_bookings.count()


class Booking(models.Model):
    """
    Represents one passenger ticket inside a reservation.

    reservation remains nullable for compatibility with development data
    created before group reservations were introduced. New application
    bookings always belong to a Reservation.
    """

    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        related_name="passenger_bookings",
        null=True,
        blank=True,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="bookings",
        null=True,
        blank=True,
    )

    flight = models.ForeignKey(
        Flight,
        on_delete=models.CASCADE,
        related_name="bookings",
    )

    seat = models.ForeignKey(
        Seat,
        on_delete=models.PROTECT,
        related_name="bookings",
    )

    travel_date = models.DateField()

    passenger_name = models.CharField(
        max_length=100,
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    currency = models.CharField(
        max_length=3,
        default="USD",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = [
            "-travel_date",
            "-created_at",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "flight",
                    "travel_date",
                    "seat",
                ],
                name="unique_seat_booking_per_flight_date",
            )
        ]

    def __str__(self):
        return (
            f"{self.passenger_name} - "
            f"{self.flight.flight_number} - "
            f"{self.travel_date} - "
            f"{self.seat.seat_number}"
        )

    def clean(self):
        errors = {}

        if self.seat_id and self.flight_id and self.seat.flight_id != self.flight_id:
            errors["seat"] = "The selected seat does not belong to this flight."

        if self.reservation_id:
            if self.flight_id != self.reservation.flight_id:
                errors["flight"] = (
                    "The passenger booking flight does not match the reservation."
                )

            if self.travel_date != self.reservation.travel_date:
                errors["travel_date"] = (
                    "The passenger booking date does not match the reservation."
                )

            if self.seat_id and self.seat.cabin_class != self.reservation.cabin_class:
                errors["seat"] = (
                    "The selected seat does not match the reservation cabin class."
                )

            if self.currency != self.reservation.currency:
                errors["currency"] = (
                    "The passenger booking currency does not match the reservation."
                )

        if errors:
            raise ValidationError(errors)
