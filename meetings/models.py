from django.db import models
from django.contrib.auth.models import User

class Organization(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    # Add other fields as per your requirements

    def __str__(self):
        return self.name

class Meeting(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    title = models.CharField(max_length=101)
    date = models.DateField()
    present_members = models.ManyToManyField('Member', related_name='meetings')

    def __str__(self):
        return self.title


class AgendaItem(models.Model):
    agenda_item = models.CharField(max_length=100)
    description = models.TextField()
    mjesec = models.PositiveIntegerField(default=1)
    ulaz = models.IntegerField(default=0)
    izlaz = models.IntegerField(default=0)
    prenos = models.IntegerField(default=0)
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='agenda_items', default=None)

    def __str__(self):
        return self.agenda_item


class Member(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    present_times = models.PositiveIntegerField(default=0)
    # Add any other relevant fields for the member

    def __str__(self):
        return self.name


