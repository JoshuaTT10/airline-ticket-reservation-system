from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views
from .forms import StyledPasswordResetForm, StyledSetPasswordForm

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
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="reservations/password_reset_form.html",
            form_class=StyledPasswordResetForm,
            email_template_name="reservations/password_reset_email.txt",
            subject_template_name="reservations/password_reset_subject.txt",
            success_url=reverse_lazy("reservations:password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="reservations/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="reservations/password_reset_confirm.html",
            form_class=StyledSetPasswordForm,
            success_url=reverse_lazy("reservations:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="reservations/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
    path(
        "health/",
        views.health_check,
        name="health_check",
    ),
]
