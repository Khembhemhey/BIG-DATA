from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('clean_data/', views.clean_data, name='clean_data'),
    path('stats/', views.statistics, name='statistics'),
    path('insights/', views.insights, name='insights'),
    path('top/', views.top, name='top'),
    path('visual/', views.visualize, name='visual'),
    path('about/', views.about, name='about'),
    
    
]
