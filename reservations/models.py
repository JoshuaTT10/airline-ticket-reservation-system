from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class City(models.Model):
    name = models.CharField(max_length=100, unique=True)
    airport_code = models.CharField(max_length=3, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "cities"

    def __str__(self):
        return f"{self.name} ({self.airport_code})"


class Airline(models.Model):
    name = models.CharField(max_length=100, unique=True)
    airline_code = models.CharField(max_length=2, unique=True)

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
    flight_number = models.CharField(max_length=10, unique=True)
    departure_time = models.TimeField()
    arrival_time = models.TimeField()

    class Meta:
        ordering = ["departure_city", "arrival_city", "departure_time"]

    def __str__(self):
        return (
            f"{self.flight_number}: {self.departure_city.airport_code} "
            f"to {self.arrival_city.airport_code}"
        )

    def clean(self):
        if self.departure_city == self.arrival_city:
            raise ValidationError("Departure city and arrival city must be different.")


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
    seat_letter = models.CharField(max_length=1, choices=SeatLetter.choices)
    cabin_class = models.CharField(
        max_length=10,
        choices=CabinClass.choices,
    )

    class Meta:
        ordering = ["flight", "row_number", "seat_letter"]
        constraints = [
            models.UniqueConstraint(
                fields=["flight", "row_number", "seat_letter"],
                name="unique_seat_per_flight",
            )
        ]

    def __str__(self):
        return f"{self.flight.flight_number} - {self.seat_number}"

    @property
    def seat_number(self):
        return f"{self.row_number}{self.seat_letter}"


class Booking(models.Model):
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
    passenger_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-travel_date", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["flight", "travel_date", "seat"],
                name="unique_seat_booking_per_flight_date",
            )
        ]

    def __str__(self):
        return (
            f"{self.passenger_name} - {self.flight.flight_number} - "
            f"{self.travel_date} - {self.seat.seat_number}"
        )

    def clean(self):
        if self.seat_id and self.flight_id and self.seat.flight_id != self.flight_id:
            raise ValidationError(
                {"seat": "The selected seat does not belong to this flight."}
            )
