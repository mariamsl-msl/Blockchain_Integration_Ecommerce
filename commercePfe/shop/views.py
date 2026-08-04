from django.shortcuts import render

def home(request):
    return render(request, 'shop/home.html')

def women(request):
    return render(request, 'shop/women.html')

def men(request):
    return render(request, 'shop/men.html')


def girls(request):
    return render(request, "shop/girls.html")

def boys(request):
    return render(request, 'shop/boys.html')

def babies(request):
    return render(request, 'shop/babies.html')

def cosmetics(request):
    return render(request, 'shop/cosmetics.html')

# 
def accessories(request):
    return render(request, 'shop/accessories.html')

def pages(request):
    return render(request, 'shop/pages.html')


