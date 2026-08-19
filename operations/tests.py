from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser, StudentProfile
from core.models import Room, RoomAllocation
from operations.models import ChatMessage, Conversation, Notification, Fee, Complaint, LeaveApplication, Attendance, Visitor


class DashboardAndChatTests(TestCase):
    def setUp(self):
        self.student_user = CustomUser.objects.create_user(
            username='student1',
            password='secret123',
            role='student',
            email='student@example.com',
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            enrollment_number='S1001',
        )
        self.warden_user = CustomUser.objects.create_user(
            username='warden1',
            password='secret123',
            role='warden',
            email='warden@example.com',
        )
        Notification.objects.create(
            recipient=self.student_user,
            title='New update',
            message='Your complaint has been reviewed.',
            notification_type='info',
        )

    def test_student_dashboard_lists_recent_notifications(self):
        self.client.force_login(self.student_user)
        response = self.client.get(reverse('student_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Recent Notifications')
        self.assertContains(response, 'New update')

    def test_chat_page_lists_existing_conversations(self):
        conversation = Conversation.objects.create(title='Room support')
        conversation.participants.add(self.student_user, self.warden_user)
        ChatMessage.objects.create(
            conversation=conversation,
            sender=self.student_user,
            content='Hello warden',
        )

        self.client.force_login(self.student_user)
        response = self.client.get(reverse('chat'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Room support')
        self.assertContains(response, 'Hello warden')

    def test_student_can_start_a_new_chat_with_warden(self):
        self.client.force_login(self.student_user)
        response = self.client.post(
            reverse('chat'),
            {'content': 'Can I talk to you about my room?'}
        )

        self.assertEqual(response.status_code, 302)
        conversation = Conversation.objects.filter(participants=self.student_user).first()
        self.assertIsNotNone(conversation)
        self.assertTrue(ChatMessage.objects.filter(conversation=conversation, sender=self.student_user).exists())

    def test_admin_dashboard_shows_summary_metrics(self):
        admin_user = CustomUser.objects.create_user(
            username='admin1',
            password='secret123',
            role='admin',
            email='admin@example.com',
        )
        active_student = CustomUser.objects.create_user(
            username='student2',
            password='secret123',
            role='student',
            email='student2@example.com',
            is_active=True,
        )
        pending_student = CustomUser.objects.create_user(
            username='student3',
            password='secret123',
            role='student',
            email='student3@example.com',
            is_active=False,
        )
        StudentProfile.objects.create(user=active_student, enrollment_number='S1002')
        StudentProfile.objects.create(user=pending_student, enrollment_number='S1003')

        Notification.objects.create(
            recipient=admin_user,
            title='Admin alert',
            message='New approval submitted.',
            notification_type='info',
        )

        conversation = Conversation.objects.create(title='Admin support')
        conversation.participants.add(admin_user, active_student)

        self.client.force_login(admin_user)
        response = self.client.get(reverse('admin_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Admin Dashboard')
        self.assertContains(response, 'Total Students')
        self.assertContains(response, 'Pending Approvals')
        self.assertContains(response, 'Unread Alerts')
        self.assertContains(response, '1 pending')

    def test_admin_pending_registrations_link_returns_to_admin_dashboard(self):
        admin_user = CustomUser.objects.create_user(
            username='admin2',
            password='secret123',
            role='admin',
            email='admin2@example.com',
        )
        CustomUser.objects.create_user(
            username='student4',
            password='secret123',
            role='student',
            email='student4@example.com',
            is_active=False,
        )

        self.client.force_login(admin_user)
        response = self.client.get(reverse('pending_registrations'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('admin_dashboard'))
        self.assertNotContains(response, reverse('warden_dashboard'))

    def test_warden_dashboard_shows_fee_metric(self):
        warden_user = CustomUser.objects.create_user(
            username='warden2',
            password='secret123',
            role='warden',
            email='warden2@example.com',
        )
        student = CustomUser.objects.create_user(
            username='student5',
            password='secret123',
            role='student',
            email='student5@example.com',
            is_active=True,
        )
        profile = StudentProfile.objects.create(user=student, enrollment_number='S1005')

        for i in range(5):
            Fee.objects.create(
                student=profile,
                fee_type='hostel',
                amount=100,
                due_date='2026-08-15',
                status='pending',
            )

        self.client.force_login(warden_user)
        response = self.client.get(reverse('warden_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Warden Dashboard')
        self.assertContains(response, 'Fee Records')
        html = response.content.decode('utf-8')
        self.assertIn('>5<', html)

    def test_warden_can_approve_leave_request_without_profile_record(self):
        warden_user = CustomUser.objects.create_user(
            username='warden_leave',
            password='secret123',
            role='warden',
            email='warden_leave@example.com',
        )
        student = CustomUser.objects.create_user(
            username='student_leave',
            password='secret123',
            role='student',
            email='student_leave@example.com',
            is_active=True,
        )
        student_profile = StudentProfile.objects.create(user=student, enrollment_number='S1010')
        leave = student_profile.leave_applications.create(
            leave_from='2026-08-20',
            leave_to='2026-08-25',
            reason='Family visit',
            destination='Home town',
            contact_during_leave='9876543210',
            status='pending',
        )

        self.client.force_login(warden_user)
        response = self.client.post(
            reverse('warden_leave_requests'),
            {'leave_id': leave.id, 'action': 'approve', 'notes': 'Approved for family visit'}
        )

        self.assertEqual(response.status_code, 302)
        leave.refresh_from_db()
        self.assertEqual(leave.status, 'approved')
        self.assertIsNotNone(leave.approved_by)

    def test_warden_can_resolve_complaint_without_profile_record(self):
        warden_user = CustomUser.objects.create_user(
            username='warden_complaint',
            password='secret123',
            role='warden',
            email='warden_complaint@example.com',
        )
        student = CustomUser.objects.create_user(
            username='student_complaint',
            password='secret123',
            role='student',
            email='student_complaint@example.com',
            is_active=True,
        )
        student_profile = StudentProfile.objects.create(user=student, enrollment_number='S1011')
        complaint = Complaint.objects.create(
            student=student_profile,
            title='Water issue',
            description='No water supply for two days.',
            category='water',
            priority='high',
            status='pending',
        )

        self.client.force_login(warden_user)
        response = self.client.post(
            reverse('resolve_complaint', args=[complaint.id]),
            {'status': 'resolved', 'resolution_notes': 'Water supply restored by maintenance team.'}
        )

        self.assertEqual(response.status_code, 302)
        complaint.refresh_from_db()
        self.assertEqual(complaint.status, 'resolved')
        self.assertIsNotNone(complaint.resolved_by)

    def test_warden_can_bulk_approve_selected_leave_requests(self):
        warden_user = CustomUser.objects.create_user(
            username='warden_bulk_leave',
            password='secret123',
            role='warden',
            email='warden_bulk_leave@example.com',
        )
        student = CustomUser.objects.create_user(
            username='student_bulk_leave',
            password='secret123',
            role='student',
            email='student_bulk_leave@example.com',
            is_active=True,
        )
        student_profile = StudentProfile.objects.create(user=student, enrollment_number='S1018')
        leave_one = student_profile.leave_applications.create(
            leave_from='2026-09-01',
            leave_to='2026-09-05',
            reason='Family visit',
            destination='Home town',
            contact_during_leave='9876543210',
            status='pending',
        )
        leave_two = student_profile.leave_applications.create(
            leave_from='2026-09-10',
            leave_to='2026-09-15',
            reason='Medical checkup',
            destination='City hospital',
            contact_during_leave='9876543210',
            status='pending',
        )

        self.client.force_login(warden_user)
        response = self.client.post(
            reverse('warden_leave_requests'),
            {'bulk_action': 'approve', 'leave_ids': [str(leave_one.id), str(leave_two.id)], 'notes': 'Approved in bulk.'}
        )

        self.assertEqual(response.status_code, 302)
        leave_one.refresh_from_db()
        leave_two.refresh_from_db()
        self.assertEqual(leave_one.status, 'approved')
        self.assertEqual(leave_two.status, 'approved')

    def test_warden_can_bulk_resolve_selected_complaints(self):
        warden_user = CustomUser.objects.create_user(
            username='warden_bulk_complaint',
            password='secret123',
            role='warden',
            email='warden_bulk_complaint@example.com',
        )
        student = CustomUser.objects.create_user(
            username='student_bulk_complaint',
            password='secret123',
            role='student',
            email='student_bulk_complaint@example.com',
            is_active=True,
        )
        student_profile = StudentProfile.objects.create(user=student, enrollment_number='S1019')
        complaint_one = Complaint.objects.create(
            student=student_profile,
            title='Water issue',
            description='No water for two days.',
            category='water',
            priority='high',
            status='pending',
        )
        complaint_two = Complaint.objects.create(
            student=student_profile,
            title='Power issue',
            description='Lights flickering.',
            category='electricity',
            priority='medium',
            status='pending',
        )

        self.client.force_login(warden_user)
        response = self.client.post(
            reverse('warden_complaints'),
            {'bulk_action': 'resolve', 'complaint_ids': [str(complaint_one.id), str(complaint_two.id)], 'resolution_notes': 'Fixed by maintenance team.'}
        )

        self.assertEqual(response.status_code, 302)
        complaint_one.refresh_from_db()
        complaint_two.refresh_from_db()
        self.assertEqual(complaint_one.status, 'resolved')
        self.assertEqual(complaint_two.status, 'resolved')

    def test_warden_attendance_analytics_page_renders_trend_and_absentees(self):
        warden_user = CustomUser.objects.create_user(
            username='warden_stats',
            password='secret123',
            role='warden',
            email='warden_stats@example.com',
        )
        student = CustomUser.objects.create_user(
            username='student_stats',
            password='secret123',
            role='student',
            email='student_stats@example.com',
            is_active=True,
        )
        student_profile = StudentProfile.objects.create(user=student, enrollment_number='S1012')
        today = __import__('datetime').date.today()
        Attendance.objects.create(student=student_profile, date=today, status='absent', notes='No show')
        Attendance.objects.create(student=student_profile, date=today.__sub__(__import__('datetime').timedelta(days=1)), status='present', notes='On time')

        self.client.force_login(warden_user)
        response = self.client.get(reverse('warden_attendance_analytics'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Attendance Analytics')
        self.assertContains(response, 'Absentees')
        self.assertContains(response, 'student_stats')

    def test_warden_can_export_fee_data_as_csv(self):
        warden_user = CustomUser.objects.create_user(
            username='warden_export_fees',
            password='secret123',
            role='warden',
            email='warden_export_fees@example.com',
        )
        student = CustomUser.objects.create_user(
            username='student_export_fees',
            password='secret123',
            role='student',
            email='student_export_fees@example.com',
            is_active=True,
        )
        student_profile = StudentProfile.objects.create(user=student, enrollment_number='S1014')
        Fee.objects.create(
            student=student_profile,
            fee_type='hostel',
            amount=2500,
            amount_paid=1200,
            due_date='2026-08-25',
            status='pending',
            month='Aug-2026',
        )

        self.client.force_login(warden_user)
        response = self.client.get(reverse('export_reports', args=['fees', 'csv']))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('fee_type', response.content.decode('utf-8'))
        self.assertIn('hostel', response.content.decode('utf-8'))

    def test_warden_can_export_complaint_data_as_pdf(self):
        warden_user = CustomUser.objects.create_user(
            username='warden_export_complaints',
            password='secret123',
            role='warden',
            email='warden_export_complaints@example.com',
        )
        student = CustomUser.objects.create_user(
            username='student_export_complaints',
            password='secret123',
            role='student',
            email='student_export_complaints@example.com',
            is_active=True,
        )
        student_profile = StudentProfile.objects.create(user=student, enrollment_number='S1015')
        Complaint.objects.create(
            student=student_profile,
            title='Water issue',
            description='No water for two days.',
            category='water',
            priority='high',
            status='pending',
        )

        self.client.force_login(warden_user)
        response = self.client.get(reverse('export_reports', args=['complaints', 'pdf']))

        self.assertEqual(response.status_code, 200)
        self.assertIn('application/pdf', response['Content-Type'])
        self.assertIn(b'%PDF', response.content[:4])

    def test_status_change_sends_email_and_creates_notification(self):
        from accounts.views import dispatch_status_notification

        student = CustomUser.objects.create_user(
            username='student_notify',
            password='secret123',
            role='student',
            email='student_notify@example.com',
            is_active=True,
        )
        StudentProfile.objects.create(user=student, enrollment_number='S1016')

        sent = dispatch_status_notification(
            recipient=student,
            title='Leave Approved',
            message='Your leave request has been approved.',
            notification_type='success',
            sender=self.warden_user,
            related_model='leave',
            related_id=42,
        )

        self.assertTrue(sent)
        self.assertTrue(student.notifications.filter(title='Leave Approved').exists())

    def test_student_self_service_portal_shows_room_and_fee_summary(self):
        student = CustomUser.objects.create_user(
            username='student_self_service',
            password='secret123',
            role='student',
            email='student_self_service@example.com',
            is_active=True,
        )
        student_profile = StudentProfile.objects.create(user=student, enrollment_number='S1017')
        room = Room.objects.create(
            room_number='101',
            floor=1,
            block='A',
            room_type='double',
            capacity=2,
            rent_amount=3000,
            has_wifi=True,
            status='occupied',
        )
        RoomAllocation.objects.create(student=student_profile, room=room, is_active=True)
        Fee.objects.create(
            student=student_profile,
            fee_type='hostel',
            amount=3000,
            amount_paid=1500,
            due_date='2026-08-25',
            status='pending',
            month='Aug-2026',
        )

        self.client.force_login(student)
        response = self.client.get(reverse('student_self_service'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Student Self-Service Portal')
        self.assertContains(response, 'Room Overview')
        self.assertContains(response, 'Fee Payment Status')
        self.assertContains(response, 'Room 101')

    def test_automated_reminders_are_generated_for_overdue_fees_and_pending_approvals(self):
        warden_user = CustomUser.objects.create_user(
            username='warden_reminder',
            password='secret123',
            role='warden',
            email='warden_reminder@example.com',
        )
        student = CustomUser.objects.create_user(
            username='student_reminder',
            password='secret123',
            role='student',
            email='student_reminder@example.com',
            is_active=True,
        )
        student_profile = StudentProfile.objects.create(user=student, enrollment_number='S1020')
        Fee.objects.create(
            student=student_profile,
            fee_type='hostel',
            amount=2500,
            amount_paid=0,
            due_date='2026-08-01',
            status='overdue',
            month='Aug-2026',
        )
        student_profile.leave_applications.create(
            leave_from='2026-08-20',
            leave_to='2026-08-25',
            reason='Family visit',
            destination='Home town',
            contact_during_leave='9876543210',
            status='pending',
        )
        Complaint.objects.create(
            student=student_profile,
            title='Water issue',
            description='No water supply.',
            category='water',
            priority='high',
            status='pending',
        )

        self.client.force_login(warden_user)
        response = self.client.get(reverse('warden_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Notification.objects.filter(recipient=warden_user, title='Overdue Fee Reminder').exists())
        self.assertTrue(Notification.objects.filter(recipient=warden_user, title='Pending Approvals Reminder').exists())

    def test_warden_visitor_status_workflow_and_gate_pass_page(self):
        warden_user = CustomUser.objects.create_user(
            username='warden_visitor',
            password='secret123',
            role='warden',
            email='warden_visitor@example.com',
        )
        student = CustomUser.objects.create_user(
            username='student_visitor',
            password='secret123',
            role='student',
            email='student_visitor@example.com',
            is_active=True,
        )
        student_profile = StudentProfile.objects.create(user=student, enrollment_number='S1013')
        visitor = Visitor.objects.create(
            student=student_profile,
            visitor_name='Ravi Kumar',
            visitor_phone='9876543210',
            visitor_id_type='aadhar',
            visitor_id_number='123456789012',
            visit_date='2026-08-20',
            visit_time='18:00:00',
            purpose='Family visit',
            status='pending',
        )

        self.client.force_login(warden_user)
        page_response = self.client.get(reverse('warden_visitors'))
        self.assertEqual(page_response.status_code, 200)
        self.assertContains(page_response, 'Visitor Management')

        gate_response = self.client.get(reverse('visitor_gate_pass', args=[visitor.id]))
        self.assertEqual(gate_response.status_code, 200)
        self.assertContains(gate_response, 'Gate Pass')

        checkin_response = self.client.post(
            reverse('check_in_visitor', args=[visitor.id]),
            {'status': 'checked_in', 'notes': 'Visitor has arrived'}
        )
        self.assertEqual(checkin_response.status_code, 302)
        visitor.refresh_from_db()
        self.assertEqual(visitor.status, 'checked_in')
        self.assertIsNotNone(visitor.checked_in_at)
