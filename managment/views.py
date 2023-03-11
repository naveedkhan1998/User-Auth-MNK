from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated,AllowAny
from .serializers import StudentSerializer
from .models import Student
import json
from rest_framework.response import Response
# Create your views here.


@api_view(["GET"])
@permission_classes([AllowAny])
def get_students_list(request):
    student_qs = Student.objects.all()
    data = StudentSerializer(student_qs,many=True).data
    return Response(data,status=200)


@api_view(["POST","PUT","DELETE"])
@permission_classes([AllowAny])
def update_students_list(request):
    if request.method == 'POST':
        data2 = request.data
        serializer = StudentSerializer(data=data2)
        if serializer.is_valid():
            serializer.create(validated_data=serializer.validated_data)
            return Response({"msg":"created_succesfully"},status=200)
        else:
            return Response({"msg":"error"},status=400)
    if request.method == 'PUT':
        id = request.GET.get('id')
        qs = Student.objects.filter(id=id)
        if qs.exists():
            serializer = StudentSerializer(data=request.data)
            if serializer.is_valid():
                serializer.update(qs[0],serializer.validated_data)
                return Response({"msg":"created_succesfully"},status=200)
            else:
                return Response({"msg":"error"},status=400)
    #student_qs = Student.objects.all()
    #data = StudentSerializer(student_qs,many=True).data
    #return Response(data,status=200)


