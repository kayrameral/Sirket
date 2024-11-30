import datetime
from django.test import TestCase
from django.utils import timezone
from datetime import time, date
from .models import Attendance, Employee, Notification, User

def test_late_attendance(self):
    """Geç kalan çalışanın geç kalma durumu ve yıllık izin kesintisi doğru hesaplanmalı."""
    attendance = Attendance.objects.create(
        employee=self.employee,
        date=datetime.date.today(),
        check_in=datetime.time(11, 0)  # 60 dakika geç
    )
    attendance.save()

   
    self.assertTrue(attendance.is_late, "is_late doğru ayarlanmamış.")  # Beklenen: True
    self.assertEqual(attendance.late_minutes, 60, "Geç kalma süresi yanlış hesaplanmış.")  # Beklenen: 60