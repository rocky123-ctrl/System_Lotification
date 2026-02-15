from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'permissions'

router = DefaultRouter()
router.register(r'modules', views.ModuleViewSet)
router.register(r'roles', views.RoleViewSet)
router.register(r'permissions', views.ModulePermissionViewSet)
router.register(r'user-roles', views.UserRoleViewSet)
router.register(r'audit-logs', views.AuditLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('user-permissions/<int:user_id>/', views.get_user_permissions, name='user_permissions'),
    path('my-permissions/', views.get_my_permissions, name='my_permissions'),
    path('check-permission/', views.check_permission, name='check_permission'),
]
