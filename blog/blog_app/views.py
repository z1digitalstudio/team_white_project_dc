# Create your views here.
from django.http import HttpResponse


# View created as an example to avoid the 404 error
def home(request):
    return HttpResponse(" ")
