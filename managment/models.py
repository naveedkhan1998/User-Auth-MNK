from django.db import models
from account.models import User
# Create your models here.


class Standard(models.Model):
    standard = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)
    is_in_session = models.BooleanField(default=False)

    def __str__(self):
        return str(self.standard)
    
class Subject(models.Model):
    subject_name = models.CharField(blank=False,max_length=255,default="MATH")
    teachers = models.ManyToManyField(User)
    is_active = models.BooleanField(default=True)
    is_in_session = models.BooleanField(default=False)

    def __str__(self):
        return self.subject_name


class Student(models.Model):
    avatar = models.ImageField(
        verbose_name='avatar',
        upload_to='student/avatar/',
        null=True,
        default='/profile_icon.png'
    )
    name = models.CharField(max_length=255,blank=False)
    standard = models.ForeignKey(Standard,on_delete=models.CASCADE, null=False)
    parents = models.ManyToManyField(User,blank=True)
    is_in_session = models.BooleanField(default=False)
    
    def __str__(self) -> str:
        return self.name

class ClassRoom(models.Model):
    teacher = models.ForeignKey(User,on_delete=models.CASCADE,blank=False)
    standard = models.ForeignKey(Standard,on_delete=models.CASCADE,blank=False)
    subject = models.ForeignKey(Subject,on_delete=models.CASCADE,blank=False)
    is_active = models.BooleanField(default=True)
    is_in_session = models.BooleanField(default=False)

    def __str__(self):
        return "Teacher:"+self.teacher.name+"| Class:"+str(self.standard.standard)+"| Subject:"+self.subject.subject_name

class ClassRoomAttendance(models.Model):

    def percentage(self):
        query = Student.objects.filter(standard=self.classroom.standard)
        return (self.students_present.count()/query.count())*100

    classroom = models.ForeignKey(ClassRoom,on_delete=models.PROTECT,blank=False)
    students_present = models.ManyToManyField(Student,related_name='presentes')
    students_abscent = models.ManyToManyField(Student,related_name='abscentses')
    attendance_percentage = models.FloatField(default=0)
    created_on = models.DateTimeField(auto_now_add=True)
    finished_on = models.DateTimeField(blank=True,null=True)
    is_active = models.BooleanField(default=True)
    is_in_session = models.BooleanField(default=True)


    def __str__(self):
        return str(self.classroom)+" : "+"Total Attendance: "+str(self.percentage())+" Created On:"+str(self.created_on)
    
    
    
    
