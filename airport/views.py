from django.db.models import F, Count
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from airport.permissions import IsAdminOrIfAuthenticatedReadOnly
from airport.models import (
    AirplaneType,
    Airplane,
    Crew,
    Airport,
    Route,
    Flight,
    Order,
)
from airport.pagination import (
    AirplanePagination,
    CrewPagination,
    AirportPagination,
    OrderPagination,
    RoutePagination,
    FlightPagination,
)
from airport.serializers import (
    AirplaneTypeSerializer,
    AirplaneSerializer,
    AirplaneListSerializer,
    AirplaneDetailSerializer,
    AirplaneImageSerializer,
    CrewSerializer,
    CrewListSerializer,
    CrewDetailSerializer,
    CrewImageSerializer,
    AirportSerializer,
    AirportListSerializer,
    AirportDetailSerializer,
    AirportImageSerializer,
    RouteSerializer,
    RouteListSerializer,
    RouteDetailSerializer,
    FlightSerializer,
    FlightListSerializer,
    FlightDetailSerializer,
    OrderSerializer,
    OrderListSerializer,
)


class UploadImageMixin:
    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
        permission_classes=[IsAdminUser],
    )
    def upload_image(self, request, pk=None):
        """Endpoint for uploading the image to the specific instance"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(tags=["AirplaneTypes"])
class AirplaneTypeViewSet(viewsets.ModelViewSet):
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)


@extend_schema(tags=["Airplanes"])
class AirplaneViewSet(UploadImageMixin, viewsets.ModelViewSet):
    queryset = Airplane.objects.select_related("airplane_type")
    serializer_class = AirplaneSerializer
    pagination_class = AirplanePagination
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ("airplane_type",)

    def get_serializer_class(self):
        if self.action == "list":
            return AirplaneListSerializer

        if self.action == "retrieve":
            return AirplaneDetailSerializer

        if self.action == "upload_image":
            return AirplaneImageSerializer

        return AirplaneSerializer


@extend_schema(tags=["Crews"])
class CrewViewSet(UploadImageMixin, viewsets.ModelViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer
    pagination_class = CrewPagination
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ("position",)

    def get_serializer_class(self):
        if self.action == "list":
            return CrewListSerializer

        if self.action == "retrieve":
            return CrewDetailSerializer

        if self.action == "upload_image":
            return CrewImageSerializer

        return CrewSerializer


@extend_schema(tags=["Airports"])
class AirportViewSet(UploadImageMixin, viewsets.ModelViewSet):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer
    pagination_class = AirportPagination
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ("city", "country")

    def get_serializer_class(self):
        if self.action == "list":
            return AirportListSerializer

        if self.action == "retrieve":
            return AirportDetailSerializer

        if self.action == "upload_image":
            return AirportImageSerializer

        return AirportSerializer


@extend_schema(tags=["Routes"])
class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.select_related("source", "destination")
    serializer_class = RouteSerializer
    pagination_class = RoutePagination
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ("source", "destination")

    def get_serializer_class(self):
        if self.action == "list":
            return RouteListSerializer

        if self.action == "retrieve":
            return RouteDetailSerializer

        return RouteSerializer


@extend_schema(tags=["Flights"])
class FlightViewSet(viewsets.ModelViewSet):
    queryset = (
        Flight.objects
        .select_related(
            "route__source",
            "route__destination",
            "airplane__airplane_type",
        )
        .prefetch_related("crews")
        .annotate(
            tickets_available=(
                F("airplane__rows") * F("airplane__seats_in_row")
                - Count("tickets")
            )
        )
    )
    serializer_class = FlightSerializer
    pagination_class = FlightPagination
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ("route", "departure_time", "arrival_time")

    def get_serializer_class(self):
        if self.action == "list":
            return FlightListSerializer

        if self.action == "retrieve":
            return FlightDetailSerializer

        return FlightSerializer


@extend_schema(tags=["Orders"])
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related(
        "tickets__flight__airplane",
        "tickets__flight__crews",
        "tickets__flight__route",
    )
    serializer_class = OrderSerializer
    pagination_class = OrderPagination
    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ("created_at",)

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer

        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
