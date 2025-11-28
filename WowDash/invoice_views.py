from django.shortcuts import render

def index(request):
    context={
        "title": "Invoice List",
        "subTitle": "Invoice List",
    }
    return render(request, "home/index.html", context)


def addNew(request):
    context={
        "title": "Invoice List",
        "subTitle": "Invoice List",
    }
    return render(request, "invoice/addNew.html", context)
    
def edit(request):
    context={
        "title": "Invoice List",
        "subTitle": "Invoice List",
    }
    return render(request, "invoice/edit.html", context)
    
def list(request):
    context={
        "title": "Invoice List",
        "subTitle": "Invoice List",
    }
    return render(request, "invoice/list.html", context)
    
def preview(request):
    context={
        "title": "Invoice List",
        "subTitle": "Invoice List",
    }
    return render(request, "invoice/preview.html", context)
    