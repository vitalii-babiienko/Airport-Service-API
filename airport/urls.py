from rest_framework import routers

from airport.views import (
    AirplaneTypeViewSet,
    AirplaneViewSet,
    CrewViewSet,
    AirportViewSet,
    RouteViewSet,
    FlightViewSet,
    OrderViewSet,
)

router = routers.DefaultRouter()
router.register("airplane_types", AirplaneTypeViewSet)
router.register("airplanes", AirplaneViewSet)
router.register("crews", CrewViewSet)
router.register("airports", AirportViewSet)
router.register("routes", RouteViewSet)
router.register("flights", FlightViewSet)
router.register("orders", OrderViewSet)

urlpatterns = router.urls

app_name = "airport"
