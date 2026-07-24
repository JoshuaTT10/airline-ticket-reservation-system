from django.urls import path

from . import views

app_name = "reservations"

urlpatterns = [
    path(
        "",
        views.home,
        name="home",
    ),
    path(
        "airports/destinations/",
        views.destination_options,
        name="destination_options",
    ),
    path(
        "flights/search/",
        views.flight_search,
        name="flight_search",
    ),
    path(
        "flights/<int:flight_id>/seats/",
        views.seat_selection,
        name="seat_selection",
    ),
    path(
        "bookings/",
        views.booking_history,
        name="booking_history",
    ),
    path(
        "reservations/<str:booking_reference>/",
        views.reservation_confirmation,
        name="reservation_confirmation",
    ),
    path(
        "register/",
        views.register_view,
        name="register",
    ),
    path(
        "login/",
        views.login_view,
        name="login",
    ),
    path(
        "logout/",
        views.logout_view,
        name="logout",
    ),
    path(
        "health/",
        views.health_check,
        name="health_check",
    ),
]
