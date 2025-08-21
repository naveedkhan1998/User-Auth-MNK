from rest_framework import serializers
from rest_framework.fields import IntegerField, CharField, DateTimeField
from account.serializers import UserProfileSerializer
from .models import Standard,Subject,Student,ClassRoom,ClassRoomAttendance
from backend.settings import MAIN_URL_2


class StandardSerializer(serializers.ModelSerializer):
    id = IntegerField(required=False)
    class Meta:
        model = Standard
        fields = ['id','standard','is_in_session']

class StudentSerializer(serializers.ModelSerializer):
    @staticmethod
    def get_avatar(obj):
        try:
            return MAIN_URL_2+obj.avatar.url
        except:
            return None
        
    id = IntegerField(required=False)
    avatar = serializers.SerializerMethodField('get_avatar')
    standard = StandardSerializer()
    class Meta:
        model = Student
        fields = ['id','name','standard','avatar','is_in_session']

class StudentSerializerPOST(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ['id','name','standard','avatar','is_in_session']

class SubjectSerializer(serializers.ModelSerializer):
    teachers = UserProfileSerializer(many=True)
    class Meta:
        model = Subject
        fields = '__all__'

class SubjectSerializerPOST(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = '__all__'

class ClassRoomSerializer(serializers.ModelSerializer):
    teacher = UserProfileSerializer()
    standard = StandardSerializer()
    subject = SubjectSerializer()
    class Meta:
        model = ClassRoom
        fields = '__all__'

class ClassRoomSerializerPOST(serializers.ModelSerializer):

    def create(self, attrs):
        teacher_obj = attrs.get('teacher')
        subject_obj:Subject = attrs.get('subject')
        if teacher_obj not in subject_obj.teachers.all():
            raise serializers.ValidationError("Logged IN Teacher is not Authorised to teach the class.")
        query = ClassRoom.objects.filter(teacher=teacher_obj,subject=subject_obj)
        if query.exists():
            raise serializers.ValidationError("Class Room Already Exists!!")
        obj = ClassRoom(**attrs)
        obj.save()
        return obj
    class Meta:
        model = ClassRoom
        fields = '__all__'
class ClassRoomAttendanceSerializer(serializers.ModelSerializer):
    #@staticmethod
    #def get_attendance_percentage(obj):
    #    return (obj.students_present.count()/(obj.students_present.count()+obj.students_abscent.count()))*100


    classroom = ClassRoomSerializer()
    students_present = StudentSerializer(many=True)
    students_abscent = StudentSerializer(many=True)
    #attendance_percentage = serializers.SerializerMethodField()
    class Meta:
        model = ClassRoomAttendance
        fields = '__all__'

class ClassRoomAttendanceSerializerPOST(serializers.ModelSerializer):

    #def create(self,attrs):
    #    classroom:ClassRoom = attrs.get('classroom')
    #    students_present:Student = attrs.get('students_present')
    #    students_abscent:Student = attrs.get('students_abscent')
    #    percentage = 0
    #    student_query = Student.objects.filter(standard=classroom.standard).exclude(id__in=students_present.all())
    #    attrs['students_abscent'] = student_query
    #    percentage = (students_present.count()/student_query.count())*100
    #    obj = ClassRoomAttendance(**attrs,attendance_percentage=percentage)
    #    return obj


    class Meta:
        model = ClassRoomAttendance
        fields = '__all__'



