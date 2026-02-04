# views.py - UPDATED with rate limiting, threat detection, and optimized queries
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.db.models import Q, Count, F, Prefetch
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import transaction
import json
import requests
from datetime import datetime, timedelta
import logging
from django.db.models import Avg, Count, Sum  # Add this line
from .models import (
    Training, City, ContactRequest, CurrencyRate,
    PageView, ClickEvent, PhoneCall, WhatsAppClick,
    FormSubmission, VisitorSession, DailyStat,
    TrainingWaitlist, TrainingReview, ThreatIP, RateLimitLog,
    Profile, StudentProfile, ProfessorProfile, AssistantProfile, Session,
    RecordedVideo, LiveRecording, AttendanceLog, VideoProgress, Question,
    TrainingPreSubscription, Notification, Live, Seance
)
from .forms import ContactRequestForm, TrainingReviewForm, WaitlistForm, TrainingInquiryForm, MigrationInquiryForm, StudentRegistrationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .context_processors import get_client_ip, get_location_from_ip
from .api_client import get_api_client, SystemeCalculAPIError
import uuid
from django.conf import settings

from diray import models

from functools import wraps

def assistant_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.role in ['ASSISTANT', 'ADMIN']:
            return view_func(request, *args, **kwargs)
        messages.error(request, "Accès réservé aux assistants.")
        return redirect('diray:home')
    return _wrapped_view

def student_active_required(view_func):
    """Decorator to enforce ACTIVE status for students"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login') 
            
        if not hasattr(request.user, 'profile'):
            messages.error(request, "Profil introuvable.")
            return redirect('diray:home')
            
        profile = request.user.profile
        
        # If not a student (e.g. Professor/Admin), allow access (or let other decorators handle it)
        if profile.role != 'STUDENT':
            return view_func(request, *args, **kwargs)
            
        # Check Account Status
        if profile.status == 'SUSPENDED':
            return redirect('diray:account_status')
            
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def professor_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if hasattr(request.user, 'profile') and request.user.profile.role == 'PROFESSOR':
            return view_func(request, *args, **kwargs)
        messages.error(request, "Accès réservé aux professeurs.")
        return redirect('diray:home')
    return _wrapped_view

logger = logging.getLogger(__name__)

# ========== RATE LIMITING & THREAT DETECTION ==========

class RateLimiter:
    """Simple rate limiter with threat detection"""
    
    @staticmethod
    def check_rate_limit(ip_address, endpoint, limit=5, period_minutes=1):
        """
        Check if IP has exceeded rate limit
        Returns: (is_allowed, remaining_seconds)
        """
        one_minute_ago = timezone.now() - timedelta(minutes=period_minutes)
        
        # Count requests in the last minute
        request_count = RateLimitLog.objects.filter(
            ip_address=ip_address,
            endpoint=endpoint,
            last_request__gte=one_minute_ago
        ).count()
        
        # Log the request
        RateLimitLog.objects.create(
            ip_address=ip_address,
            endpoint=endpoint,
            period_minutes=period_minutes
        )
        
        # Check if limit exceeded
        if request_count >= limit:
            # Mark as potential threat
            threat_ip, created = ThreatIP.objects.get_or_create(
                ip_address=ip_address,
                defaults={
                    'reason': f'Rate limit exceeded on {endpoint}: {request_count+1} requests in {period_minutes} minute(s)',
                    'threat_level': 'high',
                }
            )
            
            if not created:
                threat_ip.increment_request_count()
                threat_ip.reason = f'Rate limit exceeded on {endpoint}: {threat_ip.request_count} total violations'
                threat_ip.save()
            
            return False, 60  # Wait 60 seconds
        
        return True, 0
    
    @staticmethod
    def is_ip_blocked(ip_address):
        """Check if IP is blocked"""
        return ThreatIP.objects.filter(
            ip_address=ip_address,
            is_blocked=True
        ).exists()







# Additional functionality
import uuid


@csrf_exempt
@require_POST
def mark_review_helpful(request):
    """Mark review as helpful or not helpful"""
    try:
        data = json.loads(request.body)
        review_id = data.get('review_id')
        is_helpful = data.get('is_helpful', True)
        
        review = TrainingReview.objects.get(id=review_id)
        
        if is_helpful:
            review.helpful_count += 1
        else:
            review.not_helpful_count += 1
        
        review.save()
        
        return JsonResponse({
            'success': True,
            'helpful_count': review.helpful_count,
            'not_helpful_count': review.not_helpful_count
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

# Helper function to get client IP
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip












@csrf_exempt
@require_POST
def subscribe_promotion(request):
    """Subscribe to promotion"""
    try:
        data = json.loads(request.body)
        
        # Create a demo subscription for promotion
        transaction_id = str(uuid.uuid4())
        
        return JsonResponse({
            'success': True,
            'message': 'Inscription à la promotion réussie',
            'subscription': {
                'transaction_id': transaction_id,
                'full_name': data.get('full_name', 'Client'),
                'paid_price': '3500',
                'currency_used': 'MAD',
                'receipt_url': f'/media/receipts/{transaction_id}.pdf'
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        })



# Helper function to get average rating
def get_training_avg_rating(training_id):
    """Calculate average rating for a training"""
    from django.db.models import Avg
    result = TrainingReview.objects.filter(
        training_id=training_id,
        is_approved=True
    ).aggregate(Avg('rating'))
    
    return result['rating__avg'] or 0


# views.py - UPDATED with avatar support for reviews
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.db.models import Q, Count, F, Prefetch
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import transaction
import json
import requests
from datetime import datetime, timedelta
import logging
from django.db.models import Avg, Count, Sum
from .models import (
    Training, City, ContactRequest, CurrencyRate,
    PageView, ClickEvent, PhoneCall, WhatsAppClick,
    FormSubmission, VisitorSession, DailyStat,
    TrainingWaitlist, TrainingReview, ThreatIP, RateLimitLog,
    CompanyBankAccount, TrainingPreSubscription
)
from .forms import ContactRequestForm, TrainingReviewForm, WaitlistForm, TrainingInquiryForm, MigrationInquiryForm
from .context_processors import get_client_ip, get_location_from_ip
import uuid

logger = logging.getLogger(__name__)

# ========== RATE LIMITING & THREAT DETECTION ==========

class RateLimiter:
    """Simple rate limiter with threat detection"""
    
    @staticmethod
    def check_rate_limit(ip_address, endpoint, limit=5, period_minutes=1):
        """
        Check if IP has exceeded rate limit
        Returns: (is_allowed, remaining_seconds)
        """
        one_minute_ago = timezone.now() - timedelta(minutes=period_minutes)
        
        # Count requests in the last minute
        request_count = RateLimitLog.objects.filter(
            ip_address=ip_address,
            endpoint=endpoint,
            last_request__gte=one_minute_ago
        ).count()
        
        # Log the request
        RateLimitLog.objects.create(
            ip_address=ip_address,
            endpoint=endpoint,
            period_minutes=period_minutes
        )
        
        # Check if limit exceeded
        if request_count >= limit:
            # Mark as potential threat
            threat_ip, created = ThreatIP.objects.get_or_create(
                ip_address=ip_address,
                defaults={
                    'reason': f'Rate limit exceeded on {endpoint}: {request_count+1} requests in {period_minutes} minute(s)',
                    'threat_level': 'high',
                }
            )
            
            if not created:
                threat_ip.increment_request_count()
                threat_ip.reason = f'Rate limit exceeded on {endpoint}: {threat_ip.request_count} total violations'
                threat_ip.save()
            
            return False, 60  # Wait 60 seconds
        
        return True, 0
    
    @staticmethod
    def is_ip_blocked(ip_address):
        """Check if IP is blocked"""
        return ThreatIP.objects.filter(
            ip_address=ip_address,
            is_blocked=True
        ).exists()

# ========== CACHING FUNCTIONS ==========

def get_cached_featured_trainings():
    """Get featured trainings from cache or database"""
    cache_key = 'featured_trainings'
    featured_trainings = cache.get(cache_key)
    
    if featured_trainings is None:
        featured_trainings = Training.objects.filter(
            is_active=True,
            is_featured=True
        ).select_related(None).only(
            'id', 'title', 'slug', 'short_description', 'price_mad',
            'duration_days', 'success_rate', 'max_students', 'badge',
            'thumbnail', 'category_caces', 'category_electricite',
            'category_soudage', 'category_securite', 'category_management'
        ).order_by('-created_at')[:4]
        
        # Convert to list to cache properly
        featured_trainings = list(featured_trainings)
        cache.set(cache_key, featured_trainings, 1800)  # 30 minutes
    
    return featured_trainings

def get_cached_currency_rates():
    """Get currency rates from cache or database"""
    cache_key = 'currency_rates'
    rates = cache.get(cache_key)
    
    if rates is None:
        rates = {}
        db_rates = CurrencyRate.objects.all()
        for rate in db_rates:
            rates[rate.currency_code] = float(rate.rate_to_mad)
        
        if not rates:
            rates = {
                'MAD': 1.0,
                'EUR': 0.093,
                'USD': 0.100,
                'GBP': 0.079,
                'CAD': 0.136,
                'AED': 0.367,
            }
        
        cache.set(cache_key, rates, 3600)  # 1 hour
    
    return rates

def get_cached_categories(trainings):
    """Get categories from cache or calculate"""
    cache_key = f'categories_{hash(str([t.id for t in trainings]))}'
    categories = cache.get(cache_key)
    
    if categories is None:
        categories = []
        category_data = {
            'caces': {'id': 'caces', 'name': 'CACES Engins', 'icon': 'construction', 'active_count': 0},
            'electricite': {'id': 'electricite', 'name': 'Électricité', 'icon': 'bolt', 'active_count': 0},
            'soudage': {'id': 'soudage', 'name': 'Soudage', 'icon': 'whatshot', 'active_count': 0},
            'securite': {'id': 'securite', 'name': 'Sécurité', 'icon': 'security', 'active_count': 0},
            'management': {'id': 'management', 'name': 'Management', 'icon': 'groups', 'active_count': 0},
            'autre': {'id': 'autre', 'name': 'Autre', 'icon': 'category', 'active_count': 0},
        }
        
        for training in trainings:
            if training.category_caces: category_data['caces']['active_count'] += 1
            if training.category_electricite: category_data['electricite']['active_count'] += 1
            if training.category_soudage: category_data['soudage']['active_count'] += 1
            if training.category_securite: category_data['securite']['active_count'] += 1
            if training.category_management: category_data['management']['active_count'] += 1
            if training.category_autre: category_data['autre']['active_count'] += 1
        
        for cat_id, cat_data in category_data.items():
            if cat_data['active_count'] > 0:
                categories.append(cat_data)
        
        cache.set(cache_key, categories, 900)  # 15 minutes
    
    return categories

# ========== ANALYTICS TRACKING ==========

def track_page_view(request, page_title=''):
    """Track page view for analytics"""
    try:
        session_id = request.session.session_key
        if not session_id:
            request.session.create()
            session_id = request.session.session_key
        
        ip_address = get_client_ip(request)
        user_location = get_location_from_ip(ip_address)
        
        # Check if IP is blocked
        if RateLimiter.is_ip_blocked(ip_address):
            logger.warning(f"Blocked IP tried to access page: {ip_address}")
            return
        
        # Track visitor session
        visitor_session, created = VisitorSession.objects.get_or_create(
            session_id=session_id,
            defaults={
                'ip_address': ip_address,
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'city': user_location.get('city', ''),
                'country': user_location.get('country', ''),
                'device_type': 'desktop',
                'landing_page': request.path,
                'referrer': request.META.get('HTTP_REFERER', '')
            }
        )
        
        if not created:
            visitor_session.page_views += 1
            visitor_session.last_activity = timezone.now()
            visitor_session.save()
        
        # Track page view
        PageView.objects.create(
            url=request.path,
            page_title=page_title,
            referrer=request.META.get('HTTP_REFERER', ''),
            session_id=session_id,
            ip_address=ip_address,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            city=user_location.get('city', ''),
            country=user_location.get('country', ''),
            device_type='desktop'
        )
        
    except Exception as e:
        logger.error(f"Error tracking page view: {e}")

def home(request):
    """Home page view with optimized queries"""
    track_page_view(request, "Accueil - Diray Centre")
    
    # Get featured trainings from cache or database
    featured_trainings = cache.get('featured_trainings')
    
    if featured_trainings is None:
        featured_trainings = Training.objects.filter(
            is_active=True,
            is_featured=True
        ).only(
            'id', 'title', 'slug', 'short_description', 'price_mad',
            'duration_days', 'success_rate', 'max_students', 'badge',
            'thumbnail'
        ).order_by('-created_at')[:4]
        
        # If no featured trainings, get recent active ones
        if not featured_trainings:
            featured_trainings = Training.objects.filter(
                is_active=True
            ).only(
                'id', 'title', 'slug', 'short_description', 'price_mad',
                'duration_days', 'success_rate', 'max_students', 'badge',
                'thumbnail'
            ).order_by('-created_at')[:4]
        
        cache.set('featured_trainings', featured_trainings, 1800)  # 30 minutes
    
    # Get user location
    ip_address = get_client_ip(request)
    user_location = get_location_from_ip(ip_address)
    
    # Get currency rates from cache
    currency_rates = cache.get('currency_rates')
    if currency_rates is None:
        currency_rates = {}
        try:
            db_rates = CurrencyRate.objects.all()
            for rate in db_rates:
                currency_rates[rate.currency_code] = float(rate.rate_to_mad)
        except:
            currency_rates = {'MAD': 1.0, 'EUR': 0.093, 'USD': 0.100, 'GBP': 0.079}
        cache.set('currency_rates', currency_rates, 3600)
    
    # Get preferred currency
    preferred_currency = request.session.get('preferred_currency', 'MAD')
    
    # Prepare training data
    for training in featured_trainings:
        training.price_mad_float = float(training.price_mad)
        training.price_in_preferred = float(training.get_price_in_currency(preferred_currency))
    
    context = {
        'featured_trainings': featured_trainings,
        'user_location': user_location,
        'currency_rates': currency_rates,
        'preferred_currency': preferred_currency,
    }
    
    return render(request, "diray/home.html", context)

def training_catalog(request):
    """Training catalog view with optimized queries"""
    track_page_view(request, "Catalogue des formations")
    
    # Check rate limit
    ip_address = get_client_ip(request)
    allowed, wait_time = RateLimiter.check_rate_limit(ip_address, 'training_catalog')
    
    if not allowed:
        return JsonResponse({
            'error': 'Rate limit exceeded',
            'wait_time': wait_time
        }, status=429)
    
    # Get all active trainings with optimized query
    trainings = Training.objects.filter(is_active=True).only(
        'id', 'title', 'slug', 'short_description', 'price_mad',
        'duration_days', 'success_rate', 'max_students', 'badge',
        'thumbnail', 'next_session', 'is_featured',
        'category_caces', 'category_electricite', 'category_soudage',
        'category_securite', 'category_management', 'category_autre'
    ).order_by('-created_at')
    
    # Get search query
    search_query = request.GET.get('q', '')
    if search_query:
        trainings = trainings.filter(
            Q(title__icontains=search_query) |
            Q(short_description__icontains=search_query)
        )
    
    # Get category filter
    category_filter = request.GET.get('category', 'all')
    if category_filter != 'all':
        category_map = {
            'caces': 'category_caces',
            'electricite': 'category_electricite',
            'soudage': 'category_soudage',
            'securite': 'category_securite',
            'management': 'category_management',
            'autre': 'category_autre',
        }
        if category_filter in category_map:
            filter_kwargs = {category_map[category_filter]: True}
            trainings = trainings.filter(**filter_kwargs)
    
    # Get categories from cache
    categories = get_cached_categories(trainings)
    total_count = trainings.count()
    
    # Get preferred currency
    preferred_currency = request.session.get('preferred_currency', 'MAD')
    
    # Prepare training data
    trainings_list = list(trainings)
    for training in trainings_list:
        training.price_mad_float = float(training.price_mad)
        training.price_in_preferred = float(training.get_price_in_currency(preferred_currency))
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(trainings_list, 12)
    
    try:
        trainings_page = paginator.page(page)
    except PageNotAnInteger:
        trainings_page = paginator.page(1)
    except EmptyPage:
        trainings_page = paginator.page(paginator.num_pages)
    
    context = {
        'trainings': trainings_page,
        'categories': categories,
        'selected_category': category_filter,
        'search_query': search_query,
        'total_count': total_count,
        'preferred_currency': preferred_currency,
    }
    
    return render(request, "diray/training_catalog.html", context)



# Update the training_detail function in views.py
def training_detail(request, slug):
    """Training detail view with reviews and optimized queries"""
    training = get_object_or_404(
        Training.objects.select_related(None),
        slug=slug,
        is_active=True
    )
    
    # Increment view count
    training.increment_view_count()
    track_page_view(request, f"{training.title} - Diray Centre")
    
    # Get active bank account
    active_bank_account = CompanyBankAccount.get_active_account()
    
    # Check rate limit
    ip_address = get_client_ip(request)
    allowed, wait_time = RateLimiter.check_rate_limit(ip_address, f'training_detail_{slug}')
    
    if not allowed:
        return JsonResponse({
            'error': 'Rate limit exceeded',
            'wait_time': wait_time
        }, status=429)
    
    # Get preferred currency
    preferred_currency = request.session.get('preferred_currency', 'MAD')
    
    # Prepare training data
    training.price_mad_float = float(training.price_mad)
    training.price_in_preferred = float(training.get_price_in_currency(preferred_currency))
    
    # Get available cities (only names, no phones)
    available_cities = []
    city_fields = [
        ('available_casablanca', 'Casablanca'),
        ('available_rabat', 'Rabat'),
        ('available_tanger', 'Tanger'),
        ('available_marrakech', 'Marrakech'),
        ('available_agadir', 'Agadir'),
        ('available_fes', 'Fès'),
        ('available_meknes', 'Meknès'),
        ('available_oujda', 'Oujda'),
        ('available_laayoune', 'Laâyoune'),
        ('available_dakhla', 'Dakhla'),
        ('available_other', 'Autre ville'),
    ]
    
    for field, name in city_fields:
        if getattr(training, field):
            available_cities.append({'name': name})
    
    # Get reviews
    reviews = TrainingReview.objects.filter(
        training=training,
        is_approved=True
    ).order_by('-created_at')
    
    # Add avatar path to each review (compatible with old and new reviews)
    for review in reviews:
        if not review.avatar or review.avatar == '':
            # Assign a default avatar based on review ID or name
            avatar_number = (review.id % 4) + 1 if review.id else (hash(review.full_name) % 4) + 1
            review.avatar = f'images/avatars/avatar{avatar_number}.png'
        # Ensure the avatar path is complete
        elif not review.avatar.startswith('images/avatars/'):
            # If it's just a filename, prepend the path
            if '.' in review.avatar:
                review.avatar = f'images/avatars/{review.avatar}'
            else:
                review.avatar = f'images/avatars/avatar1.png'
    
    avg_rating = get_training_avg_rating(training.id)
    
    # Get waitlist count
    waitlist_count = TrainingWaitlist.objects.filter(training=training).count()
    
    # Get gallery images, certificates, testimonials, FAQs, and features
    gallery_images = training.get_gallery_images()
    certificates = training.get_certificates()
    testimonials = training.get_testimonials()
    faqs = training.get_faqs()
    features = training.get_features()
    categories = training.get_categories()
    
    context = {
        'training': training,
        'available_cities': available_cities,
        'reviews': reviews,
        'review_count': reviews.count(),
        'waitlist_count': waitlist_count,
        'preferred_currency': preferred_currency,
        'gallery_images': gallery_images,
        'certificates': certificates,
        'testimonials': testimonials,
        'faqs': faqs,
        'features': features,
        'categories': categories,
        'avg_rating': avg_rating or 0,
        'preferred_currency': request.session.get('currency', 'MAD'),
        'bank_account': active_bank_account,
    }
    
    return render(request, "diray/training_detail.html", context)







def migration_services(request):
    """Migration services page"""
    track_page_view(request, "Services de migration")
    
    # Check rate limit
    ip_address = get_client_ip(request)
    allowed, wait_time = RateLimiter.check_rate_limit(ip_address, 'migration_services')
    
    if not allowed:
        return JsonResponse({
            'error': 'Rate limit exceeded',
            'wait_time': wait_time
        }, status=429)
    
    cities = City.objects.filter(is_active=True).order_by('name')
    ip_address = get_client_ip(request)
    user_location = get_location_from_ip(ip_address)
    
    context = {
        'all_cities': cities,
        'user_location': user_location,
    }
    
    return render(request, "diray/migration_services.html", context)

def contact_centers(request):
    """Contact centers page"""
    track_page_view(request, "Centres de contact")
    
    # Check rate limit
    ip_address = get_client_ip(request)
    allowed, wait_time = RateLimiter.check_rate_limit(ip_address, 'contact_centers')
    
    if not allowed:
        return JsonResponse({
            'error': 'Rate limit exceeded',
            'wait_time': wait_time
        }, status=429)
    
    cities = City.objects.filter(is_active=True).order_by('name')
    ip_address = get_client_ip(request)
    user_location = get_location_from_ip(ip_address)
    
    context = {
        'all_cities': cities,
        'user_location': user_location,
    }
    
    return render(request, "diray/contact_centers.html", context)

# ========== API VIEWS ==========


@require_POST
@csrf_exempt
def submit_contact_request(request):
    """Handle contact form submission with rate limiting"""
    try:
        # Check rate limit
        ip_address = get_client_ip(request)
        allowed, wait_time = RateLimiter.check_rate_limit(ip_address, 'submit_contact', limit=5)
        
        data = json.loads(request.body)
        
        # Get user location
        user_location = get_location_from_ip(ip_address)
        
        # Determine request type
        request_type = data.get('request_type', 'information')
        
        # Create contact request
        contact_data = {
            'full_name': data.get('full_name', '').strip(),
            'email': data.get('email', '').strip().lower(),
            'phone': data.get('phone', '').strip(),
            'city': data.get('city', user_location.get('city', '')),
            'country': data.get('country', user_location.get('country', 'Maroc')),
            'request_type': request_type,
            'message': data.get('message', '').strip(),
            'training_title': data.get('training_title', ''),
            'payment_method': data.get('payment_method', ''),
            'ip_address': ip_address,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'session_id': request.session.session_key or '',
        }
        
        # Add payment details if present
        if data.get('payment_method'):
            contact_data['payment_status'] = 'pending' if data['payment_method'] == 'bank_transfer' else 'completed'
            contact_data['card_last_four'] = data.get('card_last_four', '')
            contact_data['card_expiry'] = data.get('card_expiry', '')
            contact_data['transfer_reference'] = data.get('transfer_reference', '')
        
        # Create contact request
        contact_request = ContactRequest.objects.create(**contact_data)
        
        # If training specified, increment inquiry count
        training_id = data.get('training_id')
        if training_id:
            try:
                training = Training.objects.get(id=training_id)
                training.increment_inquiry_count()
                contact_request.training = training
                contact_request.save()
            except Training.DoesNotExist:
                pass
        
        # Track form submission
        if request.session.session_key:
            FormSubmission.objects.create(
                form_type='contact',
                training_title=data.get('training_title', ''),
                session_id=request.session.session_key,
                ip_address=ip_address,
                city=user_location.get('city', ''),
                country=user_location.get('country', ''),
                time_spent=data.get('time_spent', 0)
            )
        
        return JsonResponse({
            'success': True,
            'message': 'Votre demande a été envoyée avec succès.',
            'request_id': contact_request.id
        })
        
    except Exception as e:
        logger.error(f"Error submitting contact request: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Une erreur est survenue: {str(e)}'
        }, status=500)


@csrf_exempt
@require_POST
def create_pre_subscription(request):
    """Create a pre-subscription with bank transfer support"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['training_id', 'full_name', 'email', 'phone', 'city', 'payment_method']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'success': False,
                    'message': f'Le champ {field} est obligatoire'
                })
        
        # Get training
        try:
            training = Training.objects.get(id=data['training_id'])
        except Training.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Formation non trouvée'
            })
        
        # Create subscription data
        subscription_data = {
            'training': training,
            'full_name': data['full_name'],
            'email': data['email'],
            'phone': data['phone'],
            'city': data['city'],
            'payment_method': data['payment_method'],
            'original_price_mad': data.get('original_price_mad', training.price_mad),
            'paid_price_mad': data.get('paid_price_mad', training.price_mad),
            'currency_used': data.get('currency_used', 'MAD'),
            'payment_status': 'pending' if data['payment_method'] == 'bank_transfer' else 'completed',
            'ip_address': get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'session_id': request.session.session_key or str(uuid.uuid4())
        }
        
        # Add card details if applicable
        if data['payment_method'] == 'card':
            subscription_data['card_last_four'] = data.get('card_last_four', '')[-4:] if data.get('card_last_four') else ''
            subscription_data['card_expiry'] = data.get('card_expiry', '')
        
        # Add bank transfer details if applicable
        if data['payment_method'] == 'bank_transfer':
            subscription_data['transfer_confirmation'] = data.get('transfer_confirmation', '')
            subscription_data['transfer_reference'] = f"TRF-{str(uuid.uuid4())[:8].upper()}"
        
        # Create subscription
        subscription = TrainingPreSubscription.objects.create(**subscription_data)
        
        # Generate PDF receipt
        receipt_url = subscription.generate_receipt_pdf()
        
        return JsonResponse({
            'success': True,
            'message': 'Inscription créée avec succès' if data['payment_method'] != 'bank_transfer' 
                      else 'Pré-inscription enregistrée. Veuillez effectuer le virement.',
            'subscription': {
                'id': subscription.id,
                'transaction_id': str(subscription.transaction_id),
                'full_name': subscription.full_name,
                'paid_price': str(subscription.paid_price_mad),
                'currency_used': subscription.currency_used,
                'receipt_url': receipt_url or '',
                'payment_method': subscription.payment_method,
                'payment_status': subscription.payment_status,
                'transfer_reference': subscription.transfer_reference if data['payment_method'] == 'bank_transfer' else None
            }
        })
        
    except Exception as e:
        logger.error(f"Error creating pre-subscription: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        })



@csrf_exempt
@require_POST
def submit_review(request):
    """Submit a training review with avatar support"""
    try:
        data = json.loads(request.body)
        training_id = data.get('training_id')
        
        training = Training.objects.get(id=training_id)
        
        # Create review
        review = TrainingReview.objects.create(
            training=training,
            full_name=data.get('full_name'),
            email=data.get('email'),
            rating=int(data.get('rating', 5)),
            title=data.get('title'),
            comment=data.get('comment'),
            avatar=data.get('avatar', 'images/avatars/avatar1.png'),
            is_approved=False,  # Needs admin approval
            created_at=timezone.now()
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Votre avis a été soumis et sera examiné par notre équipe.',
            'review_id': review.id
        })
        
    except Training.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Formation non trouvée'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        })

@csrf_exempt
@require_POST
def join_waitlist(request):
    """Join training waitlist"""
    try:
        data = json.loads(request.body)
        training_id = data.get('training_id')
        email = data.get('email')
        
        training = Training.objects.get(id=training_id)
        
        # Check if already in waitlist
        existing = TrainingWaitlist.objects.filter(
            training=training, 
            email=email
        ).first()
        
        if existing:
            return JsonResponse({
                'success': False,
                'message': 'Vous êtes déjà sur la liste d\'attente pour cette formation.'
            })
        
        # Count current waitlist position
        position = TrainingWaitlist.objects.filter(training=training).count() + 1
        
        # Create waitlist entry
        TrainingWaitlist.objects.create(
            training=training,
            email=email,
            full_name=data.get('full_name', ''),
            phone=data.get('phone', ''),
            city=data.get('city', ''),
            created_at=timezone.now()
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Ajouté à la liste d\'attente',
            'position': position
        })
        
    except Training.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Formation non trouvée'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        })

# Helper function to get average rating
def get_training_avg_rating(training_id):
    """Calculate average rating for a training"""
    from django.db.models import Avg
    result = TrainingReview.objects.filter(
        training_id=training_id,
        is_approved=True
    ).aggregate(Avg('rating'))
    
    return result['rating__avg'] or 0

@require_POST
@csrf_exempt
def update_currency(request):
    """Update user's preferred currency"""
    try:
        # Check rate limit
        ip_address = get_client_ip(request)
        allowed, wait_time = RateLimiter.check_rate_limit(ip_address, 'update_currency', limit=10)
        
        if not allowed:
            return JsonResponse({
                'success': False,
                'wait_time': wait_time
            }, status=429)
        
        data = json.loads(request.body)
        currency = data.get('currency', 'MAD')
        
        valid_currencies = ['MAD', 'EUR', 'USD', 'GBP', 'CAD', 'AED', 'CHF']
        
        if currency in valid_currencies:
            request.session['preferred_currency'] = currency
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'message': 'Devise non supportée.'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@csrf_exempt
def get_currency_rates_api(request):
    """API endpoint to get currency rates"""
    try:
        rates = get_cached_currency_rates()
        return JsonResponse({
            'success': True,
            'rates': rates,
            'last_updated': datetime.now().isoformat()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@require_POST
@csrf_exempt
def track_click_event(request):
    """Track button/link clicks for analytics"""
    try:
        data = json.loads(request.body)
        
        session_id = request.session.session_key
        if not session_id:
            return JsonResponse({'success': False})
        
        ip_address = get_client_ip(request)
        user_location = get_location_from_ip(ip_address)
        
        ClickEvent.objects.create(
            element_type=data.get('element_type', 'button'),
            element_text=data.get('element_text', ''),
            element_id=data.get('element_id', ''),
            url=data.get('url', request.path),
            session_id=session_id,
            ip_address=ip_address,
            city=user_location.get('city', '')
        )
        
        return JsonResponse({'success': True})
        
    except:
        return JsonResponse({'success': False})

@require_POST
@csrf_exempt
def track_phone_call(request):
    """Track phone call clicks"""
    try:
        data = json.loads(request.body)
        
        session_id = request.session.session_key
        if not session_id:
            return JsonResponse({'success': False})
        
        ip_address = get_client_ip(request)
        user_location = get_location_from_ip(ip_address)
        
        PhoneCall.objects.create(
            phone_number=data.get('phone_number', ''),
            caller_city=user_location.get('city', ''),
            caller_country=user_location.get('country', ''),
            url=data.get('url', request.path),
            session_id=session_id,
            ip_address=ip_address
        )
        
        return JsonResponse({'success': True})
        
    except:
        return JsonResponse({'success': False})

@require_POST
@csrf_exempt
def track_whatsapp_click(request):
    """Track WhatsApp button clicks"""
    try:
        data = json.loads(request.body)
        
        session_id = request.session.session_key
        if not session_id:
            return JsonResponse({'success': False})
        
        ip_address = get_client_ip(request)
        user_location = get_location_from_ip(ip_address)
        
        WhatsAppClick.objects.create(
            phone_number=data.get('phone_number', '+212779259942'),
            message_prefill=data.get('message', ''),
            url=data.get('url', request.path),
            session_id=session_id,
            ip_address=ip_address,
            city=user_location.get('city', '')
        )
        
        return JsonResponse({'success': True})
        
    except:
        return JsonResponse({'success': False})

@csrf_exempt
def get_training_reviews(request, training_id):
    """Get reviews for a training"""
    try:
        training = get_object_or_404(Training, id=training_id)
        reviews = TrainingReview.objects.filter(
            training=training,
            is_approved=True
        ).order_by('-created_at')
        
        reviews_data = []
        for review in reviews:
            reviews_data.append({
                'id': review.id,
                'full_name': review.full_name,
                'avatar': review.avatar or f'images/avatars/avatar{(review.id % 4) + 1}.png',
                'rating': review.rating,
                'title': review.title,
                'comment': review.comment,
                'is_verified': review.is_verified,
                'created_at': review.created_at.strftime('%d/%m/%Y'),
                'helpful_count': review.helpful_count,
                'not_helpful_count': review.not_helpful_count,
            })
        
        avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        
        return JsonResponse({
            'success': True,
            'reviews': reviews_data,
            'avg_rating': round(avg_rating, 1),
            'total_reviews': reviews.count()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@require_POST
@csrf_exempt
def mark_review_helpful(request):
    """Mark review as helpful"""
    try:
        data = json.loads(request.body)
        review_id = data.get('review_id')
        is_helpful = data.get('is_helpful', True)
        
        review = get_object_or_404(TrainingReview, id=review_id)
        
        if is_helpful:
            review.helpful_count = F('helpful_count') + 1
        else:
            review.not_helpful_count = F('not_helpful_count') + 1
        
        review.save(update_fields=['helpful_count', 'not_helpful_count'])
        
        return JsonResponse({
            'success': True,
            'helpful_count': review.helpful_count,
            'not_helpful_count': review.not_helpful_count
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

# ==========================================
# AUTHENTICATION VIEWS
# ==========================================

from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages

def register(request):
    """Handle student registration"""
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['cin_or_passport'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['full_name'].split(' ')[0],
                last_name=' '.join(form.cleaned_data['full_name'].split(' ')[1:])
            )
            
            # Profile is created by signal, but we update it here
            try:
                profile = user.profile
                profile.role = 'STUDENT'
                profile.full_name = form.cleaned_data['full_name']
                profile.cin_or_passport = form.cleaned_data['cin_or_passport']
                profile.phone_number = form.cleaned_data['phone_number']
                profile.city = form.cleaned_data['city']
                profile.save()
            except Exception as e:
                logger.error(f"Error updating profile: {e}")
            
            # Authenticate and login (optional, or redirect to login)
            login(request, user)
            messages.success(request, "Compte créé avec succès! En attente de validation.")
            return redirect('diray:home')
    else:
        form = StudentRegistrationForm()
    
    return render(request, 'registration/signup.html', {'form': form})

def login_view(request):
    """
    Custom login view with external API authentication

    This view authenticates students via the Système de Calcul API.
    If SYSTEME_CALCUL_API_URL is not configured, it falls back to local Django auth.
    """
    if request.method == 'POST':
        email = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not email or not password:
            messages.error(request, "Veuillez remplir tous les champs.")
            return render(request, 'registration/login.html', {'form': AuthenticationForm()})

        # Check if external API is configured
        api_url = getattr(settings, 'SYSTEME_CALCUL_API_URL', None)

        if api_url:
            # Try external API authentication
            try:
                api_client = get_api_client()
                result = api_client.authenticate_student(email, password)

                if result.get('success'):
                    student_data = result.get('student', {})
                    api_token = result.get('token')

                    # Create or update local Django user
                    username = student_data.get('cin') or email
                    user, created = User.objects.get_or_create(
                        username=username,
                        defaults={
                            'email': student_data.get('email', email),
                            'first_name': student_data.get('full_name', '').split()[0] if student_data.get('full_name') else '',
                            'last_name': ' '.join(student_data.get('full_name', '').split()[1:]) if student_data.get('full_name') else '',
                        }
                    )

                    # Update user email if changed
                    if not created and user.email != student_data.get('email', email):
                        user.email = student_data.get('email', email)
                        user.save()

                    # Create or update profile
                    profile, profile_created = Profile.objects.get_or_create(
                        user=user,
                        defaults={
                            'full_name': student_data.get('full_name', ''),
                            'cin_or_passport': student_data.get('cin', ''),
                            'phone_number': student_data.get('phone', ''),
                            'role': 'STUDENT',
                            'status': 'ACTIVE',
                        }
                    )

                    if not profile_created:
                        # Update profile with latest data from API
                        profile.full_name = student_data.get('full_name', profile.full_name)
                        profile.phone_number = student_data.get('phone', profile.phone_number)
                        profile.status = 'ACTIVE'
                        profile.save()

                    # Create student profile if doesn't exist
                    StudentProfile.objects.get_or_create(profile=profile)

                    # Log the user in
                    user.backend = 'django.contrib.auth.backends.ModelBackend'
                    login(request, user)

                    # Store API token in session for subsequent API calls
                    request.session['api_token'] = api_token
                    request.session['api_student_id'] = student_data.get('id')
                    request.session['api_student_data'] = student_data

                    messages.success(request, f"Bienvenue, {student_data.get('full_name', 'Étudiant')}!")
                    return redirect('diray:dashboard')
                else:
                    # API authentication failed
                    error_msg = result.get('error', 'Identifiants invalides.')
                    messages.error(request, error_msg)

            except SystemeCalculAPIError as e:
                logger.error(f"API authentication error: {e.message}")
                messages.error(request, "Erreur de connexion au serveur. Veuillez réessayer.")
            except Exception as e:
                logger.error(f"Unexpected error during API auth: {str(e)}")
                messages.error(request, "Une erreur inattendue s'est produite.")

        else:
            # Fallback to local Django authentication
            form = AuthenticationForm(request, data=request.POST)
            if form.is_valid():
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password')
                user = authenticate(username=username, password=password)
                if user is not None:
                    login(request, user)
                    return redirect('diray:home')
                else:
                    messages.error(request, "Identifiants invalides.")
            else:
                messages.error(request, "Identifiants invalides.")

    form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('diray:home')

# ==========================================
# STUDENT DASHBOARD VIEWS
# ==========================================

def dashboard(request):
    """Student dashboard view - Enhanced with stats and schedule"""
    # 🧠 Behavior to Implement: Simulate logged-in experience
    if not request.user.is_authenticated:
        return render(request, 'diray/dashboard/restricted_access.html')
    if not hasattr(request.user, 'profile'):
        messages.error(request, "Votre profil n'est pas encore configuré.")
        return redirect('diray:home')
        
    profile = request.user.profile
    
    # Check role and redirect accordingly
    if profile.role == 'PROFESSOR':
        return redirect('diray:professor_dashboard')
    elif profile.role in ['ADMIN', 'ASSISTANT']:
        return redirect('/admin/')
    
    # Check if student
    if profile.role != 'STUDENT':
         messages.warning(request, "Accès restreint aux étudiants.")
         return redirect('diray:home')
         
    try:
        student_profile = profile.student_profile
    except StudentProfile.DoesNotExist:
        student_profile = StudentProfile.objects.create(profile=profile)
    
    # Get active formations
    my_formations = student_profile.authorized_formations.all()
    
    # Calculate watch percentage
    total_videos = RecordedVideo.objects.filter(training__in=my_formations).count()
    watched_videos = VideoProgress.objects.filter(student=profile, video__training__in=my_formations, completed=True).count()
    watch_percentage = int((watched_videos / total_videos) * 100) if total_videos > 0 else 0
    
    # Get next seance
    next_seance = None
    if student_profile.session:
        next_seance = Seance.objects.filter(
            session=student_profile.session,
            date__gte=timezone.now().date()
        ).order_by('date', 'time').first()
    
    # Notifications
    student_session = student_profile.session
    notifications = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).filter(
        Q(session=student_session) | Q(session__isnull=True)
    )[:10]

    # Active streams
    active_streams = Live.objects.filter(
        session=student_session,
        is_active=True
    ).select_related('session', 'session__professor__profile').prefetch_related('session__formations') if student_session else []

    context = {
        'profile': profile,
        'student_profile': student_profile,
        'my_formations': my_formations,
        'next_seance': next_seance,
        'watch_percentage': watch_percentage,
        'active_streams': active_streams,
        'notifications': notifications,
        'active_count': my_formations.count(),
        'amount_paid': student_profile.amount_paid,
        'amount_remaining': student_profile.amount_remaining,
    }
    
    return render(request, 'diray/dashboard/dashboard.html', context)

@login_required
@student_active_required
def student_schedule(request):
    """View to display student's schedule (seances)"""
    profile = request.user.profile
    try:
        student_profile = profile.student_profile
    except:
        return redirect('diray:dashboard')
        
    session = student_profile.session
    seances = []
    if session:
        seances = Seance.objects.filter(session=session).order_by('date', 'time')
        
    return render(request, 'diray/dashboard/schedule.html', {
        'profile': profile,
        'session': session,
        'seances': seances
    })

@login_required
@student_active_required
def student_profile(request):
    """View to update student profile"""
    profile = request.user.profile
    
    if request.method == 'POST':
        # Update logic here
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone_number', '')
        city_name = request.POST.get('city')
        
        user = request.user
        user.first_name = first_name
        user.last_name = last_name
        user.save()
        
        profile.full_name = f"{first_name} {last_name}"
        profile.phone_number = phone
        
        # Fix: Get or create City object instead of assigning string
        if city_name:
            city_obj, created = City.objects.get_or_create(name=city_name)
            profile.city = city_obj
        
        profile.save()
        
        messages.success(request, "Profil mis à jour avec succès.")
        return redirect('diray:student_profile')
        
    return render(request, 'diray/dashboard/profile.html', {'profile': profile})


@login_required
@require_POST
def upload_profile_picture(request):
    """Secure profile picture upload via ImgBB API"""
    import mimetypes
    import os
    from django.core.files.uploadedfile import InMemoryUploadedFile
    
    try:
        profile = request.user.profile
    except:
        return JsonResponse({'success': False, 'error': 'Profil introuvable.'}, status=400)
    
    # Security: Rate Limiting (3 uploads per hour)
    cache_key = f'profile_upload_{request.user.id}'
    attempts = cache.get(cache_key, 0)
    if attempts >= 3:
        return JsonResponse({
            'success': False, 
            'error': 'Trop de tentatives. Veuillez réessayer dans 1 heure.'
        }, status=429)
    
    # Get uploaded file
    if 'profile_picture' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'Aucun fichier sélectionné.'}, status=400)
    
    uploaded_file = request.FILES['profile_picture']
    
    # Security: File Size Validation (Max 5MB)
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    if uploaded_file.size > MAX_FILE_SIZE:
        return JsonResponse({
            'success': False, 
            'error': 'L\'image doit faire moins de 5MB.'
        }, status=400)
    
    # Security: File Type Validation
    ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp']
    ALLOWED_MIMES = ['image/jpeg', 'image/png', 'image/webp']
    
    # Check extension
    file_ext = uploaded_file.name.split('.')[-1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        return JsonResponse({
            'success': False, 
            'error': 'Format non supporté. Utilisez JPG, PNG ou WebP.'
        }, status=400)
    
    # Security: MIME Type Validation (server-side)
    mime_type, _ = mimetypes.guess_type(uploaded_file.name)
    if mime_type not in ALLOWED_MIMES:
        return JsonResponse({
            'success': False, 
            'error': 'Type de fichier invalide.'
        }, status=400)
    
    # Security: Filename Sanitization
    import re
    safe_filename = re.sub(r'[^a-zA-Z0-9._-]', '', uploaded_file.name)
    
    # Get session info for folder organization
    try:
        student_profile = profile.student_profile
        session_folder = student_profile.session.city.name if student_profile.session and student_profile.session.city else 'default'
    except:
        session_folder = 'default'
    
    # Sanitize folder name
    session_folder = re.sub(r'[^a-zA-Z0-9_-]', '', session_folder)
    
    # Prepare ImgBB upload
    IMGBB_API_KEY = '4f4a4f813037f0bdf500c95d898ede08'
    IMGBB_URL = 'https://api.imgbb.com/1/upload'
    
    try:
        # Read file content
        file_content = uploaded_file.read()
        
        # Prepare request
        import base64
        encoded_image = base64.b64encode(file_content).decode('utf-8')
        
        # Create album/folder name with session
        album_name = f"diray_{session_folder}_{profile.user.username}"
        
        payload = {
            'key': IMGBB_API_KEY,
            'image': encoded_image,
            'name': f"{profile.user.username}_{safe_filename}",
        }
        
        # Upload to ImgBB
        response = requests.post(IMGBB_URL, data=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                # Get direct image URL
                image_url = data['data']['display_url']
                
                # Save to profile
                profile.profile_picture = image_url
                profile.save(update_fields=['profile_picture'])
                
                # Increment rate limit counter
                cache.set(cache_key, attempts + 1, 3600)  # 1 hour
                
                return JsonResponse({
                    'success': True, 
                    'image_url': image_url,
                    'message': 'Photo de profil mise à jour avec succès!'
                })
            else:
                return JsonResponse({
                    'success': False, 
                    'error': 'Erreur lors du téléchargement. Veuillez réessayer.'
                }, status=500)
        else:
            return JsonResponse({
                'success': False, 
                'error': 'Erreur de connexion au serveur. Veuillez réessayer.'
            }, status=500)
            
    except requests.exceptions.Timeout:
        return JsonResponse({
            'success': False, 
            'error': 'Délai d\'attente dépassé. Veuillez réessayer.'
        }, status=504)
    except requests.exceptions.RequestException as e:
        return JsonResponse({
            'success': False, 
            'error': 'Erreur de connexion. Veuillez réessayer.'
        }, status=500)
    except Exception as e:
        logging.error(f"Profile upload error: {str(e)}")
        return JsonResponse({
            'success': False, 
            'error': 'Une erreur est survenue. Veuillez réessayer.'
        }, status=500)

# Classroom
@login_required
def classroom(request, training_slug, video_id=None):
    """Classroom view for VOD"""
    try:
        profile = request.user.profile
        student_profile = profile.student_profile
    except:
         return redirect('diray:home')

    # Get Training and check access
    training = get_object_or_404(Training, slug=training_slug)
    if not student_profile.authorized_formations.filter(id=training.id).exists():
        messages.error(request, "Vous n'avez pas accès à cette formation.")
        return redirect('diray:dashboard')
        
    # Get Videos
    videos = RecordedVideo.objects.filter(training=training, is_active=True).order_by('created_at')
    
    if not videos.exists():
        messages.warning(request, "Aucune vidéo disponible pour cette formation.")
        return redirect('diray:dashboard')
        
    # Select current video
    if video_id:
        current_video = get_object_or_404(RecordedVideo, id=video_id, training=training)
    else:
        current_video = videos.first()
        
    # Find the session this student is currently in for this training
    student_session = student_profile.session
    
    # Validating session pertains to this training (optional but good)
    if student_session and not student_session.formations.filter(id=training.id).exists():
        student_session = None

    # Get Questions (filtered by session if available)
    if student_session:
        questions = Question.objects.filter(video=current_video, student__session=student_session, is_deleted=False).order_by('-created_at')
    else:
        questions = Question.objects.filter(video=current_video, is_deleted=False).order_by('-created_at')
    
    # Handle Question Submission
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            # Create the question
            question = Question.objects.create(
                video=current_video,
                student=student_profile,
                content=content
            )
            
            # Notify Professor(s)
            professors_to_notify = []
            if student_session:
                professors_to_notify.append(student_session.professor.profile.user)
            else:
                # Notify all professors associated with this training via past or ongoing sessions
                prof_users = User.objects.filter(
                    profile__professor_profile__sessions__formations=training
                ).distinct()
                professors_to_notify.extend(list(prof_users))

            notifications = []
            for prof_user in professors_to_notify:
                notifications.append(Notification(
                    user=prof_user,
                    session=student_session,
                    title=f"Nouvelle question - {training.title}",
                    message=f"{profile.full_name} a posé une question sur la vidéo: {current_video.title}",
                    notification_type='info',
                    link=f"/professor/comments/{'?session_id=' + str(student_session.id) if student_session else ''}"
                ))
            
            if notifications:
                Notification.objects.bulk_create(notifications)

            messages.success(request, "Votre question a été ajoutée.")
            return redirect('diray:classroom_video', training_slug=training.slug, video_id=current_video.id)
            
    context = {
        'training': training,
        'videos': videos,
        'current_video': current_video,
        'comments': questions,
    }
    
    return render(request, 'diray/classroom/classroom.html', context)

@login_required
def check_updates_ajax(request):
    """API endpoint for long-polling/updates (notifications and live status)"""
    profile = request.user.profile
    now = timezone.now()
    
    # 1. Notifications
    notifications = Notification.objects.filter(
        user=request.user, 
        is_read=False
    ).select_related('session').order_by('-created_at')[:5]
    
    notif_data = [{
        'id': n.id,
        'title': n.title,
        'message': n.message,
        'type': n.notification_type,
        'created_at': n.created_at.strftime('%H:%M'),
        'link': n.link
    } for n in notifications]

    # 2. Live Streams (Context-Specific)
    active_streams_data = []
    
    if profile.role == 'STUDENT':
        student_profile = profile.student_profile
        active_streams = Live.objects.filter(
            session=student_profile.session,
            is_active=True
        ).select_related('session').prefetch_related('session__formations') if student_profile.session else []
        
    elif profile.role == 'PROFESSOR':
        prof_profile = profile.professor_profile
        active_streams = Live.objects.filter(
            session__professor=prof_profile,
            is_active=True
        ).select_related('session').prefetch_related('session__formations')
    else:
        active_streams = []

    for stream in active_streams:
        formations = ", ".join([t.title for t in stream.session.formations.all()])
        active_streams_data.append({
            'id': stream.id,
            'session_id': stream.session.id,
            'trainings': formations,
            'professor': stream.session.professor.profile.full_name,
            'join_url': f"/live/{stream.id}/" # Hardcoded path or use reverse
        })

    return JsonResponse({
        'status': 'success',
        'notifications': notif_data,
        'unread_count': Notification.objects.filter(user=request.user, is_read=False).count(),
        'active_streams': active_streams_data,
        'server_time': now.isoformat()
    })

# ==========================================
# LIVE SESSION VIEW
# ==========================================

@professor_required
def start_live_stream(request, session_id):
    """Professor starts a new live stream event for a session"""
    session = get_object_or_404(Session, id=session_id, professor__profile=request.user.profile)
    
    if session.status == 'COMPLETED':
        messages.error(request, "Cette session est terminée. Vous ne pouvez plus lancer de live.")
        return redirect('diray:professor_dashboard')
        
    if session.status != 'ONGOING':
        messages.error(request, "La session doit être 'En cours' pour démarrer un live.")
        return redirect('diray:professor_dashboard')
    
    # Check if there's already an active stream
    active_stream = Live.objects.filter(session=session, is_active=True).first()
    if active_stream:
        messages.info(request, "Un live est déjà en cours pour cette session.")
        return redirect('diray:live_session', stream_id=active_stream.id)
    
    # Create new stream event
    stream = Live.objects.create(
        session=session,
        agora_channel=f"session_{session.id}_live_{timezone.now().strftime('%Y%H%M%S')}",
        is_active=True
    )
    
    messages.success(request, "Live démarré ! Les étudiants peuvent maintenant rejoindre.")
    return redirect('diray:live_session', stream_id=stream.id)

@professor_required
def end_live_stream(request, stream_id):
    """Professor ends an active live stream"""
    stream = get_object_or_404(Live, id=stream_id, session__professor__profile=request.user.profile)
    stream.is_active = False
    stream.ended_at = timezone.now()
    stream.save()
    
    messages.success(request, "Le live a été terminé. La session reste active.")
    return redirect('diray:professor_dashboard')

@professor_required
def update_session_status(request, session_id):
    """Professor transitions the session (CREATED -> ONGOING -> COMPLETED)"""
    session = get_object_or_404(Session, id=session_id, professor__profile=request.user.profile)
    new_status = request.POST.get('status')
    
    if new_status in ['ONGOING', 'COMPLETED']:
        session.status = new_status
        session.save()
        messages.success(request, f"Statut de la session mis à jour : {session.get_status_display()}")
        
        # If completing, end all lives
        if new_status == 'COMPLETED':
            Live.objects.filter(session=session, is_active=True).update(
                is_active=False, 
                ended_at=timezone.now()
            )
            
    return redirect('diray:professor_dashboard')

@login_required
def live_session(request, stream_id):
    """Live session view for a specific stream event"""
    stream = get_object_or_404(Live, id=stream_id)
    session = stream.session
    profile = request.user.profile
    
    user_is_host = False
    
    if profile.role == 'PROFESSOR':
        try:
            professor_profile = profile.professor_profile
            if session.professor == professor_profile:
                user_is_host = True
            else:
                messages.error(request, "Vous n'êtes pas le professeur assigné à cette session.")
                return redirect('diray:professor_dashboard')
        except ProfessorProfile.DoesNotExist:
            return redirect('diray:home')
    else:
        # Student check
        try:
            student_profile = profile.student_profile
            if student_profile.session != session:
                messages.error(request, "Vous n'avez pas accès à cette session.")
                return redirect('diray:dashboard')
            
            # Record attendance (joining now)
            AttendanceLog.objects.create(
                student=profile,
                live_stream=stream,
                session=session,
                join_time=timezone.now()
            )
        except StudentProfile.DoesNotExist:
            return redirect('diray:home')
    
    # Agora credentials
    agora_app_id = "YOUR_AGORA_APP_ID" 
    agora_channel = stream.agora_channel
    agora_token = None
    
    context = {
        'stream': stream,
        'session': session,
        'is_currently_live': stream.is_active,
        'now': timezone.now(),
        'user_is_host': user_is_host,
        'agora_app_id': agora_app_id,
        'agora_channel': agora_channel,
        'agora_token': agora_token,
    }
    
    return render(request, 'diray/live/live_session.html', context)


@login_required
@student_active_required
def recorded_videos_list(request, training_slug):
    """List all recorded videos for a training"""
    try:
        profile = request.user.profile
        student_profile = profile.student_profile
    except:
        return redirect('diray:home')
    
    # Get Training and check access
    training = get_object_or_404(Training, slug=training_slug)
    if not student_profile.authorized_formations.filter(id=training.id).exists():
        messages.error(request, "Vous n'avez pas accès à cette formation.")
        return redirect('diray:dashboard')
    
    # Get all videos
    videos = RecordedVideo.objects.filter(training=training, is_active=True).order_by('created_at')
    
    # Get progress for each video
    video_progress = {}
    for video in videos:
        try:
            progress = VideoProgress.objects.get(student=profile, video=video)
            video_progress[video.id] = {
                'watched_seconds': progress.watched_seconds,
                'completed': progress.completed,
                'percentage': int((progress.watched_seconds / video.duration_seconds) * 100) if video.duration_seconds > 0 else 0
            }
        except VideoProgress.DoesNotExist:
            video_progress[video.id] = {
                'watched_seconds': 0,
                'completed': False,
                'percentage': 0
            }
    
    context = {
        'training': training,
        'videos': videos,
        'video_progress': video_progress,
    }
    
    return render(request, 'diray/videos/videos_list.html', context)

# ==========================================
# PROFESSOR DASHBOARD & MANAGEMENT
# ==========================================

@professor_required
def professor_dashboard(request):
    """Professor dashboard main view - Session-Centric"""
    prof_profile = get_object_or_404(ProfessorProfile, profile=request.user.profile)
    
    # Get all potential sessions for this professor
    all_sessions = Session.objects.filter(
        professor=prof_profile,
        is_active=True
    ).prefetch_related('formations').order_by('-start_date')
    
    # Identify the current/selected session
    selected_session_id = request.GET.get('session_id')
    selected_session = None
    
    if selected_session_id:
        selected_session = all_sessions.filter(id=selected_session_id).first()
    
    if not selected_session:
        # Default to the most recent/active session
        now = timezone.now().date()
        selected_session = all_sessions.filter(start_date__lte=now, end_date__gte=now).first()
        if not selected_session:
            selected_session = all_sessions.first()
            
    # Scoped Data
    students_count = 0
    recent_questions = []
    active_streams = []
    upcoming_sessions = all_sessions.filter(start_date__gt=timezone.now().date())
    active_sessions = all_sessions.filter(status='ONGOING')
    
    if selected_session:
        # Students in THIS session
        students_count = selected_session.students.count()
        
        # Comments on THIS session's topics (scoped to session)
        recent_questions = Question.objects.filter(
            student__session=selected_session,
            is_deleted=False
        ).order_by('-created_at')[:5]
        
        # Active streams for THIS session
        active_streams = Live.objects.filter(
            session=selected_session,
            is_active=True
        ).prefetch_related('session__formations')

    # notifications filtering
    notifications = Notification.objects.filter(
        user=request.user, 
        is_read=False
    ).filter(
        Q(session=selected_session) | Q(session__isnull=True)
    )[:5]

    context = {
        'prof_profile': prof_profile,
        'all_sessions': all_sessions,
        'selected_session': selected_session,
        'students_count': students_count,
        'recent_comments': recent_questions,
        'active_streams': active_streams,
        'trainings': Training.objects.filter(sessions__professor=prof_profile).distinct(),
        'notifications': notifications,
        'upcoming_sessions': upcoming_sessions,
        'active_sessions': active_sessions,
        'current_time': timezone.now(),
    }
    return render(request, 'diray/professor/dashboard.html', context)

@login_required
def account_status(request):
    """View to display account status (Pending/Suspended)"""
    if not hasattr(request.user, 'profile'):
        return redirect('diray:home')
        
    profile = request.user.profile
    
    # If active, no need to be here
    if profile.status == 'ACTIVE':
        return redirect('diray:dashboard')
        
    return render(request, 'diray/dashboard/account_status.html', {'profile': profile})

@professor_required
def professor_students(request):
    """List students enrolled in professor's sessions - Session-Centric"""
    prof_profile = get_object_or_404(ProfessorProfile, profile=request.user.profile)
    
    # Session filtering
    session_id = request.GET.get('session_id')
    selected_session = None
    if session_id:
        selected_session = Session.objects.filter(id=session_id, professor=prof_profile).first()
        
    if selected_session:
        students = selected_session.students.select_related('profile').all()
    else:
        students = StudentProfile.objects.filter(
            session__professor=prof_profile
        ).select_related('profile').distinct()
    
    all_sessions = Session.objects.filter(professor=prof_profile, is_active=True).order_by('-start_date')
    
    context = {
        'students': students,
        'all_sessions': all_sessions,
        'selected_session': selected_session,
        'prof_profile': prof_profile,
    }
    return render(request, 'diray/professor/students.html', context)

@professor_required
def professor_sessions(request):
    """Manage professor's sessions"""
    prof_profile = get_object_or_404(ProfessorProfile, profile=request.user.profile)
    
    if request.method == 'POST':
        if request.user.profile.role != 'ADMIN':
            messages.error(request, "Seuls les administrateurs peuvent créer des sessions.")
            return redirect('diray:professor_sessions')

        training_ids = request.POST.getlist('training_ids')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        city_id = request.POST.get('city_id')
        is_live = request.POST.get('is_live') == 'on'
        
        try:
            city_obj = City.objects.get(id=city_id)
            session = Session.objects.create(
                professor=prof_profile,
                start_date=start_date,
                end_date=end_date,
                city=city_obj,
                is_live=is_live,
                is_active=True
            )
            if training_ids:
                session.formations.set(Training.objects.filter(id__in=training_ids))
            
            messages.success(request, "Session créée avec succès.")
        except Exception as e:
            messages.error(request, f"Erreur lors de la création: {e}")
        
        return redirect('diray:professor_sessions')
        
    sessions = Session.objects.filter(professor=prof_profile).prefetch_related('formations').order_by('-start_date')
    trainings = Training.objects.all()
    cities = City.objects.all()
    
    # Get seances for sessions
    for sess in sessions:
        sess.theory_count = sess.seances.filter(type='THEORIQUE').count()
        sess.practice_count = sess.seances.filter(type='PRATIQUE').count()
    
    context = {
        'sessions': sessions,
        'all_sessions': sessions,
        'trainings': trainings,
        'cities': cities,
        'prof_profile': prof_profile,
    }
    return render(request, 'diray/professor/sessions.html', context)

@professor_required
@require_POST
def add_seance(request):
    """Add a seance to a session (UI-based)"""
    session_id = request.POST.get('session_id')
    session = get_object_or_404(Session, id=session_id, professor__profile=request.user.profile)
    
    if session.status == 'COMPLETED':
        messages.error(request, "Cette session est terminée. Vous ne pouvez plus ajouter de séances.")
        return redirect('diray:professor_sessions')
    
    title = request.POST.get('title')
    seance_type = request.POST.get('type')
    date = request.POST.get('date')
    time = request.POST.get('time')
    location = request.POST.get('location', '')
    
    try:
        # Check if we already have 2 of this type
        existing_count = session.seances.filter(type=seance_type).count()
        if existing_count >= 2:
            messages.warning(request, f"Vous avez déjà ajouté 2 séances de type {seance_type} pour cette session.")
            
        Seance.objects.create(
            session=session,
            title=title,
            type=seance_type,
            date=date,
            time=time,
            location=location
        )
        messages.success(request, "Séance ajoutée avec succès.")
    except Exception as e:
        messages.error(request, f"Erreur: {e}")
        
    return redirect('diray:professor_sessions')

@professor_required
def professor_comments(request):
    """View and reply to comments - Session-Centric"""
    prof_profile = get_object_or_404(ProfessorProfile, profile=request.user.profile)
    
    if request.method == 'POST':
        question_id = request.POST.get('comment_id')
        reply_content = request.POST.get('reply')
        
        if question_id and reply_content:
            question = get_object_or_404(Question, id=question_id)
            
            # Check if session is completed
            if question.student.session and question.student.session.status == 'COMPLETED':
                messages.error(request, "Cette session est terminée. Vous ne pouvez plus répondre aux questions.")
                return redirect('diray:professor_comments')
            
            # Update the question with the answer
            question.answer_content = f"REPONSE PROFESSEUR: {reply_content}"
            question.answered_by = prof_profile
            question.is_answered = True
            question.save()
            
            messages.success(request, "Réponse envoyée.")
            return redirect('diray:professor_comments')

    # Session filtering
    session_id = request.GET.get('session_id')
    selected_session = None
    if session_id:
        selected_session = Session.objects.filter(id=session_id, professor=prof_profile).first()
        
    if selected_session:
        questions = Question.objects.filter(student__session=selected_session, is_deleted=False).order_by('-created_at')
    else:
        # Get trainings where the professor is teaching (via sessions)
        trainings = Training.objects.filter(sessions__professor=prof_profile).distinct()
        questions = Question.objects.filter(
            video__training__in=trainings,
            is_deleted=False
        ).order_by('-created_at')
    
    all_sessions = Session.objects.filter(professor=prof_profile, is_active=True).order_by('-start_date')
    
    context = {
        'comments': questions,
        'all_sessions': all_sessions,
        'selected_session': selected_session,
        'prof_profile': prof_profile,
    }
    return render(request, 'diray/professor/comments.html', context)

@login_required
def mark_notification_read(request, notification_id):
    """Mark a notification as read and redirect to its link"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    
    if notification.link:
        return redirect(notification.link)
    return redirect(request.META.get('HTTP_REFERER', 'diray:home'))

@professor_required
def send_session_notification(request, session_id):
    """Professor sends a notification to all students in a session"""
    session = get_object_or_404(Session, id=session_id, professor__profile=request.user.profile)
    
    if session.status == 'COMPLETED':
        messages.error(request, "Cette session est terminée. Vous ne pouvez plus envoyer de notifications.")
        return redirect('diray:manage_sessions')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        message = request.POST.get('message')
        notif_type = request.POST.get('type', 'info')
        
        if title and message:
            students = session.students.all()
            notifications = []
            for student in students:
                notifications.append(Notification(
                    user=student.profile.user,
                    session=session,
                    title=title,
                    message=message,
                    notification_type=notif_type
                ))
            
            if notifications:
                Notification.objects.bulk_create(notifications)
                messages.success(request, f"Notification envoyée à {len(notifications)} étudiants.")
            else:
                messages.warning(request, "Aucun étudiant n'est inscrit dans cette session.")
                
        return redirect('diray:manage_sessions')
    
    return redirect('diray:manage_sessions')
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@login_required
def attendance_heartbeat(request, stream_id):
    """API endpoint to update student attendance duration via heartbeat"""
    if request.method == 'POST':
        stream = get_object_or_404(Live, id=stream_id)
        profile = request.user.profile
        
        # We find the most recent log for this student and stream
        log = AttendanceLog.objects.filter(student=profile, live_stream=stream).last()
        
        if log:
            # Update leave_time to now and increment duration
            now = timezone.now()
            log.leave_time = now
            delta = now - log.join_time
            log.duration_seconds = int(delta.total_seconds())
            log.save()
            
            return JsonResponse({'status': 'success', 'duration': log.duration_seconds})
            
    return JsonResponse({'status': 'error'}, status=400)
# ==========================================
# ASSISTANT & CALL CENTER MANAGEMENT
# ==========================================

@require_POST
@assistant_required
def create_entity_ajax(request):
    """Unified creation for Students by an Assistant. Extended for efficiency."""
    try:
        data = json.loads(request.body)
        role = data.get('role', 'STUDENT')
        email = data.get('email')
        full_name = data.get('full_name')
        password = data.get('password', 'Diray2026!')
        phone = data.get('phone', '')
        city_id = data.get('city_id')
        
        # New fields for efficiency
        cin = data.get('cin', '')
        formation_ids = data.get('formation_ids', [])
        session_id = data.get('session_id', None)
        status = data.get('status', 'PENDING')
        
        if not all([email, full_name, city_id]):
            return JsonResponse({'status': 'error', 'message': 'Champs requis manquants: Email, Nom, Ville.'})
            
        # Permission check: Assistants can ONLY create STUDENTS
        if not request.user.is_superuser:
            if role != 'STUDENT':
                return JsonResponse({'status': 'error', 'message': 'Action non autorisée: Vous ne pouvez créer que des étudiants.'}, status=403)
            
        city = City.objects.get(id=city_id)
        
        # Check if assistant has access to this city
        if not request.user.is_superuser:
            assistant_profile = request.user.profile.assistant_profile
            if city not in assistant_profile.assigned_cities.all():
                return JsonResponse({'status': 'error', 'message': 'Accès refusé pour cette ville.'}, status=403)
        
        with transaction.atomic():
            # 1. Create/Get User
            user, created = User.objects.get_or_create(
                username=email,
                defaults={'email': email}
            )
            if created:
                user.set_password(password)
                user.save()
            
            # 2. Update Profile (Automatic creation managed by signals)
            profile = user.profile
            profile.role = role
            profile.full_name = full_name
            profile.phone_number = phone
            profile.city = city
            profile.status = status
            profile.cin_or_passport = cin
            profile.save()
            
            # 3. Handle Special Access (StudentProfile is auto-created via profile signal)
            if role == 'STUDENT':
                student_prof = profile.student_profile
                if formation_ids:
                    student_prof.authorized_formations.set(Training.objects.filter(id__in=formation_ids))
                if session_id:
                    session = Session.objects.get(id=session_id)
                    student_prof.session = session
                    student_prof.save()
                
            return JsonResponse({'status': 'success', 'message': f'{profile.get_role_display()} créé et configuré avec succès.'})
            
    except City.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Ville invalide.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@require_POST
@assistant_required
def toggle_student_status(request, student_id):
    """Allow assistants to approve/suspend students in their cities"""
    try:
        student = get_object_or_404(StudentProfile, id=student_id)
        
        # Permission check: Assistant must be assigned to student's city
        if not request.user.is_superuser:
            assistant_profile = request.user.profile.assistant_profile
            if student.profile.city not in assistant_profile.assigned_cities.all():
                 return JsonResponse({'status': 'error', 'message': 'Accès refusé pour cette ville.'}, status=403)
        
        # Toggle status
        new_status = 'ACTIVE' if student.profile.status != 'ACTIVE' else 'PENDING'
        student.profile.status = new_status
        student.profile.save()
        
        return JsonResponse({
            'status': 'success', 
            'message': f'Statut mis à jour: {new_status}',
            'new_status': new_status
        })
    except Exception as e:
         return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@require_POST
@assistant_required
def assistant_assign_training(request):
    """Enroll a student in specific trainings"""
    try:
        data = json.loads(request.body)
        student_id = data.get('student_id')
        training_ids = data.get('training_ids', []) # List of IDs
        
        student = get_object_or_404(StudentProfile, id=student_id)
        
        # Permission check
        if not request.user.is_superuser:
            assistant_profile = request.user.profile.assistant_profile
            if student.profile.city not in assistant_profile.assigned_cities.all():
                return JsonResponse({'status': 'error', 'message': 'Accès refusé pour cet étudiant.'}, status=403)
        
        trainings = Training.objects.filter(id__in=training_ids)
        student.authorized_formations.add(*trainings)
        
        return JsonResponse({'status': 'success', 'message': f'Affectation réussie pour {trainings.count()} formations.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@require_POST
@assistant_required
def assistant_assign_session(request):
    """Assign a student to a specific session"""
    try:
        data = json.loads(request.body)
        student_id = data.get('student_id')
        session_id = data.get('session_id')
        
        student = get_object_or_404(StudentProfile, id=student_id)
        session = get_object_or_404(Session, id=session_id)
        
        # Permission check
        if not request.user.is_superuser:
            assistant_profile = request.user.profile.assistant_profile
            if student.profile.city not in assistant_profile.assigned_cities.all() or \
               session.city not in assistant_profile.assigned_cities.all():
                return JsonResponse({'status': 'error', 'message': 'Accès refusé pour cette session ou cet étudiant.'}, status=403)
        
        student.session = session
        student.save()
        
        return JsonResponse({'status': 'success', 'message': 'Étudiant ajouté à la session.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@require_POST
@assistant_required
def assistant_create_session(request):
    """Create a new session"""
    try:
        data = json.loads(request.body)
        training_ids = data.get('training_ids', [])
        professor_id = data.get('professor_id')
        city_id = data.get('city_id')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        is_live = data.get('is_live', False)
        
        city = get_object_or_404(City, id=city_id)
        
        # Permission check
        if not request.user.is_superuser:
            assistant_profile = request.user.profile.assistant_profile
            if city not in assistant_profile.assigned_cities.all():
                return JsonResponse({'status': 'error', 'message': 'Action non autorisée pour cette ville.'}, status=403)
        
        professor = get_object_or_404(ProfessorProfile, id=professor_id)
        
        with transaction.atomic():
            session = Session.objects.create(
                professor=professor,
                city=city,
                start_date=start_date,
                end_date=end_date,
                is_live=is_live,
                is_active=True
            )
            session.formations.add(*Training.objects.filter(id__in=training_ids))
            
        return JsonResponse({'status': 'success', 'message': 'Session créée avec succès.', 'session_id': session.id})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@assistant_required
def assistant_dashboard(request):
    """Redirect to Django Admin as per user request"""
    return redirect('/admin/')


from django.contrib.auth.decorators import user_passes_test
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

@user_passes_test(lambda u: u.is_superuser)
def director_dashboard(request):
    """Redirect to Django Admin as per user request"""
    return redirect('/admin/')
