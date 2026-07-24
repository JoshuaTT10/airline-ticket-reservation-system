import math
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand

from reservations.models import (
    Airline,
    Booking,
    City,
    Flight,
    Reservation,
    Seat,
)

AIRPORTS = [
    (
        "HND",
        "Tokyo Haneda",
        "Japan",
        35.5494,
        139.7798,
    ),
    (
        "KIX",
        "Osaka Kansai",
        "Japan",
        34.4347,
        135.2440,
    ),
    (
        "CTS",
        "Sapporo New Chitose",
        "Japan",
        42.7752,
        141.6923,
    ),
    (
        "FUK",
        "Fukuoka",
        "Japan",
        33.5859,
        130.4507,
    ),
    (
        "OKA",
        "Okinawa Naha",
        "Japan",
        26.1958,
        127.6459,
    ),
    (
        "ICN",
        "Seoul Incheon",
        "South Korea",
        37.4602,
        126.4407,
    ),
    (
        "PEK",
        "Beijing Capital",
        "China",
        40.0799,
        116.6031,
    ),
    (
        "PVG",
        "Shanghai Pudong",
        "China",
        31.1443,
        121.8083,
    ),
    (
        "HKG",
        "Hong Kong International",
        "Hong Kong",
        22.3080,
        113.9185,
    ),
    (
        "SIN",
        "Singapore Changi",
        "Singapore",
        1.3644,
        103.9915,
    ),
    (
        "BKK",
        "Bangkok Suvarnabhumi",
        "Thailand",
        13.6900,
        100.7501,
    ),
    (
        "KUL",
        "Kuala Lumpur International",
        "Malaysia",
        2.7456,
        101.7072,
    ),
    (
        "DEL",
        "Delhi Indira Gandhi",
        "India",
        28.5562,
        77.1000,
    ),
    (
        "BOM",
        "Mumbai Chhatrapati Shivaji",
        "India",
        19.0896,
        72.8656,
    ),
    (
        "DXB",
        "Dubai International",
        "United Arab Emirates",
        25.2532,
        55.3657,
    ),
    (
        "DOH",
        "Doha Hamad International",
        "Qatar",
        25.2731,
        51.6081,
    ),
    (
        "LHR",
        "London Heathrow",
        "United Kingdom",
        51.4700,
        -0.4543,
    ),
    (
        "CDG",
        "Paris Charles de Gaulle",
        "France",
        49.0097,
        2.5479,
    ),
    (
        "FRA",
        "Frankfurt",
        "Germany",
        50.0379,
        8.5622,
    ),
    (
        "AMS",
        "Amsterdam Schiphol",
        "Netherlands",
        52.3105,
        4.7683,
    ),
    (
        "MAD",
        "Madrid Barajas",
        "Spain",
        40.4983,
        -3.5676,
    ),
    (
        "FCO",
        "Rome Fiumicino",
        "Italy",
        41.8003,
        12.2389,
    ),
    (
        "IST",
        "Istanbul",
        "Türkiye",
        41.2753,
        28.7519,
    ),
    (
        "ZRH",
        "Zurich",
        "Switzerland",
        47.4581,
        8.5555,
    ),
    (
        "VIE",
        "Vienna",
        "Austria",
        48.1103,
        16.5697,
    ),
    (
        "LIS",
        "Lisbon",
        "Portugal",
        38.7742,
        -9.1342,
    ),
    (
        "DUB",
        "Dublin",
        "Ireland",
        53.4213,
        -6.2701,
    ),
    (
        "CPH",
        "Copenhagen",
        "Denmark",
        55.6180,
        12.6508,
    ),
    (
        "ARN",
        "Stockholm Arlanda",
        "Sweden",
        59.6519,
        17.9186,
    ),
    (
        "JFK",
        "New York JFK",
        "United States",
        40.6413,
        -73.7781,
    ),
    (
        "LAX",
        "Los Angeles",
        "United States",
        33.9416,
        -118.4085,
    ),
    (
        "SFO",
        "San Francisco",
        "United States",
        37.6213,
        -122.3790,
    ),
    (
        "ORD",
        "Chicago O'Hare",
        "United States",
        41.9742,
        -87.9073,
    ),
    (
        "MIA",
        "Miami",
        "United States",
        25.7959,
        -80.2870,
    ),
    (
        "YYZ",
        "Toronto Pearson",
        "Canada",
        43.6777,
        -79.6248,
    ),
    (
        "YVR",
        "Vancouver",
        "Canada",
        49.1967,
        -123.1815,
    ),
    (
        "MEX",
        "Mexico City",
        "Mexico",
        19.4361,
        -99.0719,
    ),
    (
        "GRU",
        "São Paulo Guarulhos",
        "Brazil",
        -23.4356,
        -46.4731,
    ),
    (
        "GIG",
        "Rio de Janeiro Galeão",
        "Brazil",
        -22.8090,
        -43.2506,
    ),
    (
        "EZE",
        "Buenos Aires Ezeiza",
        "Argentina",
        -34.8222,
        -58.5358,
    ),
    (
        "SCL",
        "Santiago",
        "Chile",
        -33.3929,
        -70.7858,
    ),
    (
        "LIM",
        "Lima Jorge Chávez",
        "Peru",
        -12.0219,
        -77.1143,
    ),
    (
        "SYD",
        "Sydney",
        "Australia",
        -33.9399,
        151.1753,
    ),
    (
        "MEL",
        "Melbourne",
        "Australia",
        -37.6690,
        144.8410,
    ),
    (
        "AKL",
        "Auckland",
        "New Zealand",
        -37.0082,
        174.7850,
    ),
    (
        "JNB",
        "Johannesburg",
        "South Africa",
        -26.1367,
        28.2411,
    ),
    (
        "CPT",
        "Cape Town",
        "South Africa",
        -33.9700,
        18.6021,
    ),
    (
        "CAI",
        "Cairo",
        "Egypt",
        30.1219,
        31.4056,
    ),
    (
        "NBO",
        "Nairobi",
        "Kenya",
        -1.3192,
        36.9278,
    ),
    (
        "CMN",
        "Casablanca",
        "Morocco",
        33.3675,
        -7.58997,
    ),
]


AIRLINES = [
    ("NH", "All Nippon Airways"),
    ("JL", "Japan Airlines"),
    ("KE", "Korean Air"),
    ("CA", "Air China"),
    ("MU", "China Eastern Airlines"),
    ("CX", "Cathay Pacific"),
    ("SQ", "Singapore Airlines"),
    ("TG", "Thai Airways"),
    ("MH", "Malaysia Airlines"),
    ("AI", "Air India"),
    ("EK", "Emirates"),
    ("QR", "Qatar Airways"),
    ("BA", "British Airways"),
    ("AF", "Air France"),
    ("LH", "Lufthansa"),
    ("KL", "KLM"),
    ("IB", "Iberia"),
    ("AZ", "ITA Airways"),
    ("TK", "Turkish Airlines"),
    ("LX", "Swiss International Air Lines"),
    ("OS", "Austrian Airlines"),
    ("TP", "TAP Air Portugal"),
    ("EI", "Aer Lingus"),
    ("SK", "Scandinavian Airlines"),
    ("UA", "United Airlines"),
    ("AC", "Air Canada"),
    ("AM", "Aeromexico"),
    ("LA", "LATAM Airlines"),
    ("QF", "Qantas"),
    ("NZ", "Air New Zealand"),
    ("SA", "South African Airways"),
    ("MS", "EgyptAir"),
    ("KQ", "Kenya Airways"),
    ("AT", "Royal Air Maroc"),
]


HOME_AIRLINE = {
    "HND": "NH",
    "KIX": "JL",
    "CTS": "NH",
    "FUK": "JL",
    "OKA": "NH",
    "ICN": "KE",
    "PEK": "CA",
    "PVG": "MU",
    "HKG": "CX",
    "SIN": "SQ",
    "BKK": "TG",
    "KUL": "MH",
    "DEL": "AI",
    "BOM": "AI",
    "DXB": "EK",
    "DOH": "QR",
    "LHR": "BA",
    "CDG": "AF",
    "FRA": "LH",
    "AMS": "KL",
    "MAD": "IB",
    "FCO": "AZ",
    "IST": "TK",
    "ZRH": "LX",
    "VIE": "OS",
    "LIS": "TP",
    "DUB": "EI",
    "CPH": "SK",
    "ARN": "SK",
    "JFK": "UA",
    "LAX": "UA",
    "SFO": "UA",
    "ORD": "UA",
    "MIA": "UA",
    "YYZ": "AC",
    "YVR": "AC",
    "MEX": "AM",
    "GRU": "LA",
    "GIG": "LA",
    "EZE": "LA",
    "SCL": "LA",
    "LIM": "LA",
    "SYD": "QF",
    "MEL": "QF",
    "AKL": "NZ",
    "JNB": "SA",
    "CPT": "SA",
    "CAI": "MS",
    "NBO": "KQ",
    "CMN": "AT",
}


GLOBAL_HUBS = [
    "HND",
    "SIN",
    "DXB",
    "DOH",
    "LHR",
    "CDG",
    "FRA",
    "JFK",
    "LAX",
    "SYD",
]


POPULAR_ROUTES = [
    ("HND", "KIX"),
    ("HND", "CTS"),
    ("HND", "FUK"),
    ("HND", "OKA"),
    ("HND", "ICN"),
    ("HND", "SIN"),
    ("HND", "LHR"),
    ("HND", "JFK"),
    ("SIN", "BKK"),
    ("SIN", "KUL"),
    ("SIN", "SYD"),
    ("SIN", "DXB"),
    ("DXB", "LHR"),
    ("DXB", "CDG"),
    ("DXB", "BOM"),
    ("DXB", "DEL"),
    ("DOH", "LHR"),
    ("LHR", "JFK"),
    ("LHR", "CDG"),
    ("LHR", "FRA"),
    ("CDG", "JFK"),
    ("FRA", "JFK"),
    ("JFK", "LAX"),
    ("LAX", "SFO"),
    ("SYD", "MEL"),
    ("SYD", "AKL"),
]


def haversine_km(origin, destination):
    """
    Calculate approximate great-circle distance between two airports.
    """
    latitude_1 = math.radians(float(origin.latitude))

    longitude_1 = math.radians(float(origin.longitude))

    latitude_2 = math.radians(float(destination.latitude))

    longitude_2 = math.radians(float(destination.longitude))

    latitude_difference = latitude_2 - latitude_1

    longitude_difference = longitude_2 - longitude_1

    value = (
        math.sin(latitude_difference / 2) ** 2
        + math.cos(latitude_1)
        * math.cos(latitude_2)
        * math.sin(longitude_difference / 2) ** 2
    )

    return 6371 * 2 * math.asin(math.sqrt(value))


def calculate_prices(distance):
    """
    Generate realistic-looking demo fares based on distance.
    """
    economy_price = max(
        75,
        45 + distance * 0.075,
    )

    economy_price = round(economy_price / 5) * 5

    economy_price = Decimal(str(economy_price)).quantize(Decimal("0.00"))

    business_price = (economy_price * Decimal("2.60")).quantize(Decimal("0.00"))

    return (
        economy_price,
        business_price,
    )


def calculate_duration_hours(
    distance,
):
    """
    Generate an approximate demo flight duration.
    """
    return max(
        1.0,
        0.7 + distance / 820,
    )


def route_seed(
    origin_code,
    destination_code,
):
    """
    Generate a deterministic integer for a route.

    This allows route frequency and departure times to remain stable
    every time the seed database is rebuilt.
    """
    return sum(
        (index + 1) * ord(character)
        for index, character in enumerate(origin_code + destination_code)
    )


def calculate_departure_time(
    route_value,
    flight_index,
):
    """
    Select a deterministic departure slot for each route service.
    """
    departure_slots = [
        time(6, 20),
        time(10, 45),
        time(15, 10),
        time(18, 20),
    ]

    slot_index = (route_value + flight_index) % len(departure_slots)

    return departure_slots[slot_index]


def calculate_arrival_time(
    departure_time,
    duration_hours,
):
    """
    Calculate arrival time from departure time and demo duration.
    """
    base_datetime = datetime.combine(
        datetime.today().date(),
        departure_time,
    )

    arrival_datetime = base_datetime + timedelta(minutes=int(duration_hours * 60))

    return arrival_datetime.time().replace(
        second=0,
        microsecond=0,
    )


class Command(BaseCommand):
    help = "Seed AeroReserve with demo airports, airlines, flights, prices and seats."

    def add_arguments(
        self,
        parser,
    ):
        parser.add_argument(
            "--reset",
            action="store_true",
            help=("Delete existing demo airline data before rebuilding it."),
        )

    def handle(
        self,
        *args,
        **options,
    ):
        reset = options["reset"]

        if not reset and City.objects.exists() and Flight.objects.exists():
            self.stdout.write(
                self.style.SUCCESS("Demo airline data already exists. Skipping seed.")
            )

            return

        if reset:
            self.stdout.write("Removing existing demo airline data...")

            Booking.objects.all().delete()
            Reservation.objects.all().delete()
            Seat.objects.all().delete()
            Flight.objects.all().delete()
            Airline.objects.all().delete()
            City.objects.all().delete()

        self.stdout.write("Creating airports...")

        cities = {}

        for (
            airport_code,
            airport_name,
            country,
            latitude,
            longitude,
        ) in AIRPORTS:
            city, _ = City.objects.update_or_create(
                airport_code=airport_code,
                defaults={
                    "name": airport_name,
                    "country": country,
                    "latitude": Decimal(str(latitude)),
                    "longitude": Decimal(str(longitude)),
                },
            )

            cities[airport_code] = city

        self.stdout.write("Creating airlines...")

        airlines = {}

        for (
            airline_code,
            airline_name,
        ) in AIRLINES:
            airline, _ = Airline.objects.update_or_create(
                airline_code=(airline_code),
                defaults={
                    "name": (airline_name),
                },
            )

            airlines[airline_code] = airline

        self.stdout.write("Building route network...")

        routes = set()

        # Give each airport connections to
        # its four geographically nearest airports.
        for origin in cities.values():
            nearest_airports = sorted(
                (
                    (
                        haversine_km(
                            origin,
                            destination,
                        ),
                        destination,
                    )
                    for destination in cities.values()
                    if (destination.id != origin.id)
                ),
                key=lambda item: item[0],
            )[:4]

            for (
                _,
                destination,
            ) in nearest_airports:
                routes.add(
                    (
                        origin.airport_code,
                        destination.airport_code,
                    )
                )

                routes.add(
                    (
                        destination.airport_code,
                        origin.airport_code,
                    )
                )

        # Connect airports to several major global hubs.
        for airport_code in cities:
            for hub_code in GLOBAL_HUBS[:4]:
                if airport_code == hub_code:
                    continue

                routes.add(
                    (
                        airport_code,
                        hub_code,
                    )
                )

                routes.add(
                    (
                        hub_code,
                        airport_code,
                    )
                )

        # Guarantee important routes used during demos.
        for (
            origin_code,
            destination_code,
        ) in POPULAR_ROUTES:
            routes.add(
                (
                    origin_code,
                    destination_code,
                )
            )

            routes.add(
                (
                    destination_code,
                    origin_code,
                )
            )

        self.stdout.write("Creating recurring flights and seats...")

        airline_counters = {
            airline_code: 100
            for (
                airline_code,
                _,
            ) in AIRLINES
        }

        created_flights = 0
        created_seats = 0

        for (
            origin_code,
            destination_code,
        ) in sorted(routes):
            origin = cities[origin_code]

            destination = cities[destination_code]

            airline_code = HOME_AIRLINE.get(
                origin_code,
                "NH",
            )

            airline = airlines[airline_code]

            distance = haversine_km(
                origin,
                destination,
            )

            (
                economy_price,
                business_price,
            ) = calculate_prices(distance)

            duration_hours = calculate_duration_hours(distance)

            route_value = route_seed(
                origin_code,
                destination_code,
            )

            # Each configured route receives between
            # one and three recurring daily services.
            #
            # City pairs that are not in the generated
            # route network naturally have zero flights.
            flight_count = 1 + route_value % 3

            for flight_index in range(flight_count):
                airline_counters[airline_code] += 1

                flight_number = f"{airline_code}{airline_counters[airline_code]}"

                departure_time = calculate_departure_time(
                    route_value,
                    flight_index,
                )

                arrival_time = calculate_arrival_time(
                    departure_time,
                    duration_hours,
                )

                flight, flight_created = Flight.objects.update_or_create(
                    flight_number=(flight_number),
                    defaults={
                        "airline": (airline),
                        "departure_city": (origin),
                        "arrival_city": (destination),
                        "departure_time": (departure_time),
                        "arrival_time": (arrival_time),
                        "economy_price": (economy_price),
                        "business_price": (business_price),
                        "currency": ("USD"),
                    },
                )

                if flight_created:
                    created_flights += 1

                # 5 rows × 4 seats = 20 seats.
                #
                # Rows 1–3: Business
                # Rows 4–5: Economy
                for row_number in range(
                    1,
                    6,
                ):
                    if row_number <= 3:
                        cabin_class = Seat.CabinClass.BUSINESS
                    else:
                        cabin_class = Seat.CabinClass.ECONOMY

                    for seat_letter in Seat.SeatLetter.values:
                        (
                            _,
                            seat_created,
                        ) = Seat.objects.update_or_create(
                            flight=flight,
                            row_number=(row_number),
                            seat_letter=(seat_letter),
                            defaults={
                                "cabin_class": (cabin_class),
                            },
                        )

                        if seat_created:
                            created_seats += 1

        self.stdout.write("")

        self.stdout.write(self.style.SUCCESS("AeroReserve demo data is ready."))

        self.stdout.write(f"Airports: {City.objects.count()}")

        self.stdout.write(f"Airlines: {Airline.objects.count()}")

        self.stdout.write(f"Flights: {Flight.objects.count()}")

        self.stdout.write(f"Seats: {Seat.objects.count()}")

        self.stdout.write(f"New flights created during this run: {created_flights}")

        self.stdout.write(f"New seats created during this run: {created_seats}")
