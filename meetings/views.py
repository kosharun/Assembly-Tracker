from django.shortcuts import render, get_object_or_404, redirect
from .models import Meeting, AgendaItem, Member, Organization
from .forms import MeetingForm, MemberForm
from django.http import HttpResponse
from django.template.loader import get_template
from django.db.models import Max
from django.views import View
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph
from django.db.models import F, Sum
from datetime import datetime
from .forms import OrganizationRegistrationForm
from django.contrib.auth import authenticate, login, logout
from .forms import LoginForm
from django.contrib.auth.decorators import login_required

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                # Redirect to the dashboard or any other desired page
                return redirect('meetings:homepage')
            else:
                form.add_error(None, 'Invalid username or password')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('meetings:homepage')

def register(request):
    if request.method == 'POST':
        form = OrganizationRegistrationForm(request.POST)
        
        print(request.POST)
        if form.is_valid():
            user = form.save()
            # Create an organization profile for the registered user
            organization = Organization(user=user, name=form.cleaned_data['username'], email=form.cleaned_data['email'])
            organization.save()
            # Redirect to the login page or any other desired page
            return redirect('meetings:login')
    else:
        form = OrganizationRegistrationForm()
    return render(request, 'register.html', {'form': form})

class MeetingPDFView(View):
    def get(self, request, meeting_id):
        # Fetch the meeting object from the database
        meeting = Meeting.objects.get(id=meeting_id)

        # Create a response object with content type 'application/pdf'
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="meeting_{meeting.date}_{meeting.title}.pdf"'

        # Create the PDF document using ReportLab
        doc = SimpleDocTemplate(response, pagesize=letter)
        elements = []

        # Define styles for the paragraphs
        styles = getSampleStyleSheet()
        title_style = styles['Title']
        title_style.alignment = 1  # Center alignment
        date_style = ParagraphStyle('DateStyle', parent=styles['Normal'], spaceBefore=20)
        description_style = ParagraphStyle('DescriptionStyle', parent=styles['Normal'], spaceBefore=20)

        # Add the title to the document
        elements.append(Paragraph(meeting.title, title_style))

        # Add the date, agenda, and description to the document
        elements.append(Paragraph(f"<b>Date</b>: {meeting.date.strftime('%m/%d/%Y')}", date_style))
        elements.append(Paragraph("<br></br><b>Present members:</b>"))
        for present_member in meeting.present_members.all():
            elements.append(Paragraph(f"-{present_member}"))

        for agenda_item in meeting.agenda_items.all():
            if agenda_item.ulaz > 0 or agenda_item.izlaz > 0 or agenda_item.prenos > 0:
                elements.append(Paragraph(f"<b>* Cash register</b> month <b>{agenda_item.mjesec}</b>: {agenda_item.description} <br></br> Month: {agenda_item.mjesec}<br></br> Income: {agenda_item.ulaz}<br></br> Exit: {agenda_item.izlaz}<br></br> Transfer: {agenda_item.prenos}", description_style))
            else:
                elements.append(Paragraph(f"<b>* {agenda_item.agenda_item}</b>: {agenda_item.description} <br></br> ", description_style))
        elements.append(Paragraph("<br></br><b>Signature:</b>"))    
        elements.append(Paragraph("<br></br><b>______________________________</b>"))
        elements.append(Paragraph("<br></br><b>______________________________</b>"))
        elements.append(Paragraph("<br></br><b>______________________________</b>"))

        # Build the document
        doc.build(elements)

        return response


def meeting_delete(request, meeting_id):
    meeting = get_object_or_404(Meeting, id=meeting_id)
    meeting.delete()
    return redirect('meetings:homepage')


def meeting_edit(request, meeting_id):
    organization = request.user.organization
    meeting = get_object_or_404(Meeting, id=meeting_id)
    members = Member.objects.filter(organization=organization)

    if request.method == 'POST':
        form = MeetingForm(request.POST, instance=meeting)
        
        if form.is_valid():
            form.save()

            # Update agenda items
            agenda_items = request.POST.getlist('agenda_item[]')
            descriptions = request.POST.getlist('agenda_description[]')
            mjeseci = request.POST.getlist('agenda_mjesec[]')
            ulazi = request.POST.getlist('agenda_ulaz[]')
            izlazi = request.POST.getlist('agenda_izlaz[]')
            prenosi = request.POST.getlist('agenda_prenos[]')
            # Delete existing agenda items
            meeting.agenda_items.all().delete()
            print(agenda_items)
            # Save updated agenda items
            for i in range(len(mjeseci)):
                agenda_item = AgendaItem(agenda_item=agenda_items[i], mjesec=mjeseci[i], ulaz=ulazi[i], izlaz=izlazi[i], prenos=prenosi[i], meeting=meeting)
                agenda_item.save()

            if len(descriptions) > 0:
                for i in range(len(mjeseci) , len(agenda_items)):
                    agenda_item = AgendaItem(agenda_item=agenda_items[i], description=descriptions[i-len(mjeseci)], meeting=meeting)
                    agenda_item.save()


            return redirect('meetings:meeting_detail', meeting_id=meeting.id)
    else:
        form = MeetingForm(instance=meeting)

    return render(request, 'meeting_edit.html', {'form': form, 'meeting': meeting, 'members': members})

@login_required
def meeting_form(request):
    organization = request.user.organization
    members = Member.objects.filter(organization=organization)  # Retrieve the list of members from the database
    current_month = datetime.now().month
    meetings = Meeting.objects.filter(organization=organization)
    present_members = members.all()
    last_meeting_month = meetings.aggregate(Max('date__month'))['date__month__max']
    if last_meeting_month is None:
        last_meeting_month = 0
    months_to_generate = range(last_meeting_month + 1, current_month + 1)
    if request.method == 'POST':
        form = MeetingForm(request.POST)
        if form.is_valid():
            # Create a new meeting object
            meeting = form.save(commit=False)
            meeting.organization = request.user.organization
            meeting.save()
            selected_members = request.POST.getlist('present_members')

            # Associate the selected members with the meeting
            for member_id in selected_members:
                member = Member.objects.get(id=member_id)
                meeting.present_members.add(member)

            # Save the meeting with the associated present members
            meeting.save()
            # Get the agenda item and description data from the form
            
        
            agenda_items = request.POST.getlist('agenda_item[]')
            descriptions = request.POST.getlist('agenda_description[]')
            mjeseci = request.POST.getlist('agenda_mjesec[]')
            ulazi = request.POST.getlist('agenda_ulaz[]')
            izlazi = request.POST.getlist('agenda_izlaz[]')
            prenosi = request.POST.getlist('agenda_prenos[]')
            agenda_names = request.POST.getlist('agenda_name[]')  # Added agenda_names
            # Delete existing agenda items
            meeting.agenda_items.all().delete()

            # Separate data based on agenda item names and save agenda items
            for i in range(len(mjeseci)):
                agenda_item = AgendaItem(agenda_item=agenda_items[i], mjesec=mjeseci[i], ulaz=ulazi[i], izlaz=izlazi[i], prenos=prenosi[i], meeting=meeting)
                agenda_item.save()

            if len(descriptions) > 0:
                for i in range(len(mjeseci) , len(agenda_items)):
                    agenda_item = AgendaItem(agenda_item=agenda_items[i], description=descriptions[i-len(mjeseci)], meeting=meeting)
                    agenda_item.save()

            # Separate and process data for yearly graphs
            yearly_data = {}
            for agenda_name in agenda_names:
                agenda_data = meeting.agenda_items.filter(agenda_item=agenda_name).values('mjesec').annotate(
                    ulaz_sum=Sum('ulaz'),
                    izlaz_sum=Sum('izlaz'),
                    prenos_sum=Sum('prenos')
                )
                yearly_data[agenda_name] = list(agenda_data)

            # Return JSON response with yearly data
            #return JsonResponse({'yearly_data': yearly_data})
            return redirect("/")
    else:
        form = MeetingForm()

    return render(request, 'meeting_form.html', {'form': form, 'members': members, 'current_month': current_month, 'months_to_generate': months_to_generate, 'organization': organization,})

@login_required
def members_form(request):
    organization = request.user.organization
    members = Member.objects.filter(organization=organization)
    meetings = Meeting.objects.filter(organization=organization)
    members.update(present_times=0)

    for meeting in meetings:
        present_members = meeting.present_members.all()
        present_members.update(present_times=F('present_times') + 1)

    if request.method == 'POST':
        form = MemberForm(request.POST)
        if form.is_valid():
            member = form.save(commit=False)
            member.organization = request.user.organization
            member.save()
    else:
        form = MemberForm()
    return render(request, 'members_form.html', {'form': form, 'members': members, 'meetings': meetings})

def member_delete(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    member.delete()
    return redirect('meetings:members_form')

def mark_member_present(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    member.present_times += 1
    member.save()
    return redirect('meetings:members_form')

@login_required
def member_info(request, member_id):
    organization = request.user.organization
    meetings = Meeting.objects.filter(organization=organization)
    member = get_object_or_404(Member, id=member_id)
    count = meetings.count()
    return render(request, 'member_info.html', {'member': member, 'count': count})


def homepage(request):
    try:
        organization = request.user.organization
        meetings = Meeting.objects.filter(organization=organization)
        return render(request, 'homepage.html', {'meetings': meetings})
    except AttributeError:
        return render(request, 'homepage.html')


def meeting_detail(request, meeting_id):
    meeting = get_object_or_404(Meeting, id=meeting_id)
    present_members = meeting.present_members.all()  # Retrieve the selected present members for the meeting
    return render(request, 'meeting_detail.html', {'meeting': meeting, 'present_members': present_members})

def months_view(request):
    # Get all the meetings from the database
    organization = request.user.organization
    meetings = Meeting.objects.filter(organization=organization)

    # Create a dictionary to store the monthly data
    months_data = {}

    # Iterate over the meetings and extract the monthly data
    for meeting in meetings:
        year = meeting.date.year
        month = meeting.date.month

        # Retrieve all agenda items for the meeting
        agenda_items = AgendaItem.objects.filter(meeting=meeting)
        
        for item in agenda_items:
            agenda_item = item.agenda_item 
            ulaz = item.ulaz
            izlaz = item.izlaz
            prenos = item.prenos
            mjesec = item.mjesec
            # Check if the year exists in the dictionary
            if year not in months_data:
                months_data[year] = []

            # Append the agenda item data to the respective year
            months_data[year].append({'month': month, 'ulaz': ulaz, 'izlaz': izlaz, 'prenos': prenos, 'mjesec': mjesec, 'agenda_item': agenda_item,})       
    # Get the list of years
    years = list(months_data.keys())
    # Pass the years and months_data variables to the template for rendering
    context = {'years': years, 'months_data': months_data}
    return render(request, 'months_cash_register.html', context)


