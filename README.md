api/ check-in/ [name='check-in']
api/ check-out/ [name='check-out']
api/ annual-leave/ [name='annual-leave']
api/ late-employees/ [name='late-employees']
api/ leave-requests/ [name='leave-requests']
api/ approve-leave/<int:leave_id>/ [name='approve_leave']
api/ leave-report/ [name='leave-report']
api/ notifications/ [name='notifications']
api/ admin-login/ [name='admin_login']
api/ employee-login/ [name='employee_login']
api/ monthly-report/ [name='monthly_report_api']
api/ employee-dashboard/ [name='employee_dashboard']
api/ admin-dashboard/ [name='admin_dashboard']
api/ reject-leave/<int:leave_id>/ [name='reject_leave']

pathler böyle zaten core/urls.py'de görürsünüz.

örnek bir employee: employee_user | password123 
örnek iki tane admin: admin_user | password , kayra | password


Her personelin aylık çalışma saatlerini özetleyen bir rapor sistemi yanlış hesaplıyor. Başka hatalar da olabilir.
