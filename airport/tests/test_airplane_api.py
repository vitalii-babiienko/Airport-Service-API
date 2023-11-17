from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from airport.models import Airplane, AirplaneType
from airport.serializers import (
    AirplaneListSerializer,
    AirplaneDetailSerializer,
)

AIRPLANE_URL = reverse("airport:airplane-list")


def sample_airplane(**params):
    airplane_type = AirplaneType.objects.create(
        name="NB",
    )

    defaults = {
        "name": "Sample Airplane",
        "rows": 10,
        "seats_in_row": 5,
        "airplane_type": airplane_type,
    }
    defaults.update(params)

    return Airplane.objects.create(**defaults)


def detail_url(airplane_id):
    return reverse("airport:airplane-detail", args=[airplane_id])


class UnauthenticatedAirplaneApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(AIRPLANE_URL)

        self.assertEquals(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedAirplaneApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "test_pass",
        )
        self.client.force_authenticate(self.user)

    def test_list_airplanes(self):
        sample_airplane()
        sample_airplane()

        res = self.client.get(AIRPLANE_URL)

        airplanes = Airplane.objects.all()
        serializer = AirplaneListSerializer(airplanes, many=True)

        self.assertEquals(res.status_code, status.HTTP_200_OK)
        self.assertEquals(res.data["results"], serializer.data)

    def test_filter_airplanes_by_airplane_types(self):
        airplane_type_cr = AirplaneType.objects.create(name="CR")

        airplane1 = sample_airplane(
            name="Airplane 1",
            airplane_type=airplane_type_cr,
        )
        airplane2 = sample_airplane(
            name="Airplane 2",
            airplane_type=airplane_type_cr,
        )

        airplane3 = sample_airplane(name="Airplane 3")

        res = self.client.get(
            AIRPLANE_URL,
            {"airplane_type": f"{airplane_type_cr.id}"}
        )

        serializer1 = AirplaneListSerializer(airplane1)
        serializer2 = AirplaneListSerializer(airplane2)
        serializer3 = AirplaneListSerializer(airplane3)

        self.assertIn(serializer1.data, res.data["results"])
        self.assertIn(serializer2.data, res.data["results"])
        self.assertNotIn(serializer3.data, res.data["results"])

    def test_retrieve_airplane_detail(self):
        airplane = sample_airplane()

        url = detail_url(airplane.id)
        res = self.client.get(url)

        serializer = AirplaneDetailSerializer(airplane)

        self.assertEquals(res.status_code, status.HTTP_200_OK)
        self.assertEquals(res.data, serializer.data)

    def test_create_airplane_forbidden(self):
        airplane_type = AirplaneType.objects.create(
            name="NB",
        )

        payload = {
            "name": "Airplane",
            "rows": 10,
            "seats_in_row": 5,
            "airplane_type": airplane_type.id,
        }
        res = self.client.post(AIRPLANE_URL, payload)

        self.assertEquals(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_airplane_forbidden(self):
        airplane = sample_airplane()

        payload = {
            "name": "Updated Name",
        }

        url = detail_url(airplane.id)
        res = self.client.patch(url, payload)

        self.assertEquals(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_airplane_forbidden(self):
        airplane = sample_airplane()

        url = detail_url(airplane.id)
        res = self.client.delete(url)

        self.assertEquals(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminAirplaneApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com",
            "test_pass",
            is_staff=True,
        )
        self.client.force_authenticate(self.user)

    def test_create_airplane(self):
        airplane_type = AirplaneType.objects.create(
            name="NB",
        )

        payload = {
            "name": "Airplane",
            "rows": 10,
            "seats_in_row": 5,
            "airplane_type": airplane_type.id,
        }
        res = self.client.post(AIRPLANE_URL, payload)
        airplane = Airplane.objects.get(id=res.data["id"])

        self.assertEquals(res.status_code, status.HTTP_201_CREATED)
        for key in payload:
            if key != "airplane_type":
                self.assertEquals(payload[key], getattr(airplane, key))
            else:
                self.assertEquals(airplane_type, getattr(airplane, key))
