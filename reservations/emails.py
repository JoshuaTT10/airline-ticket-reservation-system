from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from .models import Reservation


def _get_reservation(reservation_id):
    return (
        Reservation.objects.select_related(
            "user",
            "flight",
            "flight__airline",
            "flight__departure_city",
            "flight__arrival_city",
        )
        .prefetch_related(
            "passenger_bookings__seat",
        )
        .get(pk=reservation_id)
    )


def _send_reservation_email(
    *,
    reservation,
    subject,
    template_name,
):
    if not reservation.contact_email:
        return 0

    passenger_bookings = reservation.passenger_bookings.all()

    message = render_to_string(
        template_name,
        {
            "reservation": reservation,
            "passenger_bookings": passenger_bookings,
        },
    )

    return send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[reservation.contact_email],
        fail_silently=False,
    )


def send_reservation_confirmation_email(reservation_id):
    reservation = _get_reservation(reservation_id)

    subject = f"Your AeroReserve booking is confirmed — {reservation.booking_reference}"

    return _send_reservation_email(
        reservation=reservation,
        subject=subject,
        template_name=("reservations/emails/reservation_confirmation_email.txt"),
    )


def send_reservation_cancellation_email(reservation_id):
    reservation = _get_reservation(reservation_id)

    subject = (
        f"Your AeroReserve reservation "
        f"{reservation.booking_reference} has been cancelled"
    )

    return _send_reservation_email(
        reservation=reservation,
        subject=subject,
        template_name=("reservations/emails/reservation_cancellation_email.txt"),
    )
