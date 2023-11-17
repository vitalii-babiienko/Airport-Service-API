from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from airport.models import Crew
from airport.serializers import (
    CrewListSerializer,
    CrewDetailSerializer,
)

CREW_URL = reverse("airport:crew-list")


def sample_crew(**params):
    defaults = {
        "first_name": "Test First Name",
        "last_name": "Test Last Name",
        "position": "FA",
    }
    defaults.update(params)

    return Crew.objects.create(**defaults)


def detail_url(crew_id):
    return reverse("airport:crew-detail", args=[crew_id])


class UnauthenticatedCrewApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(CREW_URL)

        self.assertEquals(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedCrewApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "test_pass",
        )
        self.client.force_authenticate(self.user)

    def test_list_crews(self):
        sample_crew()
        sample_crew()

        res = self.client.get(CREW_URL)

        crews = Crew.objects.all()
        serializer = CrewListSerializer(crews, many=True)

        self.assertEquals(res.status_code, status.HTTP_200_OK)
        self.assertEquals(res.data["results"], serializer.data)

    def test_filter_crew_by_position(self):
        crew1 = sample_crew()
        crew2 = sample_crew()
        crew3 = sample_crew(position="CPT")

        res = self.client.get(
            CREW_URL,
            {"position": "FA"}
        )

        serializer1 = CrewListSerializer(crew1)
        serializer2 = CrewListSerializer(crew2)
        serializer3 = CrewListSerializer(crew3)

        self.assertIn(serializer1.data, res.data["results"])
        self.assertIn(serializer2.data, res.data["results"])
        self.assertNotIn(serializer3.data, res.data["results"])

    def test_retrieve_crew_detail(self):
        crew = sample_crew()

        url = detail_url(crew.id)
        res = self.client.get(url)

        serializer = CrewDetailSerializer(crew)

        self.assertEquals(res.status_code, status.HTTP_200_OK)
        self.assertEquals(res.data, serializer.data)

    def test_create_crew_forbidden(self):
        payload = {
            "first_name": "Test First Name",
            "last_name": "Test Last Name",
            "position": "FA",
        }
        res = self.client.post(CREW_URL, payload)

        self.assertEquals(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_crew_forbidden(self):
        crew = sample_crew()

        payload = {
            "first_name": "Updated First Name",
        }

        url = detail_url(crew.id)
        res = self.client.patch(url, payload)

        self.assertEquals(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_crew_forbidden(self):
        crew = sample_crew()

        url = detail_url(crew.id)
        res = self.client.delete(url)

        self.assertEquals(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminCrewApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com",
            "test_pass",
            is_staff=True,
        )
        self.client.force_authenticate(self.user)

    def test_create_crew(self):
        payload = {
            "first_name": "Test First Name",
            "last_name": "Test Last Name",
            "position": "FA",
        }
        res = self.client.post(CREW_URL, payload)
        crew = Crew.objects.get(id=res.data["id"])

        self.assertEquals(res.status_code, status.HTTP_201_CREATED)
        for key in payload:
            self.assertEquals(payload[key], getattr(crew, key))
