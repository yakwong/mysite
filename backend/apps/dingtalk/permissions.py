from rest_framework.permissions import BasePermission


class CanManageDingTalk(BasePermission):
    message = "无权限执行钉钉管理操作"

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff


class CanViewDingTalk(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
