# urls.py - FIXED
from django.urls import path
from . import views

app_name = "diray"

urlpatterns = [
    # Main pages
    path("", views.home, name="home"),
    path("formations/", views.training_catalog, name="training_catalog"),
    path("formations/<slug:slug>/", views.training_detail, name="training_detail"),
    path("migration/", views.migration_services, name="migration_services"),
    path("centres-contact/", views.contact_centers, name="contact_centers"),
    
    # API endpoints
    path("api/contact/", views.submit_contact_request, name="submit_contact_request"),
    path("api/review/", views.submit_review, name="submit_review"),
    path("api/waitlist/", views.join_waitlist, name="join_waitlist"),
    path("api/update-currency/", views.update_currency, name="update_currency"),
    path("api/currency-rates/", views.get_currency_rates_api, name="get_currency_rates"),
    path("api/track-click/", views.track_click_event, name="track_click_event"),
    path("api/track-call/", views.track_phone_call, name="track_phone_call"),
    path("api/track-whatsapp/", views.track_whatsapp_click, name="track_whatsapp_click"),
    path("api/training/<int:training_id>/reviews/", views.get_training_reviews, name="get_training_reviews"),
    path("api/review/helpful/", views.mark_review_helpful, name="mark_review_helpful"),
    path("api/dashboard/updates/", views.check_updates_ajax, name="check_updates_ajax"),
    
    # New endpoints - FIXED: removed slug parameter
    path('api/pre-subscribe/', views.create_pre_subscription, name='create_pre_subscription'),
    path('api/subscribe-promotion/', views.subscribe_promotion, name='subscribe_promotion'),
    
    # Auth
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('mon-espace/', views.dashboard, name='dashboard'),
    path('mon-emploi-du-temps/', views.student_schedule, name='student_schedule'),
    path('mon-profil/', views.student_profile, name='student_profile'),
    path('api/profile/upload-picture/', views.upload_profile_picture, name='upload_profile_picture'),
    
    # Classroom
    path('classroom/<slug:training_slug>/', views.classroom, name='classroom'),
    path('classroom/<slug:training_slug>/video/<int:video_id>/', views.classroom, name='classroom_video'),
    
    # Live Sessions
    path('live/<int:stream_id>/', views.live_session, name='live_session'),
    path('professor/sessions/start-live/<int:session_id>/', views.start_live_stream, name='start_live_stream'),
    path('professor/live/end/<int:stream_id>/', views.end_live_stream, name='end_live_stream'),
    path('professor/session/update/<int:session_id>/', views.update_session_status, name='update_session_status'),
    path('account-status/', views.account_status, name='account_status'),
    path('api/attendance/heartbeat/<int:stream_id>/', views.attendance_heartbeat, name='attendance_heartbeat'),
    
    # Recorded Videos
    path('videos/<slug:training_slug>/', views.recorded_videos_list, name='recorded_videos_list'),
    
    # Professor Dashboard
    path('professor/', views.professor_dashboard, name='professor_dashboard'),
    path('professor/students/', views.professor_students, name='professor_students'),
    path('professor/sessions/', views.professor_sessions, name='professor_sessions'),
    path('professor/sessions/manage/', views.professor_sessions, name='manage_sessions'), # Alias for compatibility
    path('professor/sessions/add-seance/', views.add_seance, name='add_seance'),
    path('professor/comments/', views.professor_comments, name='professor_comments'),
    path('assistant/', views.assistant_dashboard, name='assistant_dashboard'),
    path('api/assistant/create-entity/', views.create_entity_ajax, name='create_entity_ajax'),
    path('api/student/<int:student_id>/toggle-status/', views.toggle_student_status, name='toggle_student_status'),
    path('api/assistant/assign-training/', views.assistant_assign_training, name='assistant_assign_training'),
    path('api/assistant/assign-session/', views.assistant_assign_session, name='assistant_assign_session'),
    path('api/assistant/create-session/', views.assistant_create_session, name='assistant_create_session'),
    path('director/', views.director_dashboard, name='director_dashboard'),
    
    # Notifications
    path('notifications/read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('professor/sessions/<int:session_id>/notify/', views.send_session_notification, name='send_session_notification'),
]
