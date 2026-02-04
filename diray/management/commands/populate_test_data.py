from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.db import IntegrityError
from diray.models import (
    Profile, StudentProfile, ProfessorProfile, Training,
    Session, RecordedVideo, VideoProgress, Comment
)


class Command(BaseCommand):
    help = 'Populate database with test data for E-Learning platform'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting to populate database...'))
        
        # Create Professors
        self.stdout.write('Setting up professors...')
        prof_data = [
            ('prof_ahmed', 'ahmed@diray.com', 'Ahmed', 'Benali', 'Électricité Bâtiment', 'Expert en électricité avec 15 ans d\'expérience', 'Casablanca'),
            ('prof_fatima', 'fatima@diray.com', 'Fatima', 'Zahra', 'Plomberie', 'Spécialiste en plomberie et sanitaire', 'Rabat'),
        ]
        
        professors = []
        for username, email, first, last, spec, bio, city in prof_data:
            try:
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={'email': email, 'first_name': first, 'last_name': last}
                )
                if created:
                    user.set_password('password123')
                    user.save()
                
                profile, _ = Profile.objects.get_or_create(
                    user=user,
                    defaults={'full_name': f'{first} {last}', 'city': city}
                )
                
                profile.role = 'PROFESSOR'
                profile.status = 'ACTIVE'
                profile.full_name = f'{first} {last}'
                profile.phone_number = f'+2126{hash(username)%100000000:08d}'
                profile.city = city
                profile.save()
                
                prof, _ = ProfessorProfile.objects.get_or_create(
                    profile=profile,
                    defaults={'specialization': spec, 'bio': bio}
                )
                professors.append(prof)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating professor {username}: {str(e)}'))
        
        # Create Students
        self.stdout.write('Setting up students...')
        students = []
        student_data = [
            ('student1', 'Mohammed', 'Alami', 'mohammed@example.com', 'Casablanca', 'AB123456'),
            ('student2', 'Yasmine', 'Idrissi', 'yasmine@example.com', 'Rabat', 'CD789012'),
            ('student3', 'Omar', 'Tazi', 'omar@example.com', 'Marrakech', 'EF345678'),
            ('student4', 'Salma', 'Bennani', 'salma@example.com', 'Fès', 'GH901234'),
            ('student5', 'Karim', 'El Fassi', 'karim@example.com', 'Tanger', 'IJ567890'),
        ]
        
        for username, first, last, email, city, cin in student_data:
            try:
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={'email': email, 'first_name': first, 'last_name': last}
                )
                if created:
                    user.set_password('password123')
                    user.save()
                
                profile, _ = Profile.objects.get_or_create(
                    user=user,
                    defaults={'full_name': f'{first} {last}', 'city': city}
                )
                
                profile.role = 'STUDENT'
                profile.status = 'ACTIVE'
                profile.full_name = f'{first} {last}'
                # Check for CIN duplicates before saving
                if cin and Profile.objects.filter(cin_or_passport=cin).exclude(user=user).exists():
                    cin = f"{cin}_{hash(username)%100}"
                profile.cin_or_passport = cin
                profile.phone_number = f'+21261234{hash(username)%10000:04d}'
                profile.city = city
                profile.save()
                
                student_profile, _ = StudentProfile.objects.get_or_create(profile=profile)
                students.append(student_profile)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating student {username}: {str(e)}'))
        
        # Get existing trainings
        self.stdout.write('Setting up trainings access...')
        trainings = Training.objects.filter(is_active=True)
        if not trainings.exists():
            self.stdout.write(self.style.ERROR('No active trainings found. Please create some first.'))
            return
            
        trainings_list = list(trainings[:3])
        
        # Enroll students in trainings
        for student in students:
            student.formations_access.add(*trainings_list[:2])
        
        # Create Sessions
        self.stdout.write('Setting up sessions...')
        now = timezone.now()
        for i, training in enumerate(trainings_list[:2]):
            try:
                # Upcoming Live Session
                session, _ = Session.objects.get_or_create(
                    training=training,
                    is_live=True,
                    is_active=True,
                    defaults={
                        'professor': professors[i % len(professors)] if professors else None,
                        'start_datetime': now + timedelta(days=3),
                        'end_datetime': now + timedelta(days=3, hours=2),
                        'city': 'Rabat' if i % 2 == 0 else 'Casablanca'
                    }
                )
                # Add students to session via StudentProfile
                for student in students[:3]:
                    student.sessions_access.add(session)
            except Exception as e:
                 self.stdout.write(self.style.ERROR(f'Error creating session for {training.title}: {str(e)}'))
        
        # Create Recorded Videos
        self.stdout.write('Setting up recorded videos...')
        video_titles = [
            'Introduction à la formation',
            'Concepts fondamentaux et sécurité',
            'Outils et équipements',
            'Étude de cas pratique',
        ]
        
        videos = []
        for i, training in enumerate(trainings_list[:2]):
            for j, title in enumerate(video_titles):
                try:
                    video, _ = RecordedVideo.objects.get_or_create(
                        training=training,
                        title=f'{title} - {training.title}',
                        defaults={
                            'description': f'Contenu détaillé pour: {title}',
                            'video_provider': 'VDOCIPHER',
                            'video_id': f'vdo_sample_{training.id}_{j}',
                            'duration_seconds': 1200 + (j * 300),
                            'is_active': True
                        }
                    )
                    videos.append(video)
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error creating video {title}: {str(e)}'))
        
        # Create Progress and Comments for existing objects
        self.stdout.write('Setting up interactions...')
        for student in students[:2]:
            for video in videos[:3]:
                try:
                    # Progress
                    VideoProgress.objects.get_or_create(
                        student=student.profile,
                        video=video,
                        defaults={
                            'watched_seconds': 300,
                            'completed': False,
                            'last_watched_at': now
                        }
                    )
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error setting progress for {student.profile.full_name}: {str(e)}'))
                    
                try:
                    # Comment
                    Comment.objects.get_or_create(
                        user=student.profile,
                        video=video,
                        content=f"Très bonne vidéo sur {video.title}!",
                        defaults={'created_at': now}
                    )
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error creating comment for {student.profile.full_name}: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ Database populated/updated successfully!'))
        self.stdout.write(f'  - {len(professors)} Professors')
        self.stdout.write(f'  - {len(students)} Students')
        self.stdout.write(f'  - {Session.objects.count()} Sessions')
        self.stdout.write(f'  - {RecordedVideo.objects.count()} Videos')
        self.stdout.write(self.style.WARNING('\nTest credentials (password123):'))
        self.stdout.write('  - Professor: prof_ahmed')
        self.stdout.write('  - Student: student1')
