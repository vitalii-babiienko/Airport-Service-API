import os
import uuid
from math import radians, cos, sin, asin, sqrt

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext as _


def create_custom_image_file_path(instance, filename):
    _, extension = os.path.splitext(filename)

    return os.path.join(
        "uploads",
        f"{instance.__class__.__name__.lower()}s",
        f"{slugify(instance.title)}-{uuid.uuid4()}{extension}"
    )


class AirplaneType(models.Model):
    class TypeName(models.TextChoices):
        NARROW_BODY = "NB", _("Narrow-body airliner")
        WIDE_BODY = "WB", _("Wide-body airliner")
        REGIONAL = "RL", _("Regional aircraft")
        COMMUTER = "CR", _("Commuter aircraft")

    name = models.CharField(
        max_length=2,
        choices=TypeName.choices,
        default=TypeName.NARROW_BODY,
    )

    def __str__(self):
        return self.name


class Airplane(models.Model):
    name = models.CharField(max_length=255)
    rows = models.IntegerField()
    seats_in_row = models.IntegerField()
    airplane_type = models.ForeignKey(
        AirplaneType,
        on_delete=models.CASCADE,
        related_name="airplanes",
    )
    image = models.ImageField(
        null=True,
        blank=True,
        upload_to=create_custom_image_file_path,
    )

    class Meta:
        ordering = ["name"]

    @property
    def capacity(self):
        return self.rows * self.seats_in_row

    def __str__(self):
        return f"{self.name} ({self.airplane_type})"


class Crew(models.Model):
    class CrewPosition(models.TextChoices):
        CAPTAIN = "CPT", _("Captain")
        FIRST_OFFICER = "FO", _("First officer")
        SECOND_OFFICER = "SO", _("Second officer")
        THIRD_OFFICER = "TO", _("Third officer")
        AIRBORNE_SENSOR_OPERATOR = "ASO", _("Airborne sensor operator")
        PURSER = "PRS", _("Purser")
        FLIGHT_ATTENDANT = "FA", _("Flight attendant")
        FLIGHT_MEDIC = "FM", _("Flight medic")
        LOADMASTER = "LM", _("Loadmaster")

    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    position = models.CharField(
        max_length=3,
        choices=CrewPosition.choices,
        default=CrewPosition.FLIGHT_ATTENDANT,
    )
    image = models.ImageField(
        null=True,
        blank=True,
        upload_to=create_custom_image_file_path,
    )

    class Meta:
        ordering = ["position", "last_name"]

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.position})"


def calculate_distance_between_two_coordinates(
    src_lat,
    src_long,
    dst_lat,
    dst_long,
):
    # Convert from degrees to radians
    src_lat = radians(src_lat)
    src_long = radians(src_long)
    dst_lat = radians(dst_lat)
    dst_long = radians(dst_long)

    # Haversine formula
    dlat = dst_lat - src_lat
    dlong = dst_long - src_long

    a = sin(dlat / 2) ** 2 + cos(src_lat) * cos(dst_lat) * sin(dlong / 2) ** 2
    c = 2 * asin(sqrt(a))

    # Earth radius in kilometers. Use 3956 for miles.
    r = 6371

    return f"{round(c * r, 2)} km"


class Airport(models.Model):
    name = models.CharField(max_length=255, unique=True)
    city = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    iata_code = models.CharField(max_length=3, unique=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    image = models.ImageField(
        null=True,
        blank=True,
        upload_to=create_custom_image_file_path,
    )

    class Meta:
        ordering = ["country", "name"]

    def __str__(self):
        return f"{self.iata_code} {self.name}"


class Route(models.Model):
    source = models.ForeignKey(
        Airport,
        on_delete=models.CASCADE,
        related_name="source",
    )
    destination = models.ForeignKey(
        Airport,
        on_delete=models.CASCADE,
        related_name="destination",
    )

    @property
    def distance(self):
        return calculate_distance_between_two_coordinates(
            self.source.latitude,
            self.source.longitude,
            self.destination.latitude,
            self.destination.longitude,
        )

    def __str__(self):
        return f"{self.source} - {self.destination}"


class Flight(models.Model):
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name="flights",
    )
    airplane = models.ForeignKey(
        Airplane,
        on_delete=models.CASCADE,
        related_name="flights",
    )
    crews = models.ManyToManyField(
        Crew,
        related_name="flights",
    )
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()

    class Meta:
        ordering = ["-departure_time"]

    def __str__(self):
        return f"{str(self.departure_time)} {self.route}"


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return str(self.created_at)


class Ticket(models.Model):
    row = models.IntegerField()
    seat = models.IntegerField()
    flight = models.ForeignKey(
        Flight,
        on_delete=models.CASCADE,
        related_name="tickets",
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="tickets",
    )

    class Meta:
        unique_together = ("flight", "row", "seat")
        ordering = ["row", "seat"]

    def __str__(self):
        return (
            f"{self.flight} (row: {self.row}, seat: {self.seat})"
        )

    @staticmethod
    def validate_ticket(row, seat, airplane, error_to_raise):
        for ticket_attr_value, ticket_attr_name, airplane_attr_name in [
            (row, "row", "rows"),
            (seat, "seat", "seats_in_row"),
        ]:
            count_attrs = getattr(airplane, airplane_attr_name)

            if not (1 <= ticket_attr_value <= count_attrs):
                raise error_to_raise(
                    {
                        ticket_attr_name: f"The {ticket_attr_name} "
                        f"number cannot be {ticket_attr_value}! "
                        f"It must be in range [1, {count_attrs}]."
                    }
                )

    def clean(self):
        Ticket.validate_ticket(
            self.row,
            self.seat,
            self.flight.airplane,
            ValidationError,
        )

    def save(
        self,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    ):
        self.full_clean()
        return super(Ticket, self).save(
            force_insert,
            force_update,
            using,
            update_fields,
        )
