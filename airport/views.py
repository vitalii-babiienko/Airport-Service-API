from django.db.models import F, Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets


from airport.models import (
    AirplaneType,
    Airplane,
    Crew,
    Airport,
    Route,
    Flight,
    Order,
)
from airport.serializers import (
    AirplaneTypeSerializer,
    AirplaneSerializer,
    AirplaneListSerializer,
    AirplaneDetailSerializer,
    CrewSerializer,
    AirportSerializer,
    AirportListSerializer,
    RouteSerializer,
    RouteListSerializer,
    RouteDetailSerializer,
    FlightSerializer,
    FlightListSerializer,
    FlightDetailSerializer,
    OrderSerializer,
    OrderListSerializer,
)


class AirplaneTypeViewSet(viewsets.ModelViewSet):
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer


class AirplaneViewSet(viewsets.ModelViewSet):
    queryset = Airplane.objects.select_related("airplane_type")
    serializer_class = AirplaneSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ("airplane_type",)

    def get_serializer_class(self):
        if self.action == "list":
            return AirplaneListSerializer

        if self.action == "retrieve":
            return AirplaneDetailSerializer

        return AirplaneSerializer


class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ("position",)


class AirportViewSet(viewsets.ModelViewSet):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ("city", "country")

    def get_serializer_class(self):
        if self.action == "list":
            return AirportListSerializer

        return AirportSerializer


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.select_related("source", "destination")
    serializer_class = RouteSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ("source", "destination")

    def get_serializer_class(self):
        if self.action == "list":
            return RouteListSerializer

        if self.action == "retrieve":
            return RouteDetailSerializer

        return RouteSerializer


class FlightViewSet(viewsets.ModelViewSet):
    queryset = (
        Flight.objects
        .select_related("route", "airplane")
        .prefetch_related("crews")
        .annotate(
            tickets_available=(
                F("airplane__rows") * F("airplane__seats_in_row")
                - Count("tickets")
            )
        )
    )
    serializer_class = FlightSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ("route", "departure_time", "arrival_time")

    def get_serializer_class(self):
        if self.action == "list":
            return FlightListSerializer

        if self.action == "retrieve":
            return FlightDetailSerializer

        return FlightSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
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
