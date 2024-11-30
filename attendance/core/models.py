from django.db import models
from django.contrib.auth.models import User
import datetime
from django.db.models.signals import post_save
from django.dispatch import receiver

class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    annual_leave = models.FloatField(default=15)  # Başlangıçta 15 gün izin
    used_leave = models.FloatField(default=0)  # Kullanılmış izin

    def __str__(self):
        return self.user.username

class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    is_late = models.BooleanField(default=False)
    late_minutes = models.FloatField(default=0)

    def save(self, *args, **kwargs):
        if self.check_in and not self.is_weekend:
            if self.check_in > datetime.time(8, 0):
                self.is_late = True
                self.late_minutes = (
                    datetime.datetime.combine(self.date, self.check_in) -
                    datetime.datetime.combine(self.date, datetime.time(8, 0))
                ).total_seconds() / 60
                leave_deduction = self.late_minutes / 600
                self.employee.annual_leave = max(0, self.employee.annual_leave - leave_deduction)
                self.employee.save()
                self.send_late_notification()
            else:
                self.is_late = False
                self.late_minutes = 0
        super().save(*args, **kwargs)

    @property
    def is_weekend(self):
        return self.date and self.date.weekday() in [5, 6]

    def send_late_notification(self):
        if self.is_late:
            notification_message = f"{self.employee.user.username} personeli {self.late_minutes:.1f} dakika geç kaldı."
            if not Notification.objects.filter(
                recipient=User.objects.first(), 
                message=notification_message
            ).exists():
                Notification.objects.create(
                    recipient=User.objects.first(),
                    message=notification_message
                )
    def work_duration(self):
        if self.check_in and self.check_out:
            start = datetime.datetime.combine(self.date, self.check_in)
            end = datetime.datetime.combine(self.date, self.check_out)
            return (end - start).seconds / 3600  # Saat cinsinden döndür
        return 0
    
    def __str__(self):
        return f"{self.employee.user.username} - {self.date}"
    @property
    def is_weekend(self):
        return self.date and self.date.weekday() in [5, 6]
    
    
class LeaveRequest(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    is_approved = models.BooleanField(default=False)  
    is_rejected = models.BooleanField(default=False) 

    @property
    def total_leave_days(self):
        total_days = (self.end_date - self.start_date).days + 1
        weekdays = [self.start_date + datetime.timedelta(days=i) for i in range(total_days)]
        business_days = [day for day in weekdays if day.weekday() not in [5, 6]]
        return len(business_days)

    def save(self, *args, **kwargs):
        if self.is_approved:
            self.employee.used_leave += self.total_leave_days
            self.employee.annual_leave = max(0, self.employee.annual_leave - self.total_leave_days)
            self.employee.save()
        super().save(*args, **kwargs)

class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.recipient.username}"

@receiver(post_save, sender=Employee)
def check_annual_leave(sender, instance, **kwargs):
    if instance.annual_leave < 3:
        Notification.objects.create(
            recipient=User.objects.filter(is_staff=True).first(),  # İlk yetkiliye bildirim gönderir
            message=f"{instance.user.username} adlı personelin kalan yıllık izni 3 günün altına düştü!"
        )

