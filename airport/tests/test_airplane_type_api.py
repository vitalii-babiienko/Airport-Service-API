from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from airport.models import AirplaneType
from airport.serializers import AirplaneTypeSerializer

AIRPLANE_TYPE_URL = reverse("airport:airplanetype-list")


def sample_airplane_type(**params):
    defaults = {
        "name": "NB",
    }
    defaults.update(params)

    return AirplaneType.objects.create(**defaults)


def detail_url(airplane_type_id):
    return reverse("airport:airplanetype-detail", args=[airplane_type_id])


class UnauthenticatedAirplaneTypeApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(AIRPLANE_TYPE_URL)

        self.assertEquals(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedAirplaneTypeApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "test_pass",
        )
        self.client.force_authenticate(self.user)

    def test_list_airplane_types(self):
        sample_airplane_type()
        sample_airplane_type()

        res = self.client.get(AIRPLANE_TYPE_URL)

        airplane_types = AirplaneType.objects.all()
        serializer = AirplaneTypeSerializer(airplane_types, many=True)

        self.assertEquals(res.status_code, status.HTTP_200_OK)
        self.assertEquals(res.data, serializer.data)

    def test_retrieve_airplane_type_detail(self):
        airplane_type = sample_airplane_type()

        url = detail_url(airplane_type.id)
        res = self.client.get(url)

        serializer = AirplaneTypeSerializer(airplane_type)

        self.assertEquals(res.status_code, status.HTTP_200_OK)
        self.assertEquals(res.data, serializer.data)

    def test_create_airplane_type_forbidden(self):
        payload = {
            "name": "NB",
        }
        res = self.client.post(AIRPLANE_TYPE_URL, payload)

        self.assertEquals(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_airplane_type_forbidden(self):
        airplane_type = sample_airplane_type()

        payload = {
            "name": "NB",
        }

        url = detail_url(airplane_type.id)
        res = self.client.patch(url, payload)

        self.assertEquals(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_airplane_type_forbidden(self):
        airplane_type = sample_airplane_type()

        url = detail_url(airplane_type.id)
        res = self.client.delete(url)

        self.assertEquals(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminAirplaneTypeApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com",
            "test_pass",
            is_staff=True,
        )
        self.client.force_authenticate(self.user)

    def test_create_airplane_type(self):
        payload = {
            "name": "NB",
        }
        res = self.client.post(AIRPLANE_TYPE_URL, payload)
        airplane_type = AirplaneType.objects.get(id=res.data["id"])

        self.assertEquals(res.status_code, status.HTTP_201_CREATED)
        for key in payload:
            self.assertEquals(payload[key], getattr(airplane_type, key))
