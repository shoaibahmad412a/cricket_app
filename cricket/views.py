from django.shortcuts import redirect, render, get_object_or_404
from .models import Team,Players
from .forms import TeamForms,PlayersForms
from django.core.paginator import Paginator

def team_list (request):
    teams=Team.objects.all()
    context ={
        'teams':teams,
    }
    status_code=200
    return render (request,'cricket/team_list.html', context)


def add_team(request):
    if request.method=='POST':
        form=TeamForms(request.POST)
        if form.is_valid():
            form.save()
            return redirect('team_list')
    else:
        form=TeamForms()    
    return render(request,'cricket/add_team.html',{'form':form})


def add_player (request,team_id):
    team = get_object_or_404(Team, id=team_id)
    if request.method=='POST':
        form=PlayersForms(request.POST)
        if form.is_valid():
            player=form.save(commit=False)
            player.team= team
            player.save()
            return redirect('team_list')
    else:
        form =PlayersForms()
    return render(request,'cricket/add_player.html',{'form':form,'team':team})


def match_list(request):
    teams = Team.objects.all()[:2]  # Fetch the first two teams
    
    # For pagination (if needed for larger lists):
    paginator = Paginator(teams, 2)  # Show 2 teams per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'cricket/match_list.html', context)