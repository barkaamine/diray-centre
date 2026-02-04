from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import (
    Profile, StudentProfile, ProfessorProfile, AssistantProfile, City,
    Session, RecordedVideo, LiveRecording,
    AttendanceLog, VideoProgress, Question, Live, Training,
    ContactRequest, DailyStat, CurrencyRate, TrainingWaitlist,
    TrainingReview, ThreatIP, RateLimitLog, FormSubmission,
    VisitorSession, PageView, WhatsAppClick, Notification, Seance
)

# ========== INLINES FOR CONSOLIDATED MANAGEMENT ==========

class RecordedVideoInline(admin.TabularInline):
    model = RecordedVideo
    extra = 1
    fields = ('title', 'video_provider', 'video_id', 'is_active')

class SessionInline(admin.TabularInline):
    model = Session.formations.through
    extra = 1

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    readonly_fields = ('student', 'content', 'created_at')
    fields = ('student', 'content', 'is_answered', 'is_deleted')

class AttendanceLogInline(admin.TabularInline):
    model = AttendanceLog
    extra = 0
    readonly_fields = ('student', 'live_stream', 'join_time', 'leave_time', 'duration_seconds')
    can_delete = False

class SeanceInline(admin.TabularInline):
    model = Seance
    extra = 0
    fields = ('title', 'type', 'date', 'time', 'location')

# ========== UPDATED ADMIN CLASSES ==========

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    
    def has_module_permission(self, request):
        if not request.user.is_superuser and hasattr(request.user.profile, 'assistant_profile'):
            return False 
        return super().has_module_permission(request)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    list_editable = ('is_read',)
    search_fields = ('title', 'message', 'user__username')
    
    def has_module_permission(self, request):
        if not request.user.is_superuser and hasattr(request.user.profile, 'assistant_profile'):
            return False
        return super().has_module_permission(request)

@admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
    list_display = ('title', 'price_mad', 'duration_days', 'get_student_count', 'is_active', 'is_featured')
    list_filter = ('is_active', 'is_featured', 'badge')
    list_editable = ('is_active', 'is_featured')
    search_fields = ('title', 'slug', 'description')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [RecordedVideoInline, SessionInline]

    def get_student_count(self, obj):
        return obj.students.count()
    get_student_count.short_description = 'Students'

@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone', 'request_type', 'status', 'payment_status', 'submitted_at')
    list_filter = ('request_type', 'status', 'payment_status', 'is_threat')
    list_editable = ('status', 'payment_status')
    search_fields = ('full_name', 'email', 'phone', 'training_title')
    readonly_fields = ('submitted_at', 'ip_address', 'user_agent', 'session_id')

@admin.register(TrainingWaitlist)
class TrainingWaitlistAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'training', 'city', 'notified', 'created_at')
    list_filter = ('notified', 'training', 'city')
    list_editable = ('notified',)
    search_fields = ('full_name', 'email', 'phone')

@admin.register(TrainingReview)
class TrainingReviewAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'training', 'rating', 'is_verified', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_verified', 'is_approved', 'training')
    list_editable = ('is_verified', 'is_approved')
    search_fields = ('full_name', 'email', 'title', 'comment')

@admin.register(DailyStat)
class DailyStatAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_visitors', 'total_pageviews', 'total_form_submissions')
    date_hierarchy = 'date'

@admin.register(CurrencyRate)
class CurrencyRateAdmin(admin.ModelAdmin):
    list_display = ('currency_code', 'currency_name', 'rate_to_mad', 'last_updated')
    list_editable = ('rate_to_mad',)
    search_fields = ('currency_code', 'currency_name')

@admin.register(ThreatIP)
class ThreatIPAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'threat_level', 'request_count', 'is_blocked', 'last_detected')
    list_filter = ('threat_level', 'is_blocked')
    list_editable = ('is_blocked', 'threat_level')
    search_fields = ('ip_address', 'reason')

@admin.register(RateLimitLog)
class RateLimitLogAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'endpoint', 'request_count', 'last_request', 'is_threat')
    list_filter = ('is_threat',)
    search_fields = ('ip_address', 'endpoint')

@admin.register(FormSubmission)
class FormSubmissionAdmin(admin.ModelAdmin):
    list_display = ('form_type', 'training_title', 'city', 'timestamp')
    list_filter = ('form_type', 'city')
    search_fields = ('training_title', 'ip_address')

@admin.register(VisitorSession)
class VisitorSessionAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'city', 'device_type', 'browser', 'page_views', 'start_time')
    list_filter = ('device_type', 'browser', 'city')
    search_fields = ('session_id', 'ip_address')

@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    list_display = ('url', 'page_title', 'city', 'device_type', 'timestamp')
    list_filter = ('device_type', 'city')
    search_fields = ('url', 'page_title', 'session_id')

@admin.register(WhatsAppClick)
class WhatsAppClickAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'city', 'timestamp')
    list_filter = ('city',)
    search_fields = ('phone_number', 'ip_address')

# Inline for Profile (used in UserAdmin)
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'
    fields = ('role', 'status', 'full_name', 'cin_or_passport', 'phone_number', 'city')

# Inline for StudentProfile
class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    can_delete = False
    verbose_name_plural = 'Student Profile'
    fk_name = 'profile'
    filter_horizontal = ('authorized_formations',)

# Inline for AssistantProfile
class AssistantProfileInline(admin.StackedInline):
    model = AssistantProfile
    can_delete = False
    verbose_name_plural = 'Assistant Profile'
    fk_name = 'profile'

# Inline for ProfessorProfile
class ProfessorProfileInline(admin.StackedInline):
    model = ProfessorProfile
    can_delete = False
    verbose_name_plural = 'Professor Profile'
    fk_name = 'profile'

# Custom User Admin
class UserAdmin(BaseUserAdmin):
    def get_inlines(self, request, obj=None):
        if obj:
            return (ProfileInline,)
        return ()
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role', 'get_status', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'profile__role', 'profile__status')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'profile__full_name', 'profile__phone_number')
    
    def get_role(self, obj):
        try:
            return obj.profile.get_role_display()
        except:
            return '-'
    get_role.short_description = 'Role'
    
    def get_status(self, obj):
        try:
            return obj.profile.get_status_display()
        except:
            return '-'
    get_status.short_description = 'Status'

# Profile Admin
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'role', 'status', 'phone_number', 'city')
    list_filter = ('role', 'status', 'city')
    list_editable = ('status', 'role')
    search_fields = ('full_name', 'cin_or_passport', 'phone_number', 'user__email')
    
    def has_module_permission(self, request):
        if not request.user.is_superuser and hasattr(request.user.profile, 'assistant_profile'):
            return False
        return super().has_module_permission(request)
    
    def get_inlines(self, request, obj=None):
        if obj and obj.role == 'STUDENT':
            return [StudentProfileInline]
        elif obj and obj.role == 'PROFESSOR':
            return [ProfessorProfileInline]
        elif obj and obj.role == 'ASSISTANT':
            return [AssistantProfileInline]
        return []

# StudentProfile Admin
@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('profile', 'get_full_name', 'amount_paid', 'total_amount_due', 'get_formations_count', 'get_session_info')
    filter_horizontal = ('authorized_formations',)
    search_fields = ('profile__full_name', 'profile__user__email', 'profile__cin_or_passport')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request).filter(profile__role='STUDENT')
        if not request.user.is_superuser and hasattr(request.user.profile, 'assistant_profile'):
            assistant = request.user.profile.assistant_profile
            qs = qs.filter(profile__city__in=assistant.assigned_cities.all())
        return qs
    
    def has_module_permission(self, request):
        if not request.user.is_superuser and hasattr(request.user.profile, 'assistant_profile'):
            return True # Students are allowed
        return super().has_module_permission(request)
    
    def get_full_name(self, obj):
        return obj.profile.full_name
    get_full_name.short_description = 'Full Name'
    
    def get_formations_count(self, obj):
        return obj.authorized_formations.count()
    get_formations_count.short_description = 'Formations'
    
    def get_session_info(self, obj):
        return obj.session
    get_session_info.short_description = 'Session'
    
    actions = ['enroll_in_all_formations']
    
    def enroll_in_all_formations(self, request, queryset):
        all_trainings = Training.objects.filter(is_active=True)
        for student in queryset:
            student.authorized_formations.add(*all_trainings)
        self.message_user(request, f"{queryset.count()} student(s) enrolled in all active formations.")
    enroll_in_all_formations.short_description = "Enroll selected students in all formations"

# ProfessorProfile Admin
@admin.register(ProfessorProfile)
class ProfessorProfileAdmin(admin.ModelAdmin):
    list_display = ('profile', 'get_full_name', 'specialization', 'bio')
    search_fields = ('profile__full_name', 'specialization')
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(profile__role='PROFESSOR')
    
    def get_full_name(self, obj):
        return obj.profile.full_name
    get_full_name.short_description = 'Full Name'

# AssistantProfile Admin
@admin.register(AssistantProfile)
class AssistantProfileAdmin(admin.ModelAdmin):
    list_display = ('profile', 'get_full_name', 'get_cities')
    search_fields = ('profile__full_name',)
    filter_horizontal = ('assigned_cities',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(profile__role='ASSISTANT')
    
    def get_full_name(self, obj):
        return obj.profile.full_name
    get_full_name.short_description = 'Full Name'
    
    def get_cities(self, obj):
        return ", ".join([c.name for c in obj.assigned_cities.all()])
    get_cities.short_description = 'Villes Assignées'

# Session Admin
@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('get_formations', 'professor', 'start_date', 'city', 'is_live', 'is_active', 'status')
    list_filter = ('is_live', 'is_active', 'city', 'start_date', 'status')
    list_editable = ('is_active', 'status', 'is_live')
    search_fields = ('formations__title', 'professor__profile__full_name')
    date_hierarchy = 'start_date'
    filter_horizontal = ('formations',)
    inlines = [SeanceInline, AttendanceLogInline]
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request.user.profile, 'assistant_profile'):
            assistant = request.user.profile.assistant_profile
            qs = qs.filter(city__in=assistant.assigned_cities.all())
        return qs

    def has_module_permission(self, request):
        if not request.user.is_superuser and hasattr(request.user.profile, 'assistant_profile'):
            return True # Sessions are allowed
        return super().has_module_permission(request)

    def get_formations(self, obj):
        return ", ".join([t.title for t in obj.formations.all()])
    get_formations.short_description = 'Formations'

    fieldsets = (
        ('Basic Info', {
            'fields': ('formations', 'professor', 'city')
        }),
        ('Schedule', {
            'fields': ('start_date', 'end_date')
        }),
        ('Type & Status', {
            'fields': ('is_live', 'is_active', 'status')
        }),
    )

@admin.register(Seance)
class SeanceAdmin(admin.ModelAdmin):
    list_display = ('title', 'session', 'type', 'date', 'time', 'location')
    list_filter = ('type', 'date', 'session')
    search_fields = ('title', 'location', 'session__formations__title')

# RecordedVideo Admin
@admin.register(RecordedVideo)
class RecordedVideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'training', 'duration_seconds', 'video_provider', 'is_active', 'created_at')
    list_filter = ('video_provider', 'is_active', 'training')
    list_editable = ('is_active',)
    search_fields = ('title', 'training__title')
    date_hierarchy = 'created_at'
    inlines = [QuestionInline]
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'training', 'description')
        }),
        ('Video Details', {
            'fields': ('video_provider', 'video_id', 'duration_seconds')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )

# LiveRecording Admin
@admin.register(LiveRecording)
class LiveRecordingAdmin(admin.ModelAdmin):
    list_display = ('session', 'recording_url', 'duration_seconds', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('session__trainings__title',)
    date_hierarchy = 'created_at'

# AttendanceLog Admin
@admin.register(AttendanceLog)
class AttendanceLogAdmin(admin.ModelAdmin):
    list_display = ('student', 'session', 'join_time', 'leave_time', 'duration_minutes')
    list_filter = ('session__formations', 'join_time')
    search_fields = ('student__full_name', 'session__formations__title')
    date_hierarchy = 'join_time'
    
    def duration_minutes(self, obj):
        if obj.leave_time:
            delta = obj.leave_time - obj.join_time
            return f"{delta.total_seconds() / 60:.0f} min"
        return "Still in session"
    duration_minutes.short_description = 'Duration'

# VideoProgress Admin
@admin.register(VideoProgress)
class VideoProgressAdmin(admin.ModelAdmin):
    list_display = ('student', 'video', 'watched_seconds', 'completed', 'last_watched_at')
    list_filter = ('completed', 'video__training')
    search_fields = ('student__full_name', 'video__title')
    date_hierarchy = 'last_watched_at'

# Question Admin
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('student', 'video', 'text_preview', 'is_answered', 'is_deleted', 'created_at')
    list_filter = ('created_at', 'video__training', 'is_answered', 'is_deleted')
    list_editable = ('is_answered', 'is_deleted')
    search_fields = ('student__profile__full_name', 'content', 'video__title')
    date_hierarchy = 'created_at'
    
    def text_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    text_preview.short_description = 'Question'

# Re-register User with custom admin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Customize admin site
admin.site.site_header = "Diray E-Learning Administration"
admin.site.site_title = "Diray Admin"
admin.site.index_title = "Welcome to Diray E-Learning Admin"

# ========== CUSTOM ADMIN ORDERING ==========

def get_app_list(self, request, app_label=None):
    """
    Override the default get_app_list to provide a custom ordering
    for models within the admin site.
    """
    app_dict = self._build_app_dict(request, app_label)
    
    # Define desired order index for models
    # Lower value = appears higher
    order_index = {
        # Auth & Users
        'User': 1,
        'Group': 2,
        'Profile': 3,
        'StudentProfile': 4,
        'ProfessorProfile': 5,
        'AssistantProfile': 6,
        
        # E-Learning Core
        'Training': 10,
        'Session': 11,
        'RecordedVideo': 12,
        'LiveRecording': 13,
        
        # Activity & Interaction
        'Question': 15,
        'AttendanceLog': 16,
        'VideoProgress': 17,
        'Notification': 18,
        
        # CRM & Sales
        'ContactRequest': 20,
        'TrainingWaitlist': 21,
        'TrainingReview': 22,
        'FormSubmission': 23,
        'WhatsAppClick': 24,
        
        # Analytics
        'DailyStat': 30,
        'VisitorSession': 31,
        'PageView': 32,
        'ClickEvent': 33,
        'PhoneCall': 34,
        
        # Config & Infrastructure
        'City': 40,
        'CurrencyRate': 41,
        
        # Security
        'ThreatIP': 50,
        'RateLimitLog': 51,
    }

    # Sort the apps alphabetically first
    app_list = sorted(app_dict.values(), key=lambda x: x['name'].lower())

    # Reorder models within each app according to our index
    for app in app_list:
        app['models'].sort(key=lambda x: order_index.get(x['object_name'], 100))

    return app_list

# Apply the override to the default AdminSite class
admin.AdminSite.get_app_list = get_app_list
