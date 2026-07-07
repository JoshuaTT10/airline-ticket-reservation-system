from django.contrib import admin

from .models import Airline, Booking, City, Flight, Seat


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("name", "airport_code")
    search_fields = ("name", "airport_code")


@admin.register(Airline)
class AirlineAdmin(admin.ModelAdmin):
    list_display = ("name", "airline_code")
    search_fields = ("name", "airline_code")


@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = (
        "flight_number",
        "airline",
        "departure_city",
        "arrival_city",
        "departure_time",
        "arrival_time",
    )
    list_filter = ("airline",)
    search_fields = ("flight_number",)


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ("flight", "seat_number", "cabin_class")
    list_filter = ("cabin_class", "flight")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "passenger_name",
        "flight",
        "travel_date",
        "seat",
        "user",
        "created_at",
    )
    list_filter = ("travel_date", "flight")
    search_fields = ("passenger_name", "user__username")
