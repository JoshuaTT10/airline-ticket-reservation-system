from datetime import time

from django.core.management.base import BaseCommand

from reservations.models import Airline, City, Flight, Seat


class Command(BaseCommand):
    help = "Create demo airline reservation data using real Japanese airlines and airports."

    def handle(self, *args, **options):
        cities = [
            ("Tokyo Haneda", "HND"),
            ("Osaka Itami", "ITM"),
            ("Sapporo New Chitose", "CTS"),
            ("Fukuoka", "FUK"),
            ("Okinawa Naha", "OKA"),
        ]

        airlines = [
            ("All Nippon Airways", "NH"),
            ("Japan Airlines", "JL"),
            ("Peach Aviation", "MM"),
            ("Skymark Airlines", "BC"),
        ]

        flights = [
            ("NH101", "NH", "HND", "ITM", time(8, 30), time(9, 45)),
            ("JL115", "JL", "HND", "ITM", time(12, 15), time(13, 30)),
            ("BC221", "BC", "HND", "ITM", time(17, 10), time(18, 25)),
            ("NH202", "NH", "ITM", "HND", time(10, 30), time(11, 45)),
            ("JL304", "JL", "ITM", "HND", time(15, 20), time(16, 35)),
            ("NH511", "NH", "HND", "CTS", time(9, 0), time(10, 40)),
            ("JL523", "JL", "HND", "CTS", time(14, 20), time(16, 0)),
            ("MM601", "MM", "HND", "FUK", time(10, 45), time(12, 40)),
            ("NH612", "NH", "FUK", "HND", time(16, 0), time(17, 55)),
            ("JL701", "JL", "HND", "OKA", time(7, 50), time(10, 35)),
            ("BC715", "BC", "HND", "OKA", time(13, 30), time(16, 15)),
        ]

        city_objects = {}

        for name, airport_code in cities:
            city, _ = City.objects.update_or_create(
                airport_code=airport_code,
                defaults={"name": name},
            )
            city_objects[airport_code] = city

        airline_objects = {}

        for name, airline_code in airlines:
            airline, _ = Airline.objects.update_or_create(
                airline_code=airline_code,
                defaults={"name": name},
            )
            airline_objects[airline_code] = airline

        created_flights = 0
        created_seats = 0

        for (
            flight_number,
            airline_code,
            departure_code,
            arrival_code,
            departure_time,
            arrival_time,
        ) in flights:
            flight, created = Flight.objects.update_or_create(
                flight_number=flight_number,
                defaults={
                    "airline": airline_objects[airline_code],
                    "departure_city": city_objects[departure_code],
                    "arrival_city": city_objects[arrival_code],
                    "departure_time": departure_time,
                    "arrival_time": arrival_time,
                },
            )

            if created:
                created_flights += 1

            for row_number in range(1, 6):
                cabin_class = (
                    Seat.CabinClass.BUSINESS
                    if row_number <= 3
                    else Seat.CabinClass.ECONOMY
                )

                for seat_letter in Seat.SeatLetter.values:
                    _, seat_created = Seat.objects.get_or_create(
                        flight=flight,
                        row_number=row_number,
                        seat_letter=seat_letter,
                        defaults={
                            "cabin_class": cabin_class,
                        },
                    )

                    if seat_created:
                        created_seats += 1

        self.stdout.write(
            self.style.SUCCESS(
                "Demo airline data created successfully: "
                f"{created_flights} new flights and "
                f"{created_seats} new seats added."
            )
        )
