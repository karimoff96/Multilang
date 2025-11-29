from django.shortcuts import render
from django.contrib.auth.decorators import login_required


    
def email(request):
    context={
        "title": "Email",
        "subTitle": "Components / Email",
    }
    return render(request,"email.html", context)
    
    

@login_required(login_url='admin_login')
def index(request):
    context={
        "title": "Dashboard",
        "subTitle": "AI",
    }
    return render(request,"index.html", context)
    
def kanban(request):
    context={
        "title": "Kanban",
        "subTitle": "Kanban",
    }
    return render(request,"kanban.html", context)
    
    
    
def stared(request):
    context={
        "title": "Email",
        "subTitle": "Components / Email",
    }
    return render(request,"stared.html", context)
    
def termsAndConditions(request):
    context={
        "title": "Terms & Condition",
        "subTitle": "Terms & Condition",
    }
    return render(request,"termsAndConditions.html", context)
    
    
def viewDetails(request):
    context={
        "title": "Email",
        "subTitle": "Components / Email",
    }
    return render(request,"viewDetails.html", context)
    
def widgets(request):
    context={
        "title": "Widgets",
        "subTitle": "Widgets",
    }
    return render(request,"widgets.html", context)
    