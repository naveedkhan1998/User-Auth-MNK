from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.decorators import permission_classes
from .renderers import UserRenderer
from rest_framework.permissions import IsAuthenticated, AllowAny
from .serializers import (
    StandardSerializer,
    SubjectSerializer,
    SubjectSerializerPOST,
    StudentSerializer,
    StudentSerializerPOST,
    ClassRoomSerializer,
    ClassRoomSerializerPOST,
    ClassRoomAttendanceSerializer,
    ClassRoomAttendanceSerializerPOST,
)
from .models import Standard, Subject, Student, ClassRoom, ClassRoomAttendance
import datetime
from .utils import set_in_session


@permission_classes([AllowAny])
class StandardView(APIView):
    renderer_classes = [UserRenderer]

    def get(self, request, id=None, format=None):
        if id is not None:
            try:
                obj = Standard.objects.get(id=id)
                students = obj.student_set.all()
                serializer_standard = StandardSerializer(obj)
                serializer_student = StudentSerializer(students, many=True)
                return Response(
                    {
                        "data": {
                            "Standard": serializer_standard.data,
                            "Students": serializer_student.data,
                        },
                        "msg": "sent_successfully",
                    },
                    status=status.HTTP_200_OK,
                )
            except Standard.DoesNotExist:
                return Response(
                    {
                        "errors": {
                            "integrity": "Object with the given id doesn't exist"
                        },
                        "msg": "ID not found",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

        qs = Standard.objects.all()
        serializer = StandardSerializer(qs, many=True)
        return Response(
            {"data": serializer.data, "msg": "sent_successfully"},
            status=status.HTTP_200_OK,
        )

    def post(self, request, format=None):
        if not request.user.is_admin:
            return Response(
                {
                    "errors": {"permissions": "Only Admin Has Access"},
                    "msg": "only admins can create or delete",
                },
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        serializer = StandardSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            obj = serializer.save()
            return Response(
                {
                    "new_object": {"id": obj.id, **serializer.data},
                    "msg": "created_succesfully",
                },
                status=status.HTTP_201_CREATED,
            )

    def put(self, request, id, format=None):
        if not request.user.is_admin:
            return Response(
                {
                    "errors": {"permissions": "Only Admin Has Access"},
                    "msg": "only admins can create or delete",
                },
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )
        id = id
        qs = Standard.objects.filter(id=id)
        if qs.exists():
            serializer = StandardSerializer(data=request.data)
            if serializer.is_valid():
                obj = serializer.update(qs[0], serializer.validated_data)
                new_data = StandardSerializer(obj).data
                return Response(
                    {"new_object": new_data, "msg": "updated_succesfully"},
                    status=status.HTTP_201_CREATED,
                )

    def delete(self, request, id, format=None):
        if not request.user.is_admin:
            return Response(
                {
                    "errors": {"permissions": "Only Admin Has Access"},
                    "msg": "only admins can create or delete",
                },
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )
        id = id
        qs = Standard.objects.filter(id=id)
        if qs.exists():
            qs.delete()
            return Response({"msg": "deleted Successfully"}, status=status.HTTP_200_OK)
        else:
            return Response(
                {
                    "errors": {"integrity": "object with the given id doesnt exist"},
                    "msg": "Id not Found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )


@permission_classes([IsAuthenticated])
class StudentView(APIView):
    renderer_classes = [UserRenderer]

    def get(self, request, format=None):
        if request.user.is_teacher or request.user.is_admin:  # teacher or admin
            id = request.GET.get("standard")
            qs = Student.objects.filter(standard__id=id)
            serializer = StudentSerializer(qs, many=True)
            return Response(
                {"data": serializer.data, "msg": "sent_successfully"},
                status=status.HTTP_200_OK,
            )
        else:  # parent
            parent = request.user
            qs = Student.objects.filter(parents=parent)
            serializer = StudentSerializer(qs, many=True)
            return Response(
                {"data": serializer.data, "msg": "sent_successfully"},
                status=status.HTTP_200_OK,
            )

    def post(self, request, format=None):
        if not request.user.is_admin:
            return Response(
                {
                    "errors": {"permissions": "Only Admin Has Access"},
                    "msg": "only admins can create or delete",
                },
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        serializer = StudentSerializerPOST(data=request.data)
        if serializer.is_valid(raise_exception=True):
            obj = serializer.save()
            new_obj = Student.objects.get(pk=obj.id)
            new_data = StudentSerializer(new_obj, many=False).data
            return Response(
                {"new_object": new_data, "msg": "created_succesfully"},
                status=status.HTTP_201_CREATED,
            )

    def put(self, request, format=None):
        if not request.user.is_admin:
            return Response(
                {
                    "errors": {"permissions": "Only Admin Has Access"},
                    "msg": "only admins can create or delete",
                },
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )
        id = request.GET.get("id")
        qs = Student.objects.filter(id=id)
        if qs.exists():
            serializer = StudentSerializerPOST(data=request.data)
            if serializer.is_valid():
                obj = serializer.update(qs[0], serializer.validated_data)
                new_data = StudentSerializer(obj, many=False).data
                return Response(
                    {"new_object": new_data, "msg": "updated_succesfully"},
                    status=status.HTTP_201_CREATED,
                )

    def delete(self, request, format=None):
        if not request.user.is_admin:
            return Response(
                {
                    "errors": {"permissions": "Only Admin Has Access"},
                    "msg": "only admins can create or delete",
                },
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )
        id = request.GET.get("id")
        qs = Student.objects.filter(id=id)
        if qs.exists():
            qs.delete()
            return Response({"msg": "deleted Successfully"}, status=status.HTTP_200_OK)
        else:
            return Response(
                {
                    "errors": {"integrity": "object with the given id doesnt exist"},
                    "msg": "Id not Found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )


@permission_classes([IsAuthenticated])
class SubjectView(APIView):
    renderer_classes = [UserRenderer]

    def get(self, request, format=None):
        qs = Subject.objects.all()
        serializer = SubjectSerializer(qs, many=True)
        return Response(
            {"data": serializer.data, "msg": "sent_successfully"},
            status=status.HTTP_200_OK,
        )

    def post(self, request, format=None):
        if not request.user.is_admin:
            return Response(
                {
                    "errors": {"permissions": "Only Admin Has Access"},
                    "msg": "only admins can create or delete",
                },
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        serializer = SubjectSerializerPOST(data=request.data)
        if serializer.is_valid(raise_exception=True):
            obj = serializer.save()
            new_obj = Subject.objects.get(pk=obj.id)
            new_data = SubjectSerializer(new_obj, many=False).data
            return Response(
                {"new_object": new_data, "msg": "created_succesfully"},
                status=status.HTTP_201_CREATED,
            )

    def put(self, request, format=None):
        if not request.user.is_admin:
            return Response(
                {
                    "errors": {"permissions": "Only Admin Has Access"},
                    "msg": "only admins can create or delete",
                },
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )
        id = request.GET.get("id")
        qs = Subject.objects.filter(id=id)
        if qs.exists():
            serializer = SubjectSerializerPOST(data=request.data)
            if serializer.is_valid():
                obj = serializer.update(qs[0], serializer.validated_data)
                new_data = SubjectSerializer(obj, many=False).data
                return Response(
                    {"new_object": new_data, "msg": "updated_succesfully"},
                    status=status.HTTP_201_CREATED,
                )

    def delete(self, request, format=None):
        if not request.user.is_admin:
            return Response(
                {
                    "errors": {"permissions": "Only Admin Has Access"},
                    "msg": "only admins can create or delete",
                },
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )
        id = request.GET.get("id")
        qs = Subject.objects.filter(id=id)
        if qs.exists():
            qs.delete()
            return Response({"msg": "deleted Successfully"}, status=status.HTTP_200_OK)
        else:
            return Response(
                {
                    "errors": {"integrity": "object with the given id doesnt exist"},
                    "msg": "Id not Found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )


@permission_classes([IsAuthenticated])
class ClassRoomView(APIView):
    renderer_classes = [UserRenderer]

    def get(self, request, format=None):
        qs = ClassRoom.objects.all()
        serializer = ClassRoomSerializer(qs, many=True)
        return Response(
            {"data": serializer.data, "msg": "sent_successfully"},
            status=status.HTTP_200_OK,
        )

    def post(self, request, format=None):
        serializer = ClassRoomSerializerPOST(data=request.data)
        if serializer.is_valid(raise_exception=True):
            obj = serializer.save()
            new_obj = ClassRoom.objects.get(pk=obj.id)
            new_data = ClassRoomSerializer(new_obj, many=False).data
            return Response(
                {"new_object": new_data, "msg": "created_succesfully"},
                status=status.HTTP_201_CREATED,
            )

    def put(self, request, format=None):
        if not request.user.is_admin:
            return Response(
                {
                    "errors": {"permissions": "Only Admin Has Access"},
                    "msg": "only admins can create or delete",
                },
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )
        id = request.GET.get("id")
        qs = ClassRoom.objects.filter(id=id)
        if qs.exists():
            serializer = ClassRoomSerializerPOST(data=request.data)
            if serializer.is_valid():
                obj = serializer.update(qs[0], serializer.validated_data)
                new_data = ClassRoomSerializer(obj, many=False).data
                return Response(
                    {"new_object": new_data, "msg": "updated_succesfully"},
                    status=status.HTTP_201_CREATED,
                )

    def delete(self, request, format=None):
        if not request.user.is_admin:
            return Response(
                {
                    "errors": {"permissions": "Only Admin Has Access"},
                    "msg": "only admins can create or delete",
                },
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )
        id = request.GET.get("id")
        qs = ClassRoom.objects.filter(id=id)
        if qs.exists():
            qs.delete()
            return Response({"msg": "deleted Successfully"}, status=status.HTTP_200_OK)
        else:
            return Response(
                {
                    "errors": {"integrity": "object with the given id doesnt exist"},
                    "msg": "Id not Found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )


@permission_classes([IsAuthenticated])
class ClassRoomAttendanceView(APIView):
    renderer_classes = [UserRenderer]

    def get(self, request, format=None):
        qs = ClassRoomAttendance.objects.all()
        serializer = ClassRoomAttendanceSerializer(qs, many=True)
        return Response(
            {"data": serializer.data, "msg": "sent_successfully"},
            status=status.HTTP_200_OK,
        )

    def post(self, request, format=None):
        serializer = ClassRoomAttendanceSerializerPOST(data=request.data)
        if serializer.is_valid(raise_exception=True):
            obj = serializer.save()
            new_obj = ClassRoomAttendance.objects.get(pk=obj.id)
            new_obj.attendance_percentage = (
                new_obj.students_present.count()
                / (new_obj.students_abscent.count() + new_obj.students_present.count())
            ) * 100
            new_obj.save()
            new_data = ClassRoomAttendanceSerializer(new_obj, many=False).data
            set_in_session(new_obj, True)
            return Response(
                {"new_object": new_data, "msg": "created_succesfully"},
                status=status.HTTP_201_CREATED,
            )

    def put(self, request, format=None):
        # if not request.user.is_admin:
        # return Response({"errors":{'permissions':'Only Admin Has Access'},"msg":"only admins can create or delete"},status=status.HTTP_406_NOT_ACCEPTABLE)
        id = request.GET.get("id")
        qs = ClassRoomAttendance.objects.filter(id=id)
        if qs.exists():
            attendance = qs.last()
            attendance.finished_on = datetime.datetime.now()
            attendance.is_in_session = False
            attendance.save()
            set_in_session(attendance, False)
            return Response(
                {"msg": "updated_succesfully"}, status=status.HTTP_201_CREATED
            )
        return Response(
            {
                "errors": {"integrity": "object with the given id doesnt exist"},
                "msg": "Not Found",
            },
            status=status.HTTP_404_NOT_FOUND,
        )

        # serializer = ClassRoomAttendanceSerializerPOST(data=request.data)
        # if serializer.is_valid(raise_exception=True):
        #    obj = serializer.update(qs[0],serializer.validated_data)
        #    new_data = ClassRoomAttendanceSerializer(obj,many=False).data
        #    return Response({"new_object":new_data,"msg":"updated_succesfully"},status=status.HTTP_201_CREATED)

    def delete(self, request, format=None):
        if not request.user.is_admin:
            return Response(
                {
                    "errors": {"permissions": "Only Admin Has Access"},
                    "msg": "only admins can create or delete",
                },
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )
        id = request.GET.get("id")
        qs = ClassRoomAttendance.objects.filter(id=id)
        if qs.exists():
            qs.delete()
            return Response({"msg": "deleted Successfully"}, status=status.HTTP_200_OK)
        else:
            return Response(
                {
                    "errors": {"integrity": "object with the given id doesnt exist"},
                    "msg": "Id not Found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )
