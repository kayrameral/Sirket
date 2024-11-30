from django.urls import path
from . import views
from .views import CheckInView, CheckOutView, AnnualLeaveView, LateEmployeesView,notifications_view, approve_leave, reject_leave
from .views import LeaveRequestView, LeaveReportView, MonthlyReportView 
urlpatterns = [
    path('check-in/', CheckInView.as_view(), name='check-in'),
    path('check-out/', CheckOutView.as_view(), name='check-out'),
    path('annual-leave/', AnnualLeaveView.as_view(), name='annual-leave'),
    path('late-employees/', LateEmployeesView.as_view(), name='late-employees'),
    path('leave-requests/', LeaveRequestView.as_view(), name='leave-requests'),
    path('approve-leave/<int:leave_id>/', approve_leave, name='approve_leave'),
    path('leave-report/', LeaveReportView.as_view(), name='leave-report'),
    path('notifications/', notifications_view, name='notifications'),
    path('admin-login/', views.admin_login, name='admin_login'),
    path('employee-login/', views.employee_login, name='employee_login'),
    path('monthly-report/', MonthlyReportView.as_view(), name='monthly_report_api'),
    path('employee-dashboard/', views.employee_dashboard, name='employee_dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('reject-leave/<int:leave_id>/', reject_leave, name='reject_leave'),
    
]