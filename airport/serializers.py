from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from airport.models import (
    AirplaneType,
    Airplane,
    Crew,
    Airport,
    Route,
    Flight,
    Order,
    Ticket,
)


class AirplaneTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirplaneType
        fields = ("id", "name")


class AirplaneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airplane
        fields = (
            "id",
            "name",
            "rows",
            "seats_in_row",
            "airplane_type",
        )


class AirplaneListSerializer(AirplaneSerializer):
    airplane_type = serializers.SlugRelatedField(
        many=False,
        read_only=True,
        slug_field="name",
    )


class AirplaneDetailSerializer(serializers.ModelSerializer):
    airplane_type = serializers.SlugRelatedField(
        many=False,
        read_only=True,
        slug_field="name",
    )

    class Meta:
        model = Airplane
        fields = (
            "id",
            "name",
            "capacity",
            "rows",
            "seats_in_row",
            "airplane_type",
        )


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = (
            "id",
            "first_name",
            "last_name",
            "position",
        )


class AirportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = (
            "id",
            "name",
            "city",
            "country",
            "iata_code",
            "latitude",
            "longitude",
        )


class AirportListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = (
            "id",
            "name",
            "city",
            "country",
            "iata_code",
        )


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = (
            "id",
            "source",
            "destination",
        )


class RouteListSerializer(RouteSerializer):
    source = AirportListSerializer(
        many=False,
        read_only=True,
    )
    destination = AirportListSerializer(
        many=False,
        read_only=True,
    )


class RouteDetailSerializer(serializers.ModelSerializer):
    source = AirportSerializer(
        many=False,
        read_only=True,
    )
    destination = AirportSerializer(
        many=False,
        read_only=True,
    )

    class Meta:
        model = Route
        fields = (
            "id",
            "source",
            "destination",
            "distance",
        )


class TicketSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        data = super(TicketSerializer, self).validate(attrs=attrs)
        Ticket.validate_ticket(
            attrs["row"],
            attrs["seat"],
            attrs["flight"].airplane,
            ValidationError
        )
        return data

    class Meta:
        model = Ticket
        fields = (
            "id",
            "row",
            "seat",
            "flight",
        )


class TicketSeatSerializer(TicketSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat")


class FlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flight
        fields = (
            "id",
            "route",
            "airplane",
            "crews",
            "departure_time",
            "arrival_time",
        )


class FlightListSerializer(serializers.ModelSerializer):
    route = serializers.StringRelatedField(many=False)
    airplane_name = serializers.CharField(
        source="airplane.name",
        read_only=True,
    )
    airplane_capacity = serializers.IntegerField(
        source="airplane.capacity",
        read_only=True,
    )
    crews = serializers.StringRelatedField(many=True)
    tickets_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = Flight
        fields = (
            "id",
            "route",
            "airplane_name",
            "airplane_capacity",
            "tickets_available",
            "crews",
            "departure_time",
            "arrival_time",
        )


class FlightDetailSerializer(FlightSerializer):
    route = RouteDetailSerializer(
        many=False,
        read_only=True,
    )
    airplane = AirplaneDetailSerializer(
        many=False,
        read_only=True,
    )
    crews = CrewSerializer(
        many=True,
        read_only=True,
    )
    taken_seats = TicketSeatSerializer(
        source="tickets",
        many=True,
        read_only=True,
    )

    class Meta:
        model = Flight
        fields = (
            "id",
            "route",
            "airplane",
            "crews",
            "departure_time",
            "arrival_time",
            "taken_seats",
        )


class TicketListSerializer(TicketSerializer):
    flight = FlightListSerializer(
        many=False,
        read_only=True,
    )


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(
        many=True,
        read_only=False,
        allow_empty=False,
    )

    class Meta:
        model = Order
        fields = (
            "id",
            "tickets",
            "created_at",
        )

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            for ticket_data in tickets_data:
                Ticket.objects.create(order=order, **ticket_data)
            return order


class OrderListSerializer(OrderSerializer):
    tickets = TicketListSerializer(
        many=True,
        read_only=True,
    )
