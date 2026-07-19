from rest_framework.permissions import BasePermission, SAFE_METHODS


def user_has_role(user, roles):
    return user.is_superuser or user.groups.filter(name__in=roles).exists()


class RoleBasedWritePermission(BasePermission):
    write_roles = []

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return user_has_role(request.user, self.write_roles)


class MasterDataPermission(RoleBasedWritePermission):
    write_roles = ["Admin", "Manager", "Inventory"]


class InventoryPermission(RoleBasedWritePermission):
    write_roles = ["Admin", "Manager", "Inventory"]


class PosPermission(RoleBasedWritePermission):
    write_roles = ["Admin", "Manager", "Cashier"]


class PromotionPermission(RoleBasedWritePermission):
    write_roles = ["Admin", "Manager"]


class AdminOnlyPermission(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (request.user.is_superuser or request.user.groups.filter(name="Admin").exists()))
