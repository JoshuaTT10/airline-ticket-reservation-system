from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import Http404, JsonResponse
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.http import (
    url_has_allowed_host_and_scheme,
)
from django.views.decorators.http import (
    require_GET,
    require_http_methods,
    require_POST,
)

from .forms import (
    MAX_BOOKING_DAYS,
    MAX_PASSENGERS,
    FlightSearchForm,
    MultiPassengerBookingForm,
    RegistrationForm,
    StyledAuthenticationForm,
)
from .models import (
    Booking,
    City,
    Flight,
    Reservation,
    Seat,
)


def _available_seat_count(
    flight,
    travel_date,
    ticket_class,
):
    booked_seat_ids = Booking.objects.filter(
        flight=flight,
        travel_date=travel_date,
    ).values_list(
        "seat_id",
        flat=True,
    )

    return (
        flight.seats.filter(
            cabin_class=ticket_class,
        )
        .exclude(
            pk__in=booked_seat_ids,
        )
        .count()
    )


def _build_seat_rows(
    flight,
    travel_date,
    ticket_class,
):
    booked_seat_ids = set(
        Booking.objects.filter(
            flight=flight,
            travel_date=travel_date,
        ).values_list(
            "seat_id",
            flat=True,
        )
    )

    seats = flight.seats.filter(
        cabin_class=ticket_class,
    ).order_by(
        "row_number",
        "seat_letter",
    )

    rows = {}

    for seat in seats:
        rows.setdefault(
            seat.row_number,
            [],
        ).append(
            {
                "seat": seat,
                "available": (seat.id not in booked_seat_ids),
            }
        )

    return [
        {
            "number": row_number,
            "seats": row_seats,
        }
        for (
            row_number,
            row_seats,
        ) in rows.items()
    ]


def _valid_travel_date(
    travel_date,
):
    if travel_date is None:
        return False

    today = timezone.localdate()

    latest_date = today + timedelta(days=MAX_BOOKING_DAYS)

    return today <= travel_date <= latest_date


def _valid_passenger_count(
    value,
):
    try:
        passenger_count = int(value)

    except (
        TypeError,
        ValueError,
    ):
        return None

    if not (1 <= passenger_count <= MAX_PASSENGERS):
        return None

    return passenger_count


def _remember_guest_reservation(
    request,
    booking_reference,
):
    references = request.session.get(
        "guest_reservation_references",
        [],
    )

    if booking_reference not in references:
        references.append(booking_reference)

    request.session["guest_reservation_references"] = references[-20:]


@require_GET
def home(request):
    initial = {}

    previous_search = request.session.get("flight_search")

    if previous_search:
        initial = {
            "departure_city": (previous_search.get("departure_city")),
            "arrival_city": (previous_search.get("arrival_city")),
            "travel_date": (previous_search.get("travel_date")),
            "ticket_class": (previous_search.get("ticket_class")),
            "passenger_count": (
                previous_search.get(
                    "passenger_count",
                    1,
                )
            ),
        }

    return render(
        request,
        "reservations/home.html",
        {
            "form": FlightSearchForm(initial=initial),
        },
    )


@require_GET
def destination_options(request):
    departure_city_id = request.GET.get("departure_city")

    if departure_city_id and departure_city_id.isdigit():
        cities = (
            City.objects.filter(arriving_flights__departure_city_id=(departure_city_id))
            .distinct()
            .order_by("name")
        )

    else:
        cities = City.objects.all()

    return render(
        request,
        ("reservations/partials/destination_select.html"),
        {
            "cities": cities,
        },
    )


@require_GET
def flight_search(request):
    form = FlightSearchForm(request.GET)

    results = []
    searched = False
    travel_date = None
    ticket_class = None
    passenger_count = 1

    if form.is_valid():
        searched = True

        departure_city = form.cleaned_data["departure_city"]

        arrival_city = form.cleaned_data["arrival_city"]

        travel_date = form.cleaned_data["travel_date"]

        ticket_class = form.cleaned_data["ticket_class"]

        passenger_count = form.cleaned_data["passenger_count"]

        flights = (
            Flight.objects.filter(
                departure_city=(departure_city),
                arrival_city=(arrival_city),
            )
            .select_related(
                "airline",
                "departure_city",
                "arrival_city",
            )
            .order_by("departure_time")
        )

        for flight in flights:
            available_seats = _available_seat_count(
                flight,
                travel_date,
                ticket_class,
            )

            if available_seats >= passenger_count:
                unit_price = flight.price_for_class(ticket_class)

                results.append(
                    {
                        "flight": flight,
                        "available_seats": (available_seats),
                        "price": unit_price,
                        "total_price": (unit_price * passenger_count),
                    }
                )

        request.session["flight_search"] = {
            "departure_city": (departure_city.id),
            "arrival_city": (arrival_city.id),
            "travel_date": (travel_date.isoformat()),
            "ticket_class": (ticket_class),
            "passenger_count": (passenger_count),
        }

    context = {
        "form": form,
        "results": results,
        "searched": searched,
        "travel_date": travel_date,
        "ticket_class": ticket_class,
        "passenger_count": (passenger_count),
        "ticket_class_label": dict(Seat.CabinClass.choices).get(
            ticket_class,
            "",
        ),
    }

    template_name = (
        "reservations/partials/flight_results.html"
        if request.htmx
        else ("reservations/search_results.html")
    )

    return render(
        request,
        template_name,
        context,
    )


@require_http_methods(["GET", "POST"])
def seat_selection(
    request,
    flight_id,
):
    flight = get_object_or_404(
        Flight.objects.select_related(
            "airline",
            "departure_city",
            "arrival_city",
        ),
        pk=flight_id,
    )

    if request.method == "POST":
        date_value = request.POST.get("travel_date")

        ticket_class = request.POST.get("ticket_class")

        passenger_count_value = request.POST.get("passenger_count")

    else:
        date_value = request.GET.get("date")

        ticket_class = request.GET.get("ticket_class")

        passenger_count_value = request.GET.get("passengers")

    travel_date = parse_date(date_value or "")

    passenger_count = _valid_passenger_count(passenger_count_value)

    cabin_classes = dict(Seat.CabinClass.choices)

    if not _valid_travel_date(travel_date):
        messages.error(
            request,
            ("Please select a valid travel date within the booking window."),
        )

        return redirect("reservations:home")

    if ticket_class not in cabin_classes:
        messages.error(
            request,
            "Please select a valid cabin class.",
        )

        return redirect("reservations:home")

    if passenger_count is None:
        messages.error(
            request,
            ("Please select between 1 and 5 passengers."),
        )

        return redirect("reservations:home")

    available_seats = _available_seat_count(
        flight,
        travel_date,
        ticket_class,
    )

    if available_seats < passenger_count:
        messages.error(
            request,
            ("This flight no longer has enough seats for your group."),
        )

        return redirect("reservations:home")

    unit_price = flight.price_for_class(ticket_class)

    total_price = unit_price * passenger_count

    if request.method == "POST":
        form = MultiPassengerBookingForm(
            request.POST,
            flight=flight,
            travel_date=(travel_date),
            ticket_class=(ticket_class),
            passenger_count=(passenger_count),
            user=request.user,
        )

        if form.is_valid():
            selected_seats = form.cleaned_data["seat_ids"]

            passenger_names = form.passenger_names()

            booking_user = request.user if (request.user.is_authenticated) else None

            try:
                with transaction.atomic():
                    reservation = Reservation.objects.create(
                        user=booking_user,
                        flight=flight,
                        travel_date=(travel_date),
                        cabin_class=(ticket_class),
                        total_price=(total_price),
                        currency=(flight.currency),
                    )

                    for (
                        passenger_name,
                        seat,
                    ) in zip(
                        passenger_names,
                        selected_seats,
                        strict=True,
                    ):
                        booking = Booking(
                            reservation=(reservation),
                            user=(booking_user),
                            flight=flight,
                            seat=seat,
                            travel_date=(travel_date),
                            passenger_name=(passenger_name),
                            price=(unit_price),
                            currency=(flight.currency),
                        )

                        booking.full_clean()
                        booking.save()

            except (
                IntegrityError,
                ValidationError,
            ):
                form.add_error(
                    "seat_ids",
                    (
                        "One or more of "
                        "those seats have "
                        "just been booked. "
                        "Please select your "
                        "seats again."
                    ),
                )

            else:
                if booking_user is None:
                    _remember_guest_reservation(
                        request,
                        reservation.booking_reference,
                    )

                messages.success(
                    request,
                    ("Your reservation has been completed successfully."),
                )

                return redirect(
                    ("reservations:reservation_confirmation"),
                    booking_reference=(reservation.booking_reference),
                )

    else:
        form = MultiPassengerBookingForm(
            flight=flight,
            travel_date=(travel_date),
            ticket_class=(ticket_class),
            passenger_count=(passenger_count),
            user=request.user,
        )

    return render(
        request,
        ("reservations/seat_selection.html"),
        {
            "flight": flight,
            "form": form,
            "seat_rows": (
                _build_seat_rows(
                    flight,
                    travel_date,
                    ticket_class,
                )
            ),
            "travel_date": (travel_date),
            "ticket_class": (ticket_class),
            "ticket_class_label": (cabin_classes[ticket_class]),
            "passenger_count": (passenger_count),
            "unit_price": (unit_price),
            "total_price": (total_price),
            "currency": (flight.currency),
        },
    )


@require_GET
def reservation_confirmation(
    request,
    booking_reference,
):
    reservation = get_object_or_404(
        Reservation.objects.select_related(
            "user",
            "flight",
            "flight__airline",
            "flight__departure_city",
            "flight__arrival_city",
        ).prefetch_related(
            "passenger_bookings__seat",
        ),
        booking_reference=(booking_reference),
    )

    if reservation.user_id is not None:
        if not request.user.is_authenticated or request.user.id != reservation.user_id:
            raise Http404

    else:
        allowed_references = request.session.get(
            "guest_reservation_references",
            [],
        )

        if reservation.booking_reference not in allowed_references:
            raise Http404

    return render(
        request,
        ("reservations/booking_confirmation.html"),
        {
            "reservation": reservation,
            "passenger_bookings": (reservation.passenger_bookings.all()),
        },
    )


@login_required
@require_GET
def booking_history(request):
    reservations = (
        Reservation.objects.filter(
            user=request.user,
        )
        .select_related(
            "flight",
            "flight__airline",
            "flight__departure_city",
            "flight__arrival_city",
        )
        .prefetch_related(
            "passenger_bookings__seat",
        )
        .order_by(
            "-travel_date",
            "-created_at",
        )
    )

    return render(
        request,
        ("reservations/booking_history.html"),
        {
            "reservations": reservations,
        },
    )


@require_http_methods(["GET", "POST"])
def register_view(request):
    if request.user.is_authenticated:
        return redirect("reservations:home")

    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()

            login(
                request,
                user,
            )

            messages.success(
                request,
                ("Account created successfully. Welcome aboard!"),
            )

            return redirect("reservations:home")

    else:
        form = RegistrationForm()

    return render(
        request,
        "reservations/register.html",
        {
            "form": form,
        },
    )


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect("reservations:home")

    next_url = request.POST.get("next") or request.GET.get(
        "next",
        "",
    )

    if request.method == "POST":
        form = StyledAuthenticationForm(
            request,
            data=request.POST,
        )

        if form.is_valid():
            login(
                request,
                form.get_user(),
            )

            messages.success(
                request,
                "You are now signed in.",
            )

            if next_url and url_has_allowed_host_and_scheme(
                url=next_url,
                allowed_hosts={request.get_host()},
                require_https=(request.is_secure()),
            ):
                return redirect(next_url)

            return redirect("reservations:home")

    else:
        form = StyledAuthenticationForm(request)

    return render(
        request,
        "reservations/login.html",
        {
            "form": form,
            "next": next_url,
        },
    )


@require_POST
def logout_view(request):
    logout(request)

    messages.success(
        request,
        "You have been signed out.",
    )

    return redirect("reservations:home")


@require_GET
def health_check(request):
    return JsonResponse(
        {
            "status": "ok",
        }
    )
