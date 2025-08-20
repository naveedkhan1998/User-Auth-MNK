from managment.models import ClassRoomAttendance,Standard,ClassRoom,Student
from account.models import User


def set_in_session(obj:ClassRoomAttendance,set:bool=True):
    obj.classroom:ClassRoom
    obj.classroom.is_in_session = set
    obj.classroom.save()
    obj.classroom.teacher:User
    obj.classroom.teacher.is_in_session = set
    obj.classroom.teacher.save()
    obj.classroom.standard:Standard
    obj.classroom.standard.is_in_session = set
    obj.classroom.standard.save()



    for student in obj.students_present.all():
        student:Student
        student.is_in_session = set
        student.save()

        