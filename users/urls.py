from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # URLs para gestión de usuarios
    path('', views.UserListView.as_view(), name='user_list'),
    path('<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('create/', views.UserCreateView.as_view(), name='user_create'),
    path('<int:pk>/update/', views.UserUpdateView.as_view(), name='user_update'),
    path('<int:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),
    
    # URLs para actividades y sesiones
    path('activities/', views.UserActivityListView.as_view(), name='user_activities'),
    path('sessions/', views.UserSessionListView.as_view(), name='user_sessions'),
    path('statistics/<int:user_id>/', views.get_user_statistics, name='user_statistics'),
    path('log-activity/', views.log_user_activity, name='log_activity'),
    path('online/', views.get_online_users, name='online_users'),
]
