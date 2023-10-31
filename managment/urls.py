from django.urls import path, include
from .views import (
    StandardView,
    StudentView,
    SubjectView,
    ClassRoomView,
    ClassRoomAttendanceView,
)  # get_students_list,update_students_list


urlpatterns = [
    path("standard/", StandardView.as_view(), name="standard"),
    path("students/", StudentView.as_view(), name="students"),
    path("subjects/", SubjectView.as_view(), name="subjects"),
    path("classrooms/", ClassRoomView.as_view(), name="classrooms"),
    path("attendance/", ClassRoomAttendanceView.as_view(), name="attendance"),
]
