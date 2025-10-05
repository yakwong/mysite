from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AsyncRoutesView,
    DeptInfoViewSet,
    MenuMetaViewSet,
    MenuViewSet,
    RoleViewSet,
)

router = DefaultRouter()
router.register("role", RoleViewSet, basename="role")
router.register("menu", MenuViewSet, basename="menu")
router.register("menumeta", MenuMetaViewSet, basename="menu-meta")
router.register("dept", DeptInfoViewSet, basename="dept-info")

urlpatterns = [
    path("asyncroutes/", AsyncRoutesView.as_view(), name="AsyncRoutesView"),
    path("", include(router.urls)),
]
