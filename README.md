# 🏢 Hostel Management System

A comprehensive Django-based web application for managing hostel operations efficiently.

## ✨ Features

### 🎓 Student Features
- **Dashboard**: Overview of room, complaints, fees, and attendance
- **Complaint Management**: Submit and track complaints with priority levels
- **Fee Management**: View and track hostel fees with payment history
- **Visitor Management**: Request and manage visitor approvals
- **Leave Applications**: Apply for leaves with dates and reasons
- **Announcements**: View hostel announcements and events
- **Profile Management**: Maintain personal information and documents
- **Room Rating**: Provide feedback on room conditions

### 👮 Warden Features
- **Complaint Dashboard**: View, assign, and resolve pending complaints
- **Leave Approval**: Approve or reject leave applications
- **Visitor Approval**: Manage visitor requests
- **Attendance Management**: Track student attendance
- **Maintenance Requests**: Manage room maintenance issues
- **Announcements**: Post hostel announcements and notices
- **Events Management**: Create and manage hostel events
- **Reports**: Generate operational reports

### 👨‍💼 Admin Features
- **Full Access**: All management capabilities
- **User Management**: Create, edit, and manage all user accounts
- **Role Management**: Assign roles and permissions
- **Room Management**: Manage rooms, allocations, and conditions
- **Financial Reports**: View comprehensive fee and payment reports
- **System Configuration**: Configure hostel parameters

## 🛠 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- Git

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd "Hostel-Management-System"
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Setup Environment Variables
```bash
cp .env.example .env
# Edit .env with your settings
```

### Step 5: Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 6: Create Superuser (Admin)
```bash
python manage.py createsuperuser
```

### Step 7: Run Development Server
```bash
python manage.py runserver
```

Access the application at: `http://localhost:8000/login/`

## 📊 Database Models

### Users & Profiles
- **CustomUser**: Extended Django user with role-based system
- **StudentProfile**: Student-specific information and documents
- **WardenProfile**: Warden assignment and details

### Room Management
- **Room**: Physical room information (number, floor, capacity, amenities)
- **RoomAllocation**: Student-to-room assignment tracking
- **RoomConditionReport**: Room inspection and maintenance status

### Operations
- **Complaint**: Issue reporting with priority and category
- **Attendance**: Daily attendance tracking
- **Fee**: Hostel fee management with multiple fee types
- **Visitor**: Guest visit tracking and approval
- **LeaveApplication**: Leave request management
- **MaintenanceRequest**: Maintenance issue tracking
- **Announcement**: Hostel-wide announcements
- **Event**: Hostel events and activities
- **RoomRating**: Student feedback on rooms

## 🔐 Security Features

✅ Password strength validation (minimum 8 characters)
✅ CSRF protection on all forms
✅ XSS protection in templates
✅ Role-based access control (RBAC)
✅ Session management with timeout
✅ Environment variable configuration
✅ SQL injection prevention (Django ORM)
✅ Secure password hashing (bcrypt/PBKDF2)
✅ Account lockout mechanism ready
✅ Audit logging capability

## 🎨 UI/UX Highlights

- **Modern Bootstrap 5 Design**: Responsive and mobile-friendly
- **Dark Theme Support**: Comfortable for extended use
- **Interactive Dashboards**: Real-time statistics and metrics
- **Data Tables**: Sortable and filterable lists
- **Modal Dialogs**: Smooth confirmations and interactions
- **Toast Notifications**: User feedback on actions
- **Font Awesome Icons**: Professional iconography
- **Smooth Animations**: Enhance user experience
- **Accessibility**: WCAG compliant

## 📱 Responsive Design

- ✅ Desktop (1920px and above)
- ✅ Laptop (1440px - 1919px)
- ✅ Tablet (768px - 1439px)
- ✅ Mobile (320px - 767px)

## 🚀 Unique & Advanced Features

1. **Smart Room Allocation**: Based on student preferences
2. **Visitor Management System**: Complete tracking with ID verification
3. **Leave & Gate Pass System**: Automated approval workflow
4. **Maintenance Request Tracking**: Priority-based assignment
5. **Financial Analytics**: Fee collection reports and insights
6. **Room Condition Reports**: Regular inspection tracking
7. **Event Calendar**: Hostel events and dates
8. **Rating System**: Student feedback on facilities
9. **Document Management**: Upload and store important documents
10. **Multi-level Notifications**: Alerts for important events

## 📝 User Roles & Permissions

### Student
- View dashboard
- Submit complaints
- Apply for leave
- Request visitors
- View fees
- Rate rooms
- Upload documents
- View announcements

### Warden
- View all complaints
- Approve/reject leaves
- Approve visitors
- Mark attendance
- Create announcements
- Manage events
- Track maintenance

### Admin
- Full system access
- User management
- Room allocation
- Financial reports
- System configuration

## 🐛 Known Issues & Fixes

### Fixed Issues ✅
- ✅ Missing URL configurations
- ✅ Incomplete form validation
- ✅ No permission decorators
- ✅ Exposed SECRET_KEY
- ✅ Limited error handling
- ✅ No audit logging

### Future Enhancements 🚧
- [ ] REST API with Django REST Framework
- [ ] Real-time notifications (WebSockets)
- [ ] Email/SMS integration
- [ ] Export to PDF/Excel
- [ ] Advanced analytics dashboard
- [ ] Mobile app (React Native)
- [ ] Two-factor authentication
- [ ] Room occupancy visualization

## 📧 API Endpoints (Future)

```
GET    /api/complaints/          - List all complaints
POST   /api/complaints/          - Create new complaint
GET    /api/complaints/{id}/     - Get complaint details
PATCH  /api/complaints/{id}/     - Update complaint

GET    /api/fees/                - List student fees
GET    /api/students/            - List all students
GET    /api/rooms/               - List all rooms
GET    /api/announcements/       - List announcements
```

## 🧪 Testing

To run tests:
```bash
python manage.py test
```

## 📊 Admin Panel

Access Django admin at: `http://localhost:8000/admin/`

Manage:
- Users and permissions
- Rooms and allocations
- Complaints and maintenance
- Fees and payments
- Announcements and events

## 🌐 Deployment Checklist

- [ ] Set DEBUG = False
- [ ] Update SECRET_KEY in environment
- [ ] Configure ALLOWED_HOSTS
- [ ] Setup HTTPS/SSL
- [ ] Configure database (PostgreSQL recommended)
- [ ] Setup static files collection
- [ ] Configure email backend
- [ ] Setup logging
- [ ] Enable CSRF protection
- [ ] Configure CORS if needed

## 📞 Support & Documentation

- **Django Documentation**: https://docs.djangoproject.com/
- **Bootstrap Documentation**: https://getbootstrap.com/docs/
- **Django Models**: See `accounts/models.py`, `operations/models.py`, `core/models.py`
- **Views Documentation**: See `accounts/views.py`

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please follow these steps:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 👥 Team

Developed with ❤️ for hostel management.

## 📞 Contact

For issues, questions, or suggestions, please open an issue on GitHub.

---

**Last Updated**: 2024
**Version**: 2.0.0
**Status**: Active Development ✨
