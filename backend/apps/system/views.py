from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from utils.response import CustomResponse
from utils.viewset import CustomModelViewSet

from .filters import DeptFilter, MenuFilter, RoleFilter
from .models import DeptInfo, Menu, MenuMeta, Role
from .serializers import (
    DeptInfoSerializer,
    MenuMetaSerializer,
    MenuSerializer,
    RoleSerializer,
    RouteSerializer,
)


class RoleViewSet(CustomModelViewSet):
    """角色表视图集"""

    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = RoleFilter


class MenuViewSet(CustomModelViewSet):
    """菜单/权限视图集"""

    queryset = Menu.objects.all().order_by("meta__rank")
    serializer_class = MenuSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = MenuFilter


class MenuMetaViewSet(CustomModelViewSet):
    """菜单meta视图集"""

    queryset = MenuMeta.objects.all()
    serializer_class = MenuMetaSerializer


class DeptInfoViewSet(CustomModelViewSet):
    """部门信息视图集"""

    queryset = DeptInfo.objects.all()
    serializer_class = DeptInfoSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = DeptFilter


class AsyncRoutesView(APIView):
    """动态路由视图"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        roles = user.role.all()
        menus = (
            Menu.objects.filter(role__in=roles, menu_type=Menu.MenuChoices.MENU, status=True)
            .distinct()
            .order_by("meta__rank")
        )
        permissions = Menu.objects.filter(
            role__in=roles,
            menu_type=Menu.MenuChoices.PERMISSION,
            status=True,
        ).distinct()
        permission_dict: dict[str, list[str]] = {}
        for perm in permissions:
            parent_id = perm.parent_id
            permission_dict.setdefault(parent_id, []).append(perm.code)

        serializer = RouteSerializer(menus, many=True, context={"permission_dict": permission_dict})
        return CustomResponse(success=True, data=serializer.data, msg="成功获取动态路由")
