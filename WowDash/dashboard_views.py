from django.shortcuts import render


def index2(request):
    context = {
        "title": "Dashboard",
        "subTitle": "CRM",
    }
    return render(request, "dashboard/index2.html", context)
