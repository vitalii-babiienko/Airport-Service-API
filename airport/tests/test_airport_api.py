from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from airport.models import Airport
from airport.serializers import (
    AirportListSerializer,
    AirportDetailSerializer,
)

AIRPORT_URL = reverse("airport:airport-list")


def sample_airport(**params):
    defaults = {
        "city": "Test City",
        "country": "Test Country",
        "latitude": 1.1,
        "longitude": 2.2,
    }
    defaults.update(params)

    return Airport.objects.create(**defaults)


def detail_url(airport_id):
    return reverse("airport:airport-detail", args=[airport_id])


class UnauthenticatedAirportApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(AIRPORT_URL)

        self.assertEquals(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedAirportApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "test_pass",
        )
        self.client.force_authenticate(self.user)

    def test_list_airports(self):
        sample_airport(
            name="Test Name A",
            iata_code="AAA",
        )
        sample_airport(
            name="Test Name B",
            iata_code="BBB",
        )

        res = self.client.get(AIRPORT_URL)

        airports = Airport.objects.all()
        serializer = AirportListSerializer(airports, many=True)

        self.assertEquals(res.status_code, status.HTTP_200_OK)
        self.assertEquals(res.data["results"], serializer.data)

    def test_filter_airports_by_city(self):
        airport1 = sample_airport(
            name="Test Name A",
            iata_code="AAA",
        )
        airport2 = sample_airport(
            name="Test Name B",
            iata_code="BBB",
        )
        airport3 = sample_airport(
            name="Test Name C",
            iata_code="CCC",
            city="Test City C",
        )

        res = self.client.get(
            AIRPORT_URL,
            {"city": "Test City"}
        )

        serializer1 = AirportListSerializer(airport1)
        serializer2 = AirportListSerializer(airport2)
        serializer3 = AirportListSerializer(airport3)

        self.assertIn(serializer1.data, res.data["results"])
        self.assertIn(serializer2.data, res.data["results"])
        self.assertNotIn(serializer3.data, res.data["results"])

    def test_filter_airports_by_country(self):
        airport1 = sample_airport(
            name="Test Name A",
            iata_code="AAA",
        )
        airport2 = sample_airport(
            name="Test Name B",
            iata_code="BBB",
        )
        airport3 = sample_airport(
            name="Test Name C",
            iata_code="CCC",
            country="Test Country C",
        )

        res = self.client.get(
            AIRPORT_URL,
            {"country": "Test Country"}
        )

        serializer1 = AirportListSerializer(airport1)
        serializer2 = AirportListSerializer(airport2)
        serializer3 = AirportListSerializer(airport3)

        self.assertIn(serializer1.data, res.data["results"])
        self.assertIn(serializer2.data, res.data["results"])
        self.assertNotIn(serializer3.data, res.data["results"])

    def test_retrieve_airport_detail(self):
        airport = sample_airport(
            name="Test Name A",
            iata_code="AAA",
        )

        url = detail_url(airport.id)
        res = self.client.get(url)

        serializer = AirportDetailSerializer(airport)

        self.assertEquals(res.status_code, status.HTTP_200_OK)
        self.assertEquals(res.data, serializer.data)

    def test_create_airport_forbidden(self):
        payload = {
            "name": "Test Name",
            "city": "Test City",
            "country": "Test Country",
            "iata_code": "AAA",
            "latitude": 1.1,
            "longitude": 2.2,
        }
        res = self.client.post(AIRPORT_URL, payload)

        self.assertEquals(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_airport_forbidden(self):
        airport = sample_airport(
            name="Test Name A",
            iata_code="AAA",
        )

        payload = {
            "name": "Updated Name",
        }

        url = detail_url(airport.id)
        res = self.client.patch(url, payload)

        self.assertEquals(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_airport_forbidden(self):
        airport = sample_airport(
            name="Test Name A",
            iata_code="AAA",
        )

        url = detail_url(airport.id)
        res = self.client.delete(url)

        self.assertEquals(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminAirportApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com",
            "test_pass",
            is_staff=True,
        )
        self.client.force_authenticate(self.user)

    def test_create_airport(self):
        payload = {
            "name": "Test Name",
            "city": "Test City",
            "country": "Test Country",
            "iata_code": "AAA",
            "latitude": 1.1,
            "longitude": 2.2,
        }
        res = self.client.post(AIRPORT_URL, payload)
        airport = Airport.objects.get(id=res.data["id"])

        self.assertEquals(res.status_code, status.HTTP_201_CREATED)
        for key in payload:
            self.assertEquals(payload[key], getattr(airport, key))
