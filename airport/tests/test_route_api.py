from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from airport.models import Airport, Route
from airport.serializers import (
    RouteListSerializer,
    RouteDetailSerializer,
)

ROUTE_URL = reverse("airport:route-list")


def sample_airport(**params):
    defaults = {
        "city": "Test City",
        "country": "Test Country",
        "latitude": 1.1,
        "longitude": 2.2,
    }
    defaults.update(params)

    return Airport.objects.create(**defaults)


def sample_route(**params):
    source = sample_airport(
        name="Test Name A",
        iata_code="AAA",
    )
    destination = sample_airport(
        name="Test Name B",
        iata_code="BBB",
    )
    defaults = {
        "source": source,
        "destination": destination,
    }
    defaults.update(params)

    return Route.objects.create(**defaults)


def detail_url(route_id):
    return reverse("airport:route-detail", args=[route_id])


class UnauthenticatedRouteApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(ROUTE_URL)

        self.assertEquals(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedRouteApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "test_pass",
        )
        self.client.force_authenticate(self.user)

    def test_list_routes(self):
        sample_route()

        res = self.client.get(ROUTE_URL)

        routes = Route.objects.all()
        serializer = RouteListSerializer(routes, many=True)

        self.assertEquals(res.status_code, status.HTTP_200_OK)
        self.assertEquals(res.data["results"], serializer.data)

    def test_retrieve_route_detail(self):
        route = sample_route()

        url = detail_url(route.id)
        res = self.client.get(url)

        serializer = RouteDetailSerializer(route)

        self.assertEquals(res.status_code, status.HTTP_200_OK)
        self.assertEquals(res.data, serializer.data)

    def test_create_route_forbidden(self):
        source = sample_airport(
            name="Test Name A",
            iata_code="AAA",
        )
        destination = sample_airport(
            name="Test Name B",
            iata_code="BBB",
        )
        payload = {
            "source": source.id,
            "destination": destination.id,
        }
        res = self.client.post(ROUTE_URL, payload)

        self.assertEquals(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_route_forbidden(self):
        route = sample_route()
        source = sample_airport(
            name="Test Name C",
            iata_code="CCC",
        )
        payload = {
            "source": source,
        }

        url = detail_url(route.id)
        res = self.client.patch(url, payload)

        self.assertEquals(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_route_forbidden(self):
        route = sample_route()

        url = detail_url(route.id)
        res = self.client.delete(url)

        self.assertEquals(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminRouteApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com",
            "test_pass",
            is_staff=True,
        )
        self.client.force_authenticate(self.user)

    def test_create_route(self):
        source = sample_airport(
            name="Test Name A",
            iata_code="AAA",
        )
        destination = sample_airport(
            name="Test Name B",
            iata_code="BBB",
        )
        payload = {
            "source": source.id,
            "destination": destination.id,
        }
        res = self.client.post(ROUTE_URL, payload)
        route = Route.objects.get(id=res.data["id"])

        self.assertEquals(res.status_code, status.HTTP_201_CREATED)
        self.assertEquals(source, getattr(route, "source"))
        self.assertEquals(destination, getattr(route, "destination"))
