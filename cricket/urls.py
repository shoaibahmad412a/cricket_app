from django.urls import path
from . import views


urlpatterns=[
    #1
    path('teams/', views.team_list, name='team_list'),
    #2
    path('teams/add/', views.add_team, name='add_team'),
    #3
    path('teams/<int:team_id>/add_player/', views.add_player, name='add_player'),
    #4
    path('matchlist', views.match_list, name='match_list')

]