from datetime import timedelta, timezone
import datetime
from django.http import JsonResponse
from .forms import LeaveRequestForm
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from rest_framework.response import Response
from rest_framework import status
from .models import Employee, LeaveRequest, Notification,Attendance
from .serializers import LeaveRequestSerializer, EmployeeSerializer
from django.contrib.auth.decorators import login_required
from django.contrib import messages

class CheckInView(APIView):
    def post(self, request):
        employee = request.user.employee
        employee.check_in_time = timezone.now()
        employee.save()
        return Response({'message': 'Checked in successfully!'}, status=status.HTTP_200_OK)

class CheckOutView(APIView):
    def post(self, request):
        employee = request.user.employee
        employee.check_out_time = timezone.now()
        employee.save()
        return Response({'message': 'Checked out successfully!'}, status=status.HTTP_200_OK)

class AnnualLeaveView(APIView):
    def get(self, request):
        employee = request.user.employee
        return Response({'annual_leave': employee.annual_leave}, status=status.HTTP_200_OK)

class LateEmployeesView(APIView):
    def get(self, request):
        late_employees = Employee.objects.filter(check_in_time__gt='08:00')
        serialized_data = EmployeeSerializer(late_employees, many=True)
        return Response(serialized_data.data, status=status.HTTP_200_OK)


class LeaveRequestView(APIView):
    def get(self, request):
        leave_requests = LeaveRequest.objects.filter(employee=request.user.employee)
        serialized_data = LeaveRequestSerializer(leave_requests, many=True)
        return Response(serialized_data.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = LeaveRequestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(employee=request.user.employee)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LeaveReportView(APIView):
    def get(self, request):
        employee = request.user.employee
        leave_data = LeaveRequest.objects.filter(employee=employee)
        report = {
            'employee': employee.user.username,
            'leave_count': leave_data.count(),
        }
        return Response(report, status=status.HTTP_200_OK)

class MonthlyReportView(APIView):
    def get(self, request):
        employee = request.user.employee
        worked_hours = calculate_monthly_hours(employee.id)
        report = {
            'employee': employee.user.username,
            'worked_hours': worked_hours,
            'vacation_days_left': employee.annual_leave,
        }
        return Response(report, status=status.HTTP_200_OK)
    
def calculate_monthly_hours(employee_id):
    today = datetime.datetime.now()
    first_day_of_month = today.replace(day=1)
    last_day_of_month = (first_day_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    attendances = Attendance.objects.filter(
        employee_id=employee_id,
        date__gte=first_day_of_month,
        date__lte=last_day_of_month
    )
    total_hours = sum([attendance.work_duration() for attendance in attendances])
    return total_hours

def employee_login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and not user.is_staff:  
            login(request, user)
            return redirect('employee_dashboard')
        else:
            messages.error(request, "Geçersiz kimlik bilgileri veya Yetkili olarak giriş yaptınız!")
    return render(request, 'employee_login.html')

def admin_login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:  
            login(request, user)
            return redirect('admin_dashboard') 
        else:
            messages.error(request, "Geçersiz kimlik bilgileri veya Personel olarak giriş yaptınız!")
    return render(request, 'admin_login.html')

def employee_dashboard(request):
    user = request.user
    if user.is_staff:
        return redirect('admin_dashboard')
    employee = Employee.objects.get(user=user)
    leave_requests = LeaveRequest.objects.filter(employee=employee).order_by('-start_date')

    if request.method == "POST":
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            leave_request = form.save(commit=False)
            leave_request.employee = employee
            leave_request.save()
            messages.success(request, "İzin talebiniz başarıyla oluşturuldu!")
            return redirect('employee_dashboard')
        else:
            messages.error(request, "İzin talebinde hata oluştu. Lütfen tarihleri kontrol edin.")
    else:
        form = LeaveRequestForm()
    context = {
        'employee': employee,
        'leave_requests': leave_requests,
        'form': form,
    }
    return render(request, 'employee_dashboard.html', context)


@login_required
def admin_dashboard(request):
    user = request.user
    if not user.is_staff:
        return redirect('employee_dashboard') 
    employees = Employee.objects.all()
    attendances = Attendance.objects.filter(is_late=True).order_by('-date')
    for attendance in attendances:
        if attendance.is_late:
            late_minutes = (
                datetime.datetime.combine(attendance.date, attendance.check_in) - 
                datetime.datetime.combine(attendance.date, datetime.time(8, 0))
            ).total_seconds() / 60
            attendance.late_minutes = late_minutes  # Geç kalma süresini atıyoruz
            employee = attendance.employee
            messages.info(request, f"{employee.user.first_name} {employee.user.last_name} geç kaldı! ({late_minutes:.2f} dakika)")
           
    leave_requests = LeaveRequest.objects.all().order_by('-start_date')  # İzin talepleri
    if request.method == 'POST':
        form = LeaveRequestForm(request.POST)
        employee_id = request.POST.get('employee') 
        if form.is_valid() and employee_id:
            leave_request = form.save(commit=False)
            employee = Employee.objects.get(id=employee_id)
            leave_request.employee = employee 
            leave_request.save()
            messages.success(request, f"{employee.user.first_name} {employee.user.last_name} için izin tanımlandı!")
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Lütfen tüm alanları doldurduğunuzdan emin olun!")
    else:
        form = LeaveRequestForm()
    pending_requests = LeaveRequest.objects.filter(is_approved=False, is_rejected=False).order_by('-start_date')
    employee_monthly_hours = [
        {
            'employee': employee,
            'monthly_hours': calculate_monthly_hours(employee.id)
        }
        for employee in employees
    ]
    context = {
        'pending_requests': pending_requests,
        'attendances': attendances,  # Geç kalma süresi ile attendances verisi
        'employees': employees,  # Personel listesi
        'employee_monthly_hours': employee_monthly_hours,
        'leave_requests': leave_requests,
        'form': form  # İzin formu
    }
    return render(request, 'admin_dashboard.html', context)
from django.shortcuts import get_object_or_404

@login_required
def approve_leave(request, leave_id):
    if not request.user.is_staff:
        return redirect('employee_dashboard')
    leave_request = get_object_or_404(LeaveRequest, id=leave_id)
    leave_request.is_approved = True
    leave_request.save()
    messages.success(request, f"{leave_request.employee.user.username} adlı çalışanın izin talebi onaylandı.")
    return redirect('admin_dashboard')

@login_required
def reject_leave(request, leave_id):
    if not request.user.is_staff:
        return redirect('employee_dashboard')
    leave_request = get_object_or_404(LeaveRequest, id=leave_id)
    leave_request.is_rejected = True
    leave_request.save()
    messages.error(request, f"{leave_request.employee.user.username} adlı çalışanın izin talebi reddedildi.")
    return redirect('admin_dashboard')

def notifications_view(request):
    notifications = Notification.objects.all().values('message', 'created_at')
    return JsonResponse({'notifications': list(notifications)})
