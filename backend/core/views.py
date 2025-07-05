from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import FootImageSerializer

def upload_form_view(request):
    return render(request, 'upload_form.html')

class FootImageUploadView(APIView):
    def post(self, request, format=None):
        serializer = FootImageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


'''
    --------------Missing Components As Reviewed----------

    User Authentication

    CV Integration

    Foot Measurement Storage - DB Error

    Shoe recommendation

    User Portal - DB Error


'''