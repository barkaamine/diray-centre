
import os
import django
import sys
from datetime import datetime, timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Project.settings')
django.setup()

from django.contrib.auth.models import User
from diray.models import Profile, StudentProfile, ProfessorProfile, Session, Training, RecordedVideo

def run_verification():
    print("Beginning Verification...")
    
    # 1. Clean up previous test data if exists
    try:
        User.objects.filter(username='test_student').delete()
        User.objects.filter(username='test_professor').delete()
        print("Cleaned up old test users.")
    except Exception as e:
        print(f"Cleanup warning: {e}")

    # 2. Test Student Creation
    try:
        student_user = User.objects.create_user(username='test_student', email='student@test.com', password='password123')
        print(f"Student User created: {student_user}")
        
        # Check Profile Signal
        profile = Profile.objects.get(user=student_user)
        print(f"Profile created automatically: {profile}")
        
        # Update Profile
        profile.role = 'STUDENT'
        profile.full_name = 'Test Student'
        profile.cin_or_passport = 'AB123456'
        profile.status = 'ACTIVE'
        profile.save()
        print("Profile updated successfully.")
        
        # Create StudentProfile
        student_profile = StudentProfile.objects.create(profile=profile)
        print("StudentProfile created.")
        
    except Exception as e:
        print(f"FAILED: Student creation error: {e}")
        return

    # 3. Test Professor Creation
    try:
        prof_user = User.objects.create_user(username='test_professor', email='prof@test.com', password='password123')
        prof_profile = prof_user.profile
        prof_profile.role = 'PROFESSOR'
        prof_profile.full_name = 'Dr. Professor'
        prof_profile.cin_or_passport = 'XY987654' # MUST BE UNIQUE
        prof_profile.save()
        
        professor_profile = ProfessorProfile.objects.create(profile=prof_profile)
        print("ProfessorProfile created.")
        
    except Exception as e:
        print(f"FAILED: Professor creation error: {e}")
        return

    # 4. Test Session Creation
    try:
        # Get or create a training
        training, _ = Training.objects.get_or_create(
            title="Test Training",
            slug="test-training",
            price_mad=1000,
            duration_days=5
        )
        
        session = Session.objects.create(
            training=training,
            city="Casablanca",
            professor=professor_profile,
            start_datetime=datetime.now(),
            end_datetime=datetime.now() + timedelta(hours=2),
            is_live=True
        )
        print(f"Session created: {session}")
        
        # Assign session to student
        student_profile.sessions_access.add(session)
        print("Session assigned to student.")
        
    except Exception as e:
         print(f"FAILED: Session creation error: {e}")
         return

    print("VERIFICATION SUCCESSFUL!")

if __name__ == '__main__':
    run_verification()
