from datetime import timedelta

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserCreationForm,
)
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from .models import Booking, City, Seat

MAX_BOOKING_DAYS = 14
MAX_PASSENGERS = 5


class AirportModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.airport_code} — {obj.name}, {obj.country}"


class FlightSearchForm(forms.Form):
    departure_city = AirportModelChoiceField(
        queryset=City.objects.none(),
        empty_label="Select departure",
        label="From",
    )

    arrival_city = AirportModelChoiceField(
        queryset=City.objects.none(),
        empty_label="Select destination",
        label="To",
    )

    travel_date = forms.DateField(
        label="Travel date",
        widget=forms.DateInput(
            attrs={
                "type": "date",
            }
        ),
    )

    ticket_class = forms.ChoiceField(
        label="Cabin class",
        choices=Seat.CabinClass.choices,
    )

    passenger_count = forms.TypedChoiceField(
        label="Passengers",
        choices=[
            (number, str(number))
            for number in range(
                1,
                MAX_PASSENGERS + 1,
            )
        ],
        coerce=int,
        initial=1,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        cities = City.objects.all()

        self.fields["departure_city"].queryset = cities
        self.fields["arrival_city"].queryset = cities

        today = timezone.localdate()
        latest_date = today + timedelta(days=MAX_BOOKING_DAYS)

        self.fields["travel_date"].widget.attrs.update(
            {
                "min": today.isoformat(),
                "max": latest_date.isoformat(),
            }
        )

        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

        self.fields["departure_city"].widget.attrs.update(
            {
                "class": "form-control airport-select",
                "data-airport-select": "true",
                "hx-get": reverse("reservations:destination_options"),
                "hx-trigger": "change",
                "hx-target": ("#destination-select-container"),
                "hx-include": ("[name='departure_city']"),
                "hx-swap": "innerHTML",
            }
        )

        self.fields["arrival_city"].widget.attrs.update(
            {
                "class": "form-control airport-select",
                "data-airport-select": "true",
            }
        )

    def clean_travel_date(self):
        travel_date = self.cleaned_data["travel_date"]

        today = timezone.localdate()

        latest_date = today + timedelta(days=MAX_BOOKING_DAYS)

        if travel_date < today:
            raise forms.ValidationError("The travel date cannot be in the past.")

        if travel_date > latest_date:
            raise forms.ValidationError(
                f"Reservations can only be made up to "
                f"{MAX_BOOKING_DAYS} days in advance."
            )

        return travel_date

    def clean(self):
        cleaned_data = super().clean()

        departure = cleaned_data.get("departure_city")

        arrival = cleaned_data.get("arrival_city")

        if departure and arrival and departure == arrival:
            raise forms.ValidationError("Departure and destination must be different.")

        return cleaned_data


class MultiPassengerBookingForm(forms.Form):
    seat_ids = forms.CharField(
        widget=forms.HiddenInput(),
    )

    def __init__(
        self,
        *args,
        flight,
        travel_date,
        ticket_class,
        passenger_count,
        user=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.flight = flight
        self.travel_date = travel_date
        self.ticket_class = ticket_class
        self.passenger_count = passenger_count
        self.user = user

        default_name = ""

        if user is not None and user.is_authenticated:
            default_name = user.get_full_name().strip() or user.username

        for number in range(
            1,
            passenger_count + 1,
        ):
            self.fields[f"passenger_{number}_name"] = forms.CharField(
                max_length=100,
                label=f"Passenger {number}",
                initial=(default_name if number == 1 else ""),
                widget=forms.TextInput(
                    attrs={
                        "class": "form-control",
                        "placeholder": (f"Passenger {number} full name"),
                        "autocomplete": "name",
                    }
                ),
            )

    def clean_seat_ids(self):
        raw_value = self.cleaned_data["seat_ids"]

        try:
            seat_ids = [
                int(value.strip()) for value in raw_value.split(",") if value.strip()
            ]

        except ValueError as error:
            raise forms.ValidationError("Invalid seat selection.") from error

        if len(seat_ids) != self.passenger_count:
            raise forms.ValidationError(
                f"Please select exactly {self.passenger_count} seats."
            )

        if len(set(seat_ids)) != len(seat_ids):
            raise forms.ValidationError("The same seat cannot be selected twice.")

        booked_seat_ids = Booking.objects.filter(
            flight=self.flight,
            travel_date=self.travel_date,
        ).values_list(
            "seat_id",
            flat=True,
        )

        seats = list(
            Seat.objects.filter(
                id__in=seat_ids,
                flight=self.flight,
                cabin_class=self.ticket_class,
            ).exclude(
                id__in=booked_seat_ids,
            )
        )

        if len(seats) != self.passenger_count:
            raise forms.ValidationError(
                "One or more selected seats are no longer available."
            )

        seat_map = {seat.id: seat for seat in seats}

        return [seat_map[seat_id] for seat_id in seat_ids]

    def passenger_names(self):
        return [
            self.cleaned_data[f"passenger_{number}_name"].strip()
            for number in range(
                1,
                self.passenger_count + 1,
            )
        ]


class RegistrationForm(UserCreationForm):
    full_name = forms.CharField(
        max_length=100,
        label="Full name",
    )

    email = forms.EmailField(
        label="Email address",
    )

    class Meta(UserCreationForm.Meta):
        model = User

        fields = (
            "username",
            "full_name",
            "email",
        )

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        placeholders = {
            "username": "Choose a username",
            "full_name": "Your full name",
            "email": "you@example.com",
            "password1": "Create a password",
            "password2": "Repeat your password",
        }

        for (
            field_name,
            field,
        ) in self.fields.items():
            field.widget.attrs["class"] = "form-control"

            field.widget.attrs["placeholder"] = placeholders.get(
                field_name,
                "",
            )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account with this email address already exists."
            )

        return email

    def save(self, commit=True):
        user = super().save(commit=False)

        full_name = self.cleaned_data["full_name"].strip()

        name_parts = full_name.split(maxsplit=1)

        user.first_name = name_parts[0]

        user.last_name = name_parts[1] if len(name_parts) > 1 else ""

        user.email = self.cleaned_data["email"].strip().lower()

        if commit:
            user.save()

        return user


class StyledAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Username or email",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": ("Username or email"),
                "autocomplete": "username",
            }
        ),
    )

    password = forms.CharField(
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Password",
                "autocomplete": ("current-password"),
            }
        ),
    )

    def clean(self):
        identifier = self.cleaned_data.get("username")

        password = self.cleaned_data.get("password")

        if identifier and password:
            identifier = identifier.strip()

            email_user = User.objects.filter(email__iexact=identifier).first()

            username = email_user.username if email_user is not None else identifier

            self.user_cache = authenticate(
                self.request,
                username=username,
                password=password,
            )

            if self.user_cache is None:
                raise forms.ValidationError(
                    ("The username/email or password is incorrect."),
                    code="invalid_login",
                )

            self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data
