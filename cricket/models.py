from django.db import models
from django.forms import ValidationError

class Team (models.Model):
    name=models.TextField(max_length=100)
    city=models.TextField(max_length=100)


    def __str__(self) :
        return self.name

class Players (models.Model):

    ROLE_CHOICES =[
       
       ('Batsman','Batsman'),
       ('Bowler', 'Bowler'),
       ('All-Rounder', 'All-Rounder'),
       ('Wicket-Keeper', 'Wicket-Keeper'),
       ('Impact-Player','Impact-Player')
    ]


    name= models.TextField(max_length=20)
    age=models.PositiveBigIntegerField()
    experience=models.PositiveIntegerField()
    role=models.CharField(max_length=20,choices=ROLE_CHOICES)
    shirt_no=models.PositiveBigIntegerField()
    team=models.ForeignKey(Team,related_name='players',on_delete=models.CASCADE)


    def __str__(self):
        return f"{self.name}({self.role})"
    
   # def save(self,*args,**kwargs):
      #  if Players.objects.filter(team=self.team, shirt_number=21).exists:
       #     raise ValidationError("Shirt number must be unique within the team.")
     #   super().save(*args, **kwargs)

