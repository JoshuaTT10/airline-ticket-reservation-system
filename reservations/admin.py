from django.contrib import admin

from .models import (
    Airline,
    Booking,
    City,
    Flight,
    Reservation,
    Seat,
)


class BookingInline(admin.TabularInline):
    model = Booking
    extra = 0

    fields = (
        "passenger_name",
        "seat",
        "price",
        "currency",
    )

    readonly_fields = fields

    can_delete = False

    def has_add_permission(
        self,
        request,
        obj=None,
    ):
        return False


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "airport_code",
        "country",
    )

    search_fields = (
        "name",
        "airport_code",
        "country",
    )


@admin.register(Airline)
class AirlineAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "airline_code",
    )

    search_fields = (
        "name",
        "airline_code",
    )


@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = (
        "flight_number",
        "airline",
        "departure_city",
        "arrival_city",
        "departure_time",
        "arrival_time",
        "economy_price",
        "business_price",
        "currency",
    )

    list_filter = (
        "airline",
        "departure_city",
        "arrival_city",
    )

    search_fields = (
        "flight_number",
        "airline__name",
        "departure_city__airport_code",
        "arrival_city__airport_code",
    )


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = (
        "flight",
        "seat_number",
        "cabin_class",
    )

    list_filter = (
        "cabin_class",
        "flight",
    )


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = (
        "booking_reference",
        "flight",
        "travel_date",
        "cabin_class",
        "passenger_count",
        "total_price",
        "currency",
        "user",
        "created_at",
    )

    list_filter = (
        "travel_date",
        "cabin_class",
        "flight",
    )

    search_fields = (
        "booking_reference",
        "user__username",
        "user__email",
    )

    readonly_fields = (
        "booking_reference",
        "created_at",
    )

    inlines = [
        BookingInline,
    ]


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "passenger_name",
        "reservation",
        "flight",
        "travel_date",
        "seat",
        "price",
        "currency",
        "user",
    )

    list_filter = (
        "travel_date",
        "flight",
    )

    search_fields = (
        "passenger_name",
        "reservation__booking_reference",
        "user__username",
    )
