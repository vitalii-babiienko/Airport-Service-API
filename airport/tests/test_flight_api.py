from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from airport.models import (
    Flight,
    Airport,
    Route,
    Crew,
)
from airport.serializers import (
    FlightListSerializer,
    FlightDetailSerializer,
)
from airport.tests.test_airplane_api import sample_airplane

FLIGHT_URL = reverse("airport:flight-list")
NUMBER_OF_FLIGHTS = 5
PAGINATION_COUNT = 5


def create_airports():
    return [
        Airport.objects.create(
            name=f"Name {i}",
            city=f"City {i}",
            country=f"Country {i}",
            iata_code=f"A{i}",
            latitude=i,
            longitude=i,
        )
        for i in range(NUMBER_OF_FLIGHTS + 1)
    ]


def create_routes(airports):
    return [
        Route.objects.create(
            source=airports[i],
            destination=airports[i + 1]
        )
        for i in range(NUMBER_OF_FLIGHTS)
    ]


def create_crews(number):
    return [
        Crew.objects.create(
            first_name=f"First Name {i}",
            last_name=f"Last Name {i}",
            position=f"F{i}",
        )
        for i in range(number)
    ]


def create_flights(routes, airplane):
    return [
        Flight.objects.create(
            route=routes[i],
            airplane=airplane,
            departure_time=f"2023-09-15 {(12 + i) % 23}:00+03:00",
            arrival_time=f"2023-09-16 {(15 + i) % 23}:00+03:00",
        )
        for i in range(NUMBER_OF_FLIGHTS)
    ]


def add_crews_to_flights(crews, flights):
    for i in range(NUMBER_OF_FLIGHTS):
        for crew in crews:
            flights[i].crews.add(crew)

    for flight in flights:
        flight.save()


def detail_url(flight_id):
    return reverse("airport:flight-detail", args=[flight_id])


class UnauthenticatedFlightApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(FLIGHT_URL)

        self.assertEquals(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedFlightApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "test_pass",
        )
        self.client.force_authenticate(self.user)

    def test_list_flights(self):
        airports = create_airports()
        routes = create_routes(airports)
        airplane = sample_airplane()
        crews = create_crews(4)
        flights_ = create_flights(routes, airplane)
        add_crews_to_flights(crews, flights_)

        res = self.client.get(FLIGHT_URL)

        flights = Flight.objects.order_by("id")
        serializer = FlightListSerializer(flights, many=True)

        self.assertEquals(res.status_code, status.HTTP_200_OK)

        for i in range(PAGINATION_COUNT):
            for key in serializer.data[i]:
                self.assertEquals(
                    res.data["results"][i][key],
                    serializer.data[i][key],
                )

    def test_retrieve_flight_detail(self):
        airports = create_airports()
        routes = create_routes(airports)
        airplane = sample_airplane()
        crews = create_crews(4)
        flights_ = create_flights(routes, airplane)
        add_crews_to_flights(crews, flights_)

        flight = Flight.objects.all()[0]

        url = detail_url(flight.id)
        res = self.client.get(url)

        serializer = FlightDetailSerializer(flight)

        self.assertEquals(res.status_code, status.HTTP_200_OK)
        self.assertEquals(res.data, serializer.data)

    def test_create_flight_forbidden(self):
        airports = create_airports()
        routes = create_routes(airports)
        airplane = sample_airplane()
        crews = create_crews(4)

        payload = {
            "route": routes[0].id,
            "airplane": airplane.id,
            "crews": [crew.id for crew in crews],
            "departure_time": "2023-09-15 12:00+03:00",
            "arrival_time": "2023-09-15 15:30+03:00",
        }
        res = self.client.post(FLIGHT_URL, payload)

        self.assertEquals(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_flight_forbidden(self):
        airports = create_airports()
        routes = create_routes(airports)
        airplane = sample_airplane()
        crews = create_crews(4)
        flights_ = create_flights(routes, airplane)
        add_crews_to_flights(crews, flights_)

        flight = Flight.objects.all()[0]

        payload = {
            "departure_time": "2023-09-15 13:45+03:00",
        }

        url = detail_url(flight.id)
        res = self.client.patch(url, payload)

        self.assertEquals(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_flight_forbidden(self):
        airports = create_airports()
        routes = create_routes(airports)
        airplane = sample_airplane()
        crews = create_crews(4)
        flights_ = create_flights(routes, airplane)
        add_crews_to_flights(crews, flights_)

        flight = Flight.objects.all()[0]

        url = detail_url(flight.id)
        res = self.client.delete(url)

        self.assertEquals(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminFlightApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com",
            "test_pass",
            is_staff=True,
        )
        self.client.force_authenticate(self.user)

    def test_create_flight(self):
        airports = create_airports()
        routes = create_routes(airports)
        airplane = sample_airplane()
        crews_ = create_crews(4)

        payload = {
            "route": routes[0].id,
            "airplane": airplane.id,
            "crews": [crew.id for crew in crews_],
            "departure_time": "2023-09-15 12:00+03:00",
            "arrival_time": "2023-09-15 15:30+03:00",
        }
        res = self.client.post(FLIGHT_URL, payload)
        flight = Flight.objects.get(id=res.data["id"])
        crews = flight.crews.all()

        self.assertEquals(res.status_code, status.HTTP_201_CREATED)
        self.assertEquals(routes[0], getattr(flight, "route"))
        self.assertEquals(airplane, getattr(flight, "airplane"))
        self.assertEquals(crews.count(), 4)
