from django.contrib import admin

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


class TicketInline(admin.TabularInline):
    model = Ticket
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user")
    inlines = (TicketInline,)


@admin.register(AirplaneType)
class AirplaneTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Airplane)
class AirplaneAdmin(admin.ModelAdmin):
    list_display = ("name", "rows", "seats_in_row", "airplane_type")


@admin.register(Crew)
class CrewAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "position")


@admin.register(Airport)
class AirportAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "country", "iata_code")


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ("source", "destination")


@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = ("route", "airplane", "departure_time", "arrival_time")


admin.site.register(Ticket)
