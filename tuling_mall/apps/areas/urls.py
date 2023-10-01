
from django.contrib import admin
from django.urls import path
from areas import views

urlpatterns = [
    path('areas/', views.AreaView.as_view()),
    path('areas/<int:area_id>/', views.SubAreaView.as_view()),
    path('addresses/create/', views.CreateAddressView.as_view()),
    path('addresses/', views.ShowAddressView.as_view()),
    path('addresses/<int:area_id>/', views.UpdateDestroyAddressView.as_view()),
    path('addresses/<int:address_id>/default/', views.DefaultAddressView.as_view()),
    path('addresses/<int:address_id>/title/', views.UpdateTitleAddressView.as_view()),

]
