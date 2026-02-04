# models.py - COMPLETE MULTILINGUAL VERSION
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid
import json
import os
from django.conf import settings
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
from datetime import datetime

# Common choices
CITY_CHOICES = [
    ('Casablanca', 'Casablanca'),
    ('Rabat', 'Rabat'),
    ('Tanger', 'Tanger'),
    ('Marrakech', 'Marrakech'),
    ('Agadir', 'Agadir'),
    ('Fès', 'Fès'),
    ('Meknès', 'Meknès'),
    ('Oujda', 'Oujda'),
    ('Laâyoune', 'Laâyoune'),
    ('Dakhla', 'Dakhla'),
    ('Autre', 'Autre'),
]

REGION_CHOICES = [
    ('north', 'Région Nord'),
    ('central', 'Région Centrale'),
    ('south', 'Région Sud'),
    ('coast', 'Région Côtière'),
]

BADGE_CHOICES = [
    ('none', 'Aucun badge'),
    ('popular', '🔥 Populaire'),
    ('new', '🆕 Nouvelle'),
    ('promo', '⚡ Promotion'),
]

class Training(models.Model):
    """Main training model with multilingual support"""
    
    # ========== BASIC INFORMATION - FRENCH ==========
    title = models.CharField(max_length=200, verbose_name="Titre FR", db_index=True)
    slug = models.SlugField(max_length=200, unique=True, verbose_name="Slug FR")
    short_description = models.TextField(max_length=300, verbose_name="Description courte FR")
    detailed_description = models.TextField(verbose_name="Description détaillée FR")
    objectives = models.TextField(verbose_name="Objectifs FR", blank=True, default="")
    
    # ========== BASIC INFORMATION - ARABIC ==========
    title_ar = models.CharField(max_length=200, verbose_name="Titre AR", blank=True)
    slug_ar = models.SlugField(max_length=200, blank=True, verbose_name="Slug AR")
    short_description_ar = models.TextField(max_length=300, verbose_name="Description courte AR", blank=True)
    detailed_description_ar = models.TextField(verbose_name="Description détaillée AR", blank=True)
    objectives_ar = models.TextField(verbose_name="Objectifs AR", blank=True, default="")
    
    # ========== BASIC INFORMATION - ENGLISH ==========
    title_en = models.CharField(max_length=200, verbose_name="Titre EN", blank=True)
    slug_en = models.SlugField(max_length=200, blank=True, verbose_name="Slug EN")
    short_description_en = models.TextField(max_length=300, verbose_name="Description courte EN", blank=True)
    detailed_description_en = models.TextField(verbose_name="Description détaillée EN", blank=True)
    objectives_en = models.TextField(verbose_name="Objectifs EN", blank=True, default="")
    
    # ========== PRICING & DURATION (COMMON) ==========
    price_mad = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Prix en MAD",
        db_index=True
    )
    duration_days = models.PositiveIntegerField(verbose_name="Durée en jours")
    max_students = models.PositiveIntegerField(
        default=20,
        verbose_name="Nombre maximum d'étudiants"
    )
    
    # ========== PROGRAMME STRUCTURE - FRENCH ==========
    programme_structure = models.JSONField(
        verbose_name="Structure du programme FR",
        default=dict,
        blank=True,
        help_text="Structure JSON du programme théorique et pratique FR"
    )
    programme_theorique = models.TextField(verbose_name="Programme théorique FR", blank=True, default="")
    programme_pratique = models.TextField(verbose_name="Programme pratique FR", blank=True, default="")
    
    # ========== PROGRAMME STRUCTURE - ARABIC ==========
    programme_structure_ar = models.JSONField(
        verbose_name="Structure du programme AR",
        default=dict,
        blank=True,
        help_text="Structure JSON du programme théorique et pratique AR"
    )
    programme_theorique_ar = models.TextField(verbose_name="Programme théorique AR", blank=True, default="")
    programme_pratique_ar = models.TextField(verbose_name="Programme pratique AR", blank=True, default="")
    
    # ========== PROGRAMME STRUCTURE - ENGLISH ==========
    programme_structure_en = models.JSONField(
        verbose_name="Structure du programme EN",
        default=dict,
        blank=True,
        help_text="Structure JSON du programme théorique et pratique EN"
    )
    programme_theorique_en = models.TextField(verbose_name="Programme théorique EN", blank=True, default="")
    programme_pratique_en = models.TextField(verbose_name="Programme pratique EN", blank=True, default="")
    
    # ========== STATS & BADGES (COMMON) ==========
    success_rate = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=95,
        verbose_name="Taux de réussite (%)"
    )
    badge = models.CharField(
        max_length=20,
        choices=BADGE_CHOICES,
        default='none',
        verbose_name="Badge"
    )
    
    # ========== FLAGS (COMMON) ==========
    is_featured = models.BooleanField(default=False, verbose_name="Formation en vedette", db_index=True)
    is_active = models.BooleanField(default=True, verbose_name="Active", db_index=True)
    
    # ========== MAIN IMAGE (COMMON) ==========
    thumbnail = models.URLField(max_length=500, blank=True, null=True, verbose_name="URL de la miniature")
    programme_pdf_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="URL du programme PDF")
    
    # ========== GALLERY IMAGES - FRENCH CAPTIONS ==========
    gallery_image_1 = models.URLField(max_length=500, blank=True, null=True, verbose_name="Image galerie 1")
    gallery_caption_1 = models.CharField(max_length=200, blank=True, verbose_name="Légende image 1 FR")
    gallery_image_2 = models.URLField(max_length=500, blank=True, null=True, verbose_name="Image galerie 2")
    gallery_caption_2 = models.CharField(max_length=200, blank=True, verbose_name="Légende image 2 FR")
    gallery_image_3 = models.URLField(max_length=500, blank=True, null=True, verbose_name="Image galerie 3")
    gallery_caption_3 = models.CharField(max_length=200, blank=True, verbose_name="Légende image 3 FR")
    gallery_image_4 = models.URLField(max_length=500, blank=True, null=True, verbose_name="Image galerie 4")
    gallery_caption_4 = models.CharField(max_length=200, blank=True, verbose_name="Légende image 4 FR")
    gallery_image_5 = models.URLField(max_length=500, blank=True, null=True, verbose_name="Image galerie 5")
    gallery_caption_5 = models.CharField(max_length=200, blank=True, verbose_name="Légende image 5 FR")
    
    # ========== GALLERY IMAGES - ARABIC CAPTIONS ==========
    gallery_caption_1_ar = models.CharField(max_length=200, blank=True, verbose_name="Légende image 1 AR")
    gallery_caption_2_ar = models.CharField(max_length=200, blank=True, verbose_name="Légende image 2 AR")
    gallery_caption_3_ar = models.CharField(max_length=200, blank=True, verbose_name="Légende image 3 AR")
    gallery_caption_4_ar = models.CharField(max_length=200, blank=True, verbose_name="Légende image 4 AR")
    gallery_caption_5_ar = models.CharField(max_length=200, blank=True, verbose_name="Légende image 5 AR")
    
    # ========== GALLERY IMAGES - ENGLISH CAPTIONS ==========
    gallery_caption_1_en = models.CharField(max_length=200, blank=True, verbose_name="Légende image 1 EN")
    gallery_caption_2_en = models.CharField(max_length=200, blank=True, verbose_name="Légende image 2 EN")
    gallery_caption_3_en = models.CharField(max_length=200, blank=True, verbose_name="Légende image 3 EN")
    gallery_caption_4_en = models.CharField(max_length=200, blank=True, verbose_name="Légende image 4 EN")
    gallery_caption_5_en = models.CharField(max_length=200, blank=True, verbose_name="Légende image 5 EN")
    
    # ========== CERTIFICATE IMAGES - FRENCH ==========
    certificate_image_1 = models.URLField(max_length=500, blank=True, null=True, verbose_name="Certificat 1 - URL")
    certificate_name_1 = models.CharField(max_length=200, blank=True, verbose_name="Certificat 1 - Nom FR")
    certificate_desc_1 = models.TextField(blank=True, verbose_name="Certificat 1 - Description FR")
    certificate_image_2 = models.URLField(max_length=500, blank=True, null=True, verbose_name="Certificat 2 - URL")
    certificate_name_2 = models.CharField(max_length=200, blank=True, verbose_name="Certificat 2 - Nom FR")
    certificate_desc_2 = models.TextField(blank=True, verbose_name="Certificat 2 - Description FR")
    certificate_image_3 = models.URLField(max_length=500, blank=True, null=True, verbose_name="Certificat 3 - URL")
    certificate_name_3 = models.CharField(max_length=200, blank=True, verbose_name="Certificat 3 - Nom FR")
    certificate_desc_3 = models.TextField(blank=True, verbose_name="Certificat 3 - Description FR")
    
    # ========== CERTIFICATE IMAGES - ARABIC ==========
    certificate_name_1_ar = models.CharField(max_length=200, blank=True, verbose_name="Certificat 1 - Nom AR")
    certificate_desc_1_ar = models.TextField(blank=True, verbose_name="Certificat 1 - Description AR")
    certificate_name_2_ar = models.CharField(max_length=200, blank=True, verbose_name="Certificat 2 - Nom AR")
    certificate_desc_2_ar = models.TextField(blank=True, verbose_name="Certificat 2 - Description AR")
    certificate_name_3_ar = models.CharField(max_length=200, blank=True, verbose_name="Certificat 3 - Nom AR")
    certificate_desc_3_ar = models.TextField(blank=True, verbose_name="Certificat 3 - Description AR")
    
    # ========== CERTIFICATE IMAGES - ENGLISH ==========
    certificate_name_1_en = models.CharField(max_length=200, blank=True, verbose_name="Certificat 1 - Nom EN")
    certificate_desc_1_en = models.TextField(blank=True, verbose_name="Certificat 1 - Description EN")
    certificate_name_2_en = models.CharField(max_length=200, blank=True, verbose_name="Certificat 2 - Nom EN")
    certificate_desc_2_en = models.TextField(blank=True, verbose_name="Certificat 2 - Description EN")
    certificate_name_3_en = models.CharField(max_length=200, blank=True, verbose_name="Certificat 3 - Nom EN")
    certificate_desc_3_en = models.TextField(blank=True, verbose_name="Certificat 3 - Description EN")
    
    # ========== LICENSE IMAGES (COMMON) ==========
    license_recto_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="URL licence recto")
    license_verso_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="URL licence verso")
    
    # ========== AVAILABLE CITIES (COMMON) ==========
    available_casablanca = models.BooleanField(default=True, verbose_name="Disponible à Casablanca")
    available_rabat = models.BooleanField(default=True, verbose_name="Disponible à Rabat")
    available_tanger = models.BooleanField(default=False, verbose_name="Disponible à Tanger")
    available_marrakech = models.BooleanField(default=False, verbose_name="Disponible à Marrakech")
    available_agadir = models.BooleanField(default=False, verbose_name="Disponible à Agadir")
    available_fes = models.BooleanField(default=False, verbose_name="Disponible à Fès")
    available_meknes = models.BooleanField(default=False, verbose_name="Disponible à Meknès")
    available_oujda = models.BooleanField(default=False, verbose_name="Disponible à Oujda")
    available_laayoune = models.BooleanField(default=False, verbose_name="Disponible à Laâyoune")
    available_dakhla = models.BooleanField(default=False, verbose_name="Disponible à Dakhla")
    available_other = models.BooleanField(default=False, verbose_name="Disponible autre ville")
    
    # ========== STATISTICS - FRENCH ==========
    stat_employment_rate = models.CharField(max_length=50, blank=True, default="95%", verbose_name="Taux d'emploi FR")
    stat_student_satisfaction = models.CharField(max_length=50, blank=True, default="4.8/5", verbose_name="Satisfaction FR")
    stat_exam_success = models.CharField(max_length=50, blank=True, default="98%", verbose_name="Taux de réussite FR")
    stat_average_salary = models.CharField(max_length=50, blank=True, default="8500 MAD", verbose_name="Salaire moyen FR")
    stat_company_partnerships = models.CharField(max_length=50, blank=True, default="50+", verbose_name="Entreprises partenaires FR")
    
    # ========== STATISTICS - ARABIC ==========
    stat_employment_rate_ar = models.CharField(max_length=50, blank=True, default="٪٩٥", verbose_name="Taux d'emploi AR")
    stat_student_satisfaction_ar = models.CharField(max_length=50, blank=True, default="٤٫٨/٥", verbose_name="Satisfaction AR")
    stat_exam_success_ar = models.CharField(max_length=50, blank=True, default="٪٩٨", verbose_name="Taux de réussite AR")
    stat_average_salary_ar = models.CharField(max_length=50, blank=True, default="٨٥٠٠ درهم", verbose_name="Salaire moyen AR")
    stat_company_partnerships_ar = models.CharField(max_length=50, blank=True, default="٥٠+", verbose_name="Entreprises partenaires AR")
    
    # ========== STATISTICS - ENGLISH ==========
    stat_employment_rate_en = models.CharField(max_length=50, blank=True, default="95%", verbose_name="Employment rate EN")
    stat_student_satisfaction_en = models.CharField(max_length=50, blank=True, default="4.8/5", verbose_name="Student satisfaction EN")
    stat_exam_success_en = models.CharField(max_length=50, blank=True, default="98%", verbose_name="Exam success rate EN")
    stat_average_salary_en = models.CharField(max_length=50, blank=True, default="8500 MAD", verbose_name="Average salary EN")
    stat_company_partnerships_en = models.CharField(max_length=50, blank=True, default="50+", verbose_name="Company partnerships EN")
    
    # ========== FEATURES - FRENCH ==========
    feature_1 = models.CharField(max_length=200, blank=True, verbose_name="Fonctionnalité 1 FR")
    feature_2 = models.CharField(max_length=200, blank=True, verbose_name="Fonctionnalité 2 FR")
    feature_3 = models.CharField(max_length=200, blank=True, verbose_name="Fonctionnalité 3 FR")
    feature_4 = models.CharField(max_length=200, blank=True, verbose_name="Fonctionnalité 4 FR")
    feature_5 = models.CharField(max_length=200, blank=True, verbose_name="Fonctionnalité 5 FR")
    
    # ========== FEATURES - ARABIC ==========
    feature_1_ar = models.CharField(max_length=200, blank=True, verbose_name="خاصية 1 AR")
    feature_2_ar = models.CharField(max_length=200, blank=True, verbose_name="خاصية 2 AR")
    feature_3_ar = models.CharField(max_length=200, blank=True, verbose_name="خاصية 3 AR")
    feature_4_ar = models.CharField(max_length=200, blank=True, verbose_name="خاصية 4 AR")
    feature_5_ar = models.CharField(max_length=200, blank=True, verbose_name="خاصية 5 AR")
    
    # ========== FEATURES - ENGLISH ==========
    feature_1_en = models.CharField(max_length=200, blank=True, verbose_name="Feature 1 EN")
    feature_2_en = models.CharField(max_length=200, blank=True, verbose_name="Feature 2 EN")
    feature_3_en = models.CharField(max_length=200, blank=True, verbose_name="Feature 3 EN")
    feature_4_en = models.CharField(max_length=200, blank=True, verbose_name="Feature 4 EN")
    feature_5_en = models.CharField(max_length=200, blank=True, verbose_name="Feature 5 EN")
    
    # ========== PREREQUISITES - FRENCH ==========
    prerequisite_1 = models.CharField(max_length=200, blank=True, verbose_name="Prérequis 1 FR")
    prerequisite_2 = models.CharField(max_length=200, blank=True, verbose_name="Prérequis 2 FR")
    prerequisite_3 = models.CharField(max_length=200, blank=True, verbose_name="Prérequis 3 FR")
    prerequisite_4 = models.CharField(max_length=200, blank=True, verbose_name="Prérequis 4 FR")
    prerequisite_5 = models.CharField(max_length=200, blank=True, verbose_name="Prérequis 5 FR")
    
    # ========== PREREQUISITES - ARABIC ==========
    prerequisite_1_ar = models.CharField(max_length=200, blank=True, verbose_name="المتطلبات المسبقة 1 AR")
    prerequisite_2_ar = models.CharField(max_length=200, blank=True, verbose_name="المتطلبات المسبقة 2 AR")
    prerequisite_3_ar = models.CharField(max_length=200, blank=True, verbose_name="المتطلبات المسبقة 3 AR")
    prerequisite_4_ar = models.CharField(max_length=200, blank=True, verbose_name="المتطلبات المسبقة 4 AR")
    prerequisite_5_ar = models.CharField(max_length=200, blank=True, verbose_name="المتطلبات المسبقة 5 AR")
    
    # ========== PREREQUISITES - ENGLISH ==========
    prerequisite_1_en = models.CharField(max_length=200, blank=True, verbose_name="Prerequisite 1 EN")
    prerequisite_2_en = models.CharField(max_length=200, blank=True, verbose_name="Prerequisite 2 EN")
    prerequisite_3_en = models.CharField(max_length=200, blank=True, verbose_name="Prerequisite 3 EN")
    prerequisite_4_en = models.CharField(max_length=200, blank=True, verbose_name="Prerequisite 4 EN")
    prerequisite_5_en = models.CharField(max_length=200, blank=True, verbose_name="Prerequisite 5 EN")
    
    # ========== FAQs - FRENCH ==========
    faq_question_1 = models.CharField(max_length=300, blank=True, verbose_name="FAQ Question 1 FR")
    faq_answer_1 = models.TextField(blank=True, verbose_name="FAQ Réponse 1 FR")
    faq_question_2 = models.CharField(max_length=300, blank=True, verbose_name="FAQ Question 2 FR")
    faq_answer_2 = models.TextField(blank=True, verbose_name="FAQ Réponse 2 FR")
    faq_question_3 = models.CharField(max_length=300, blank=True, verbose_name="FAQ Question 3 FR")
    faq_answer_3 = models.TextField(blank=True, verbose_name="FAQ Réponse 3 FR")
    faq_question_4 = models.CharField(max_length=300, blank=True, verbose_name="FAQ Question 4 FR")
    faq_answer_4 = models.TextField(blank=True, verbose_name="FAQ Réponse 4 FR")
    faq_question_5 = models.CharField(max_length=300, blank=True, verbose_name="FAQ Question 5 FR")
    faq_answer_5 = models.TextField(blank=True, verbose_name="FAQ Réponse 5 FR")
    
    # ========== FAQs - ARABIC ==========
    faq_question_1_ar = models.CharField(max_length=300, blank=True, verbose_name="سؤال FAQ 1 AR")
    faq_answer_1_ar = models.TextField(blank=True, verbose_name="جواب FAQ 1 AR")
    faq_question_2_ar = models.CharField(max_length=300, blank=True, verbose_name="سؤال FAQ 2 AR")
    faq_answer_2_ar = models.TextField(blank=True, verbose_name="جواب FAQ 2 AR")
    faq_question_3_ar = models.CharField(max_length=300, blank=True, verbose_name="سؤال FAQ 3 AR")
    faq_answer_3_ar = models.TextField(blank=True, verbose_name="جواب FAQ 3 AR")
    faq_question_4_ar = models.CharField(max_length=300, blank=True, verbose_name="سؤال FAQ 4 AR")
    faq_answer_4_ar = models.TextField(blank=True, verbose_name="جواب FAQ 4 AR")
    faq_question_5_ar = models.CharField(max_length=300, blank=True, verbose_name="سؤال FAQ 5 AR")
    faq_answer_5_ar = models.TextField(blank=True, verbose_name="جواب FAQ 5 AR")
    
    # ========== FAQs - ENGLISH ==========
    faq_question_1_en = models.CharField(max_length=300, blank=True, verbose_name="FAQ Question 1 EN")
    faq_answer_1_en = models.TextField(blank=True, verbose_name="FAQ Answer 1 EN")
    faq_question_2_en = models.CharField(max_length=300, blank=True, verbose_name="FAQ Question 2 EN")
    faq_answer_2_en = models.TextField(blank=True, verbose_name="FAQ Answer 2 EN")
    faq_question_3_en = models.CharField(max_length=300, blank=True, verbose_name="FAQ Question 3 EN")
    faq_answer_3_en = models.TextField(blank=True, verbose_name="FAQ Answer 3 EN")
    faq_question_4_en = models.CharField(max_length=300, blank=True, verbose_name="FAQ Question 4 EN")
    faq_answer_4_en = models.TextField(blank=True, verbose_name="FAQ Answer 4 EN")
    faq_question_5_en = models.CharField(max_length=300, blank=True, verbose_name="FAQ Question 5 EN")
    faq_answer_5_en = models.TextField(blank=True, verbose_name="FAQ Answer 5 EN")
    
    # ========== TESTIMONIALS - FRENCH ==========
    testimonial_name_1 = models.CharField(max_length=100, blank=True, verbose_name="Témoin 1 - Nom FR")
    testimonial_review_1 = models.TextField(blank=True, verbose_name="Témoin 1 - Témoignage FR")
    testimonial_rating_1 = models.PositiveIntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Témoin 1 - Note (1-5)")
    testimonial_position_1 = models.CharField(max_length=100, blank=True, verbose_name="Témoin 1 - Poste FR")
    testimonial_name_2 = models.CharField(max_length=100, blank=True, verbose_name="Témoin 2 - Nom FR")
    testimonial_review_2 = models.TextField(blank=True, verbose_name="Témoin 2 - Témoignage FR")
    testimonial_rating_2 = models.PositiveIntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Témoin 2 - Note (1-5)")
    testimonial_position_2 = models.CharField(max_length=100, blank=True, verbose_name="Témoin 2 - Poste FR")
    testimonial_name_3 = models.CharField(max_length=100, blank=True, verbose_name="Témoin 3 - Nom FR")
    testimonial_review_3 = models.TextField(blank=True, verbose_name="Témoin 3 - Témoignage FR")
    testimonial_rating_3 = models.PositiveIntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Témoin 3 - Note (1-5)")
    testimonial_position_3 = models.CharField(max_length=100, blank=True, verbose_name="Témoin 3 - Poste FR")
    
    # ========== TESTIMONIALS - ARABIC ==========
    testimonial_name_1_ar = models.CharField(max_length=100, blank=True, verbose_name="شاهد 1 - اسم AR")
    testimonial_review_1_ar = models.TextField(blank=True, verbose_name="شاهد 1 - شهادة AR")
    testimonial_position_1_ar = models.CharField(max_length=100, blank=True, verbose_name="شاهد 1 - منصب AR")
    testimonial_name_2_ar = models.CharField(max_length=100, blank=True, verbose_name="شاهد 2 - اسم AR")
    testimonial_review_2_ar = models.TextField(blank=True, verbose_name="شاهد 2 - شهادة AR")
    testimonial_position_2_ar = models.CharField(max_length=100, blank=True, verbose_name="شاهد 2 - منصب AR")
    testimonial_name_3_ar = models.CharField(max_length=100, blank=True, verbose_name="شاهد 3 - اسم AR")
    testimonial_review_3_ar = models.TextField(blank=True, verbose_name="شاهد 3 - شهادة AR")
    testimonial_position_3_ar = models.CharField(max_length=100, blank=True, verbose_name="شاهد 3 - منصب AR")
    
    # ========== TESTIMONIALS - ENGLISH ==========
    testimonial_name_1_en = models.CharField(max_length=100, blank=True, verbose_name="Witness 1 - Name EN")
    testimonial_review_1_en = models.TextField(blank=True, verbose_name="Witness 1 - Testimonial EN")
    testimonial_position_1_en = models.CharField(max_length=100, blank=True, verbose_name="Witness 1 - Position EN")
    testimonial_name_2_en = models.CharField(max_length=100, blank=True, verbose_name="Witness 2 - Name EN")
    testimonial_review_2_en = models.TextField(blank=True, verbose_name="Witness 2 - Testimonial EN")
    testimonial_position_2_en = models.CharField(max_length=100, blank=True, verbose_name="Witness 2 - Position EN")
    testimonial_name_3_en = models.CharField(max_length=100, blank=True, verbose_name="Witness 3 - Name EN")
    testimonial_review_3_en = models.TextField(blank=True, verbose_name="Witness 3 - Testimonial EN")
    testimonial_position_3_en = models.CharField(max_length=100, blank=True, verbose_name="Witness 3 - Position EN")
    
    # ========== CATEGORIES (COMMON) ==========
    category_caces = models.BooleanField(default=False, verbose_name="Catégorie CACES Engins", db_index=True)
    category_electricite = models.BooleanField(default=False, verbose_name="Catégorie Électricité", db_index=True)
    category_soudage = models.BooleanField(default=False, verbose_name="Catégorie Soudage", db_index=True)
    category_securite = models.BooleanField(default=False, verbose_name="Catégorie Sécurité", db_index=True)
    category_management = models.BooleanField(default=False, verbose_name="Catégorie Management", db_index=True)
    category_autre = models.BooleanField(default=False, verbose_name="Catégorie Autre", db_index=True)
    
    # ========== NEXT SESSION (COMMON) ==========
    next_session = models.DateField(null=True, blank=True, verbose_name="Prochaine session")
    
    # ========== SCHEDULE (COMMON) ==========
    schedule_json = models.JSONField(
        verbose_name="Calendrier de formation",
        default=list,
        blank=True,
        help_text="Calendrier JSON des sessions"
    )
    
    # ========== TIMESTAMPS (COMMON) ==========
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création", db_index=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    
    # ========== ANALYTICS (COMMON) ==========
    view_count = models.PositiveIntegerField(default=0, verbose_name="Nombre de vues")
    inquiry_count = models.PositiveIntegerField(default=0, verbose_name="Nombre de demandes")
    enrollment_count = models.PositiveIntegerField(default=0, verbose_name="Nombre d'inscriptions")
    
    class Meta:
        verbose_name = "Formation"
        verbose_name_plural = "Formations"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', 'created_at']),
            models.Index(fields=['is_featured', 'is_active']),
            models.Index(fields=['category_caces', 'is_active']),
            models.Index(fields=['category_electricite', 'is_active']),
            models.Index(fields=['category_soudage', 'is_active']),
            models.Index(fields=['price_mad', 'is_active']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Generate slugs if not provided
        if not self.slug:
            self.slug = slugify(self.title)
        if not self.slug_ar and self.title_ar:
            self.slug_ar = slugify(self.title_ar)
        if not self.slug_en and self.title_en:
            self.slug_en = slugify(self.title_en)
        
        # Ensure JSON fields have proper defaults
        if not self.programme_structure:
            self.programme_structure = self.get_default_programme_structure()
        if not self.programme_structure_ar:
            self.programme_structure_ar = self.get_default_programme_structure()
        if not self.programme_structure_en:
            self.programme_structure_en = self.get_default_programme_structure()
        
        if not self.schedule_json:
            self.schedule_json = self.get_default_schedule()
        
        super().save(*args, **kwargs)
    
    # ========== GETTER METHODS FOR MULTILINGUAL CONTENT ==========
    
    def get_title(self, lang='fr'):
        """Get title in specified language"""
        if lang == 'ar' and self.title_ar:
            return self.title_ar
        elif lang == 'en' and self.title_en:
            return self.title_en
        return self.title
    
    def get_slug(self, lang='fr'):
        """Get slug in specified language"""
        if lang == 'ar' and self.slug_ar:
            return self.slug_ar
        elif lang == 'en' and self.slug_en:
            return self.slug_en
        return self.slug
    
    def get_short_description(self, lang='fr'):
        """Get short description in specified language"""
        if lang == 'ar' and self.short_description_ar:
            return self.short_description_ar
        elif lang == 'en' and self.short_description_en:
            return self.short_description_en
        return self.short_description
    
    def get_detailed_description(self, lang='fr'):
        """Get detailed description in specified language"""
        if lang == 'ar' and self.detailed_description_ar:
            return self.detailed_description_ar
        elif lang == 'en' and self.detailed_description_en:
            return self.detailed_description_en
        return self.detailed_description
    
    def get_objectives(self, lang='fr'):
        """Get objectives in specified language"""
        if lang == 'ar' and self.objectives_ar:
            return self.objectives_ar
        elif lang == 'en' and self.objectives_en:
            return self.objectives_en
        return self.objectives
    
    def get_programme_structure_data(self, lang='fr'):
        """Get programme structure in specified language"""
        if lang == 'ar' and self.programme_structure_ar:
            return self.programme_structure_ar
        elif lang == 'en' and self.programme_structure_en:
            return self.programme_structure_en
        return self.programme_structure
    
    def get_programme_theorique(self, lang='fr'):
        """Get theoretical programme in specified language"""
        if lang == 'ar' and self.programme_theorique_ar:
            return self.programme_theorique_ar
        elif lang == 'en' and self.programme_theorique_en:
            return self.programme_theorique_en
        return self.programme_theorique
    
    def get_programme_pratique(self, lang='fr'):
        """Get practical programme in specified language"""
        if lang == 'ar' and self.programme_pratique_ar:
            return self.programme_pratique_ar
        elif lang == 'en' and self.programme_pratique_en:
            return self.programme_pratique_en
        return self.programme_pratique
    
    def get_gallery_caption(self, image_num, lang='fr'):
        """Get gallery caption in specified language"""
        captions_fr = {
            1: self.gallery_caption_1,
            2: self.gallery_caption_2,
            3: self.gallery_caption_3,
            4: self.gallery_caption_4,
            5: self.gallery_caption_5,
        }
        
        captions_ar = {
            1: self.gallery_caption_1_ar,
            2: self.gallery_caption_2_ar,
            3: self.gallery_caption_3_ar,
            4: self.gallery_caption_4_ar,
            5: self.gallery_caption_5_ar,
        }
        
        captions_en = {
            1: self.gallery_caption_1_en,
            2: self.gallery_caption_2_en,
            3: self.gallery_caption_3_en,
            4: self.gallery_caption_4_en,
            5: self.gallery_caption_5_en,
        }
        
        if lang == 'ar' and captions_ar.get(image_num):
            return captions_ar[image_num]
        elif lang == 'en' and captions_en.get(image_num):
            return captions_en[image_num]
        return captions_fr.get(image_num, '')
    
    def get_certificate_name(self, cert_num, lang='fr'):
        """Get certificate name in specified language"""
        names_fr = {1: self.certificate_name_1, 2: self.certificate_name_2, 3: self.certificate_name_3}
        names_ar = {1: self.certificate_name_1_ar, 2: self.certificate_name_2_ar, 3: self.certificate_name_3_ar}
        names_en = {1: self.certificate_name_1_en, 2: self.certificate_name_2_en, 3: self.certificate_name_3_en}
        
        if lang == 'ar' and names_ar.get(cert_num):
            return names_ar[cert_num]
        elif lang == 'en' and names_en.get(cert_num):
            return names_en[cert_num]
        return names_fr.get(cert_num, '')
    
    def get_certificate_desc(self, cert_num, lang='fr'):
        """Get certificate description in specified language"""
        descs_fr = {1: self.certificate_desc_1, 2: self.certificate_desc_2, 3: self.certificate_desc_3}
        descs_ar = {1: self.certificate_desc_1_ar, 2: self.certificate_desc_2_ar, 3: self.certificate_desc_3_ar}
        descs_en = {1: self.certificate_desc_1_en, 2: self.certificate_desc_2_en, 3: self.certificate_desc_3_en}
        
        if lang == 'ar' and descs_ar.get(cert_num):
            return descs_ar[cert_num]
        elif lang == 'en' and descs_en.get(cert_num):
            return descs_en[cert_num]
        return descs_fr.get(cert_num, '')
    
    def get_stat_employment_rate(self, lang='fr'):
        """Get employment rate stat in specified language"""
        if lang == 'ar' and self.stat_employment_rate_ar:
            return self.stat_employment_rate_ar
        elif lang == 'en' and self.stat_employment_rate_en:
            return self.stat_employment_rate_en
        return self.stat_employment_rate
    
    def get_stat_student_satisfaction(self, lang='fr'):
        """Get student satisfaction stat in specified language"""
        if lang == 'ar' and self.stat_student_satisfaction_ar:
            return self.stat_student_satisfaction_ar
        elif lang == 'en' and self.stat_student_satisfaction_en:
            return self.stat_student_satisfaction_en
        return self.stat_student_satisfaction
    
    def get_stat_exam_success(self, lang='fr'):
        """Get exam success stat in specified language"""
        if lang == 'ar' and self.stat_exam_success_ar:
            return self.stat_exam_success_ar
        elif lang == 'en' and self.stat_exam_success_en:
            return self.stat_exam_success_en
        return self.stat_exam_success
    
    def get_stat_average_salary(self, lang='fr'):
        """Get average salary stat in specified language"""
        if lang == 'ar' and self.stat_average_salary_ar:
            return self.stat_average_salary_ar
        elif lang == 'en' and self.stat_average_salary_en:
            return self.stat_average_salary_en
        return self.stat_average_salary
    
    def get_stat_company_partnerships(self, lang='fr'):
        """Get company partnerships stat in specified language"""
        if lang == 'ar' and self.stat_company_partnerships_ar:
            return self.stat_company_partnerships_ar
        elif lang == 'en' and self.stat_company_partnerships_en:
            return self.stat_company_partnerships_en
        return self.stat_company_partnerships
    
    def get_feature(self, num, lang='fr'):
        """Get feature in specified language"""
        features_fr = {1: self.feature_1, 2: self.feature_2, 3: self.feature_3, 4: self.feature_4, 5: self.feature_5}
        features_ar = {1: self.feature_1_ar, 2: self.feature_2_ar, 3: self.feature_3_ar, 4: self.feature_4_ar, 5: self.feature_5_ar}
        features_en = {1: self.feature_1_en, 2: self.feature_2_en, 3: self.feature_3_en, 4: self.feature_4_en, 5: self.feature_5_en}
        
        if lang == 'ar' and features_ar.get(num):
            return features_ar[num]
        elif lang == 'en' and features_en.get(num):
            return features_en[num]
        return features_fr.get(num, '')
    
    def get_prerequisite(self, num, lang='fr'):
        """Get prerequisite in specified language"""
        prereqs_fr = {1: self.prerequisite_1, 2: self.prerequisite_2, 3: self.prerequisite_3, 4: self.prerequisite_4, 5: self.prerequisite_5}
        prereqs_ar = {1: self.prerequisite_1_ar, 2: self.prerequisite_2_ar, 3: self.prerequisite_3_ar, 4: self.prerequisite_4_ar, 5: self.prerequisite_5_ar}
        prereqs_en = {1: self.prerequisite_1_en, 2: self.prerequisite_2_en, 3: self.prerequisite_3_en, 4: self.prerequisite_4_en, 5: self.prerequisite_5_en}
        
        if lang == 'ar' and prereqs_ar.get(num):
            return prereqs_ar[num]
        elif lang == 'en' and prereqs_en.get(num):
            return prereqs_en[num]
        return prereqs_fr.get(num, '')
    
    def get_faq_question(self, num, lang='fr'):
        """Get FAQ question in specified language"""
        questions_fr = {1: self.faq_question_1, 2: self.faq_question_2, 3: self.faq_question_3, 4: self.faq_question_4, 5: self.faq_question_5}
        questions_ar = {1: self.faq_question_1_ar, 2: self.faq_question_2_ar, 3: self.faq_question_3_ar, 4: self.faq_question_4_ar, 5: self.faq_question_5_ar}
        questions_en = {1: self.faq_question_1_en, 2: self.faq_question_2_en, 3: self.faq_question_3_en, 4: self.faq_question_4_en, 5: self.faq_question_5_en}
        
        if lang == 'ar' and questions_ar.get(num):
            return questions_ar[num]
        elif lang == 'en' and questions_en.get(num):
            return questions_en[num]
        return questions_fr.get(num, '')
    
    def get_faq_answer(self, num, lang='fr'):
        """Get FAQ answer in specified language"""
        answers_fr = {1: self.faq_answer_1, 2: self.faq_answer_2, 3: self.faq_answer_3, 4: self.faq_answer_4, 5: self.faq_answer_5}
        answers_ar = {1: self.faq_answer_1_ar, 2: self.faq_answer_2_ar, 3: self.faq_answer_3_ar, 4: self.faq_answer_4_ar, 5: self.faq_answer_5_ar}
        answers_en = {1: self.faq_answer_1_en, 2: self.faq_answer_2_en, 3: self.faq_answer_3_en, 4: self.faq_answer_4_en, 5: self.faq_answer_5_en}
        
        if lang == 'ar' and answers_ar.get(num):
            return answers_ar[num]
        elif lang == 'en' and answers_en.get(num):
            return answers_en[num]
        return answers_fr.get(num, '')
    
    def get_testimonial_name(self, num, lang='fr'):
        """Get testimonial name in specified language"""
        names_fr = {1: self.testimonial_name_1, 2: self.testimonial_name_2, 3: self.testimonial_name_3}
        names_ar = {1: self.testimonial_name_1_ar, 2: self.testimonial_name_2_ar, 3: self.testimonial_name_3_ar}
        names_en = {1: self.testimonial_name_1_en, 2: self.testimonial_name_2_en, 3: self.testimonial_name_3_en}
        
        if lang == 'ar' and names_ar.get(num):
            return names_ar[num]
        elif lang == 'en' and names_en.get(num):
            return names_en[num]
        return names_fr.get(num, '')
    
    def get_testimonial_review(self, num, lang='fr'):
        """Get testimonial review in specified language"""
        reviews_fr = {1: self.testimonial_review_1, 2: self.testimonial_review_2, 3: self.testimonial_review_3}
        reviews_ar = {1: self.testimonial_review_1_ar, 2: self.testimonial_review_2_ar, 3: self.testimonial_review_3_ar}
        reviews_en = {1: self.testimonial_review_1_en, 2: self.testimonial_review_2_en, 3: self.testimonial_review_3_en}
        
        if lang == 'ar' and reviews_ar.get(num):
            return reviews_ar[num]
        elif lang == 'en' and reviews_en.get(num):
            return reviews_en[num]
        return reviews_fr.get(num, '')
    
    def get_testimonial_position(self, num, lang='fr'):
        """Get testimonial position in specified language"""
        positions_fr = {1: self.testimonial_position_1, 2: self.testimonial_position_2, 3: self.testimonial_position_3}
        positions_ar = {1: self.testimonial_position_1_ar, 2: self.testimonial_position_2_ar, 3: self.testimonial_position_3_ar}
        positions_en = {1: self.testimonial_position_1_en, 2: self.testimonial_position_2_en, 3: self.testimonial_position_3_en}
        
        if lang == 'ar' and positions_ar.get(num):
            return positions_ar[num]
        elif lang == 'en' and positions_en.get(num):
            return positions_en[num]
        return positions_fr.get(num, '')
    
    # ========== UTILITY METHODS ==========
    
    def get_default_programme_structure(self):
        """Return default programme structure"""
        return {
            "theorique": {
                "percentage": 40,
                "modules": [
                    {
                        "title": "Introduction aux concepts de base",
                        "duration": "8 heures",
                        "objectives": [
                            "Comprendre les concepts fondamentaux",
                            "Maîtriser les règles de sécurité",
                            "Connaître les normes applicables"
                        ]
                    }
                ]
            },
            "pratique": {
                "percentage": 60,
                "modules": [
                    {
                        "title": "Pratique encadrée",
                        "duration": "16 heures",
                        "objectives": [
                            "Manipulation des équipements",
                            "Application des procédures",
                            "Exercices supervisés"
                        ]
                    }
                ]
            }
        }
    
    def get_default_schedule(self):
        """Return default schedule"""
        return [
            {
                "week": "Semaine 1",
                "description": "Introduction et théorie de base",
                "theoretical_hours": 20,
                "practical_hours": 10
            }
        ]
    
    def get_available_cities(self):
        """Get list of available cities"""
        cities = []
        if self.available_casablanca: cities.append('Casablanca')
        if self.available_rabat: cities.append('Rabat')
        if self.available_tanger: cities.append('Tanger')
        if self.available_marrakech: cities.append('Marrakech')
        if self.available_agadir: cities.append('Agadir')
        if self.available_fes: cities.append('Fès')
        if self.available_meknes: cities.append('Meknès')
        if self.available_oujda: cities.append('Oujda')
        if self.available_laayoune: cities.append('Laâyoune')
        if self.available_dakhla: cities.append('Dakhla')
        if self.available_other: cities.append('Autre')
        return cities
    
    def get_gallery_images(self, lang='fr'):
        """Get gallery images as list of dicts"""
        gallery = []
        images = [
            (self.gallery_image_1, 1),
            (self.gallery_image_2, 2),
            (self.gallery_image_3, 3),
            (self.gallery_image_4, 4),
            (self.gallery_image_5, 5)
        ]
        
        for url, num in images:
            if url:
                gallery.append({
                    'url': url,
                    'caption': self.get_gallery_caption(num, lang),
                    'id': num
                })
        return gallery
    
    def get_certificates(self, lang='fr'):
        """Get certificates as list of dicts"""
        certificates = []
        images = [
            (self.certificate_image_1, 1),
            (self.certificate_image_2, 2),
            (self.certificate_image_3, 3)
        ]
        
        for url, num in images:
            if url:
                certificates.append({
                    'url': url,
                    'name': self.get_certificate_name(num, lang),
                    'description': self.get_certificate_desc(num, lang),
                    'id': num
                })
        return certificates
    
    def get_features(self, lang='fr'):
        """Get features as list"""
        features = []
        for i in range(1, 6):
            feature = self.get_feature(i, lang)
            if feature:
                features.append(feature)
        return features
    
    def get_prerequisites(self, lang='fr'):
        """Get prerequisites as list"""
        prerequisites = []
        for i in range(1, 6):
            prerequisite = self.get_prerequisite(i, lang)
            if prerequisite:
                prerequisites.append(prerequisite)
        return prerequisites
    
    def get_faqs(self, lang='fr'):
        """Get FAQs as list of dicts"""
        faqs = []
        for i in range(1, 6):
            question = self.get_faq_question(i, lang)
            answer = self.get_faq_answer(i, lang)
            if question and answer:
                faqs.append({
                    'question': question,
                    'answer': answer,
                    'id': i
                })
        return faqs
    
    def get_testimonials(self, lang='fr'):
        """Get testimonials as list of dicts"""
        testimonials = []
        for i in range(1, 4):
            name = self.get_testimonial_name(i, lang)
            review = self.get_testimonial_review(i, lang)
            position = self.get_testimonial_position(i, lang)
            rating = getattr(self, f'testimonial_rating_{i}')
            
            if name and review:
                testimonials.append({
                    'name': name,
                    'review': review,
                    'rating': rating,
                    'position': position,
                    'id': i
                })
        return testimonials
    
    def get_categories(self):
        """Get categories as list"""
        categories = []
        if self.category_caces: categories.append('CACES Engins')
        if self.category_electricite: categories.append('Électricité')
        if self.category_soudage: categories.append('Soudage')
        if self.category_securite: categories.append('Sécurité')
        if self.category_management: categories.append('Management')
        if self.category_autre: categories.append('Autre')
        return categories
    
    def get_objectives_list(self, lang='fr'):
        """Parse objectives text into list"""
        objectives_text = self.get_objectives(lang)
        if not objectives_text:
            return []
        objectives = [obj.strip() for obj in objectives_text.split('\n') if obj.strip()]
        return objectives
    
    def get_programme_theorique_list(self, lang='fr'):
        """Parse theoretical programme into list"""
        programme_text = self.get_programme_theorique(lang)
        if not programme_text:
            return []
        items = [item.strip() for item in programme_text.split('\n') if item.strip()]
        return items
    
    def get_programme_pratique_list(self, lang='fr'):
        """Parse practical programme into list"""
        programme_text = self.get_programme_pratique(lang)
        if not programme_text:
            return []
        items = [item.strip() for item in programme_text.split('\n') if item.strip()]
        return items
    
    def get_structured_programme(self, lang='fr'):
        """Get structured programme data"""
        return self.get_programme_structure_data(lang)
    
    def get_schedule(self):
        """Get schedule data"""
        if not self.schedule_json:
            return self.get_default_schedule()
        return self.schedule_json
    
    def get_price_in_currency(self, currency_code):
        """Convert MAD to specified currency"""
        try:
            currency_rate = CurrencyRate.objects.filter(currency_code=currency_code).first()
            if currency_rate and currency_rate.rate_to_mad and currency_rate.rate_to_mad > 0:
                converted_price = self.price_mad * currency_rate.rate_to_mad
                return Decimal(str(round(converted_price, 2)))
            
            default_rates = {'EUR': Decimal('0.093'), 'USD': Decimal('0.100'), 'GBP': Decimal('0.079'), 'CAD': Decimal('0.136'), 'AED': Decimal('0.367')}
            rate = default_rates.get(currency_code, Decimal('1.0'))
            return self.price_mad * rate
            
        except Exception:
            return self.price_mad
    
    def increment_view_count(self):
        """Increment view count atomically"""
        self.view_count = models.F('view_count') + 1
        self.save(update_fields=['view_count'])
    
    def increment_inquiry_count(self):
        """Increment inquiry count atomically"""
        self.inquiry_count = models.F('inquiry_count') + 1
        self.save(update_fields=['inquiry_count'])

# ========== OTHER MODELS (UNCHANGED) ==========

class TrainingPreSubscription(models.Model):
    """Pre-subscription model for demo payments"""
    training = models.ForeignKey(Training, on_delete=models.CASCADE, verbose_name="Formation", related_name='presubscriptions')
    full_name = models.CharField(max_length=200, verbose_name="Nom complet")
    email = models.EmailField(verbose_name="Adresse email")
    phone = models.CharField(max_length=20, verbose_name="Téléphone")
    city = models.CharField(max_length=100, verbose_name="Ville")
    
    # Payment details
    payment_method = models.CharField(
        max_length=50, 
        choices=[
            ('card', 'Carte bancaire'),
            ('bank_transfer', 'Virement bancaire'),
            ('cash', 'Paiement sur place'),
        ],
        verbose_name="Méthode de paiement"
    )
    
    # Card details
    card_last_four = models.CharField(max_length=4, blank=True, verbose_name="4 derniers chiffres de la carte")
    card_expiry = models.CharField(max_length=5, blank=True, verbose_name="Date d'expiration")
    
    # Bank transfer details
    transfer_confirmation = models.TextField(blank=True, verbose_name="Confirmation de virement")
    transfer_reference = models.CharField(max_length=100, blank=True, verbose_name="Référence virement")
    
    # Demo payment info
    transaction_id = models.UUIDField(default=uuid.uuid4, unique=True, verbose_name="ID de transaction")
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'En attente'),
            ('processing', 'En traitement'),
            ('completed', 'Complété'),
            ('failed', 'Échoué'),
        ],
        default='pending',
        verbose_name="Statut du paiement"
    )
    
    # Amounts
    original_price_mad = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix original (MAD)")
    paid_price_mad = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant payé (MAD)")
    currency_used = models.CharField(max_length=3, default='MAD', verbose_name="Devise utilisée")
    
    # Receipt
    receipt_generated = models.BooleanField(default=False, verbose_name="Reçu généré")
    receipt_pdf_url = models.URLField(max_length=500, blank=True, verbose_name="URL du reçu PDF")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    payment_completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Date de paiement")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="Adresse IP")
    user_agent = models.TextField(blank=True, verbose_name="User Agent")
    session_id = models.CharField(max_length=100, blank=True, verbose_name="ID de session")
    
    class Meta:
        verbose_name = "Pré-inscription"
        verbose_name_plural = "Pré-inscriptions"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['training', 'payment_status']),
            models.Index(fields=['email', 'created_at']),
            models.Index(fields=['transaction_id']),
        ]
    
    def __str__(self):
        return f"Pré-inscription: {self.full_name} - {self.training.title}"
    
    def generate_receipt_pdf(self):
        """Generate receipt PDF"""
        try:
            receipt_dir = os.path.join(settings.MEDIA_ROOT, 'receipts')
            os.makedirs(receipt_dir, exist_ok=True)
            
            filename = f"receipt_{self.transaction_id}.pdf"
            filepath = os.path.join(receipt_dir, filename)
            
            doc = SimpleDocTemplate(
                filepath,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            story = []
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                textColor=colors.HexColor('#34745c')
            )
            
            story.append(Paragraph("REÇU DE PRÉ-INSCRIPTION", title_style))
            story.append(Spacer(1, 20))
            
            company_info = """
            <b>DIRAY CENTRE</b><br/>
            Formation Professionnelle<br/>
            Téléphone: +212 779 25 99 42<br/>
            Email: contact@diraycentre.ma<br/>
            """
            story.append(Paragraph(company_info, styles["Normal"]))
            story.append(Spacer(1, 20))
            
            receipt_data = [
                ["Référence:", str(self.transaction_id)],
                ["Date:", self.created_at.strftime("%d/%m/%Y %H:%M")],
                ["Client:", self.full_name],
                ["Email:", self.email],
                ["Téléphone:", self.phone],
                ["Ville:", self.city],
                ["Formation:", self.training.title],
                ["Méthode de paiement:", self.get_payment_method_display()],
                ["Montant:", f"{self.paid_price_mad} {self.currency_used}"],
                ["Statut:", self.get_payment_status_display()],
            ]
            
            table = Table(receipt_data, colWidths=[200, 300])
            table.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 1, colors.grey),
                ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#f8f9fa')),
                ('PADDING', (0,0), (-1,-1), 10),
                ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ]))
            
            story.append(table)
            story.append(Spacer(1, 30))
            
            if self.payment_method == 'bank_transfer':
                bank_account = CompanyBankAccount.get_active_account()
                if bank_account:
                    payment_details = f"""
                    <b>Coordonnées bancaires pour virement:</b><br/>
                    <br/>
                    Banque: {bank_account.bank_name}<br/>
                    Titulaire: {bank_account.account_holder}<br/>
                    RIB: {bank_account.rib}<br/>
                    IBAN: {bank_account.iban or 'N/A'}<br/>
                    <br/>
                    <b>Important:</b> Veuillez envoyer la capture d'écran de votre virement à {bank_account.confirmation_email}
                    """
                    story.append(Paragraph(payment_details, styles["Normal"]))
                    story.append(Spacer(1, 20))
            
            terms = """
            <b>Conditions générales:</b><br/>
            1. Cette pré-inscription sera confirmée après réception du paiement.<br/>
            2. Pour toute annulation, veuillez nous contacter au moins 7 jours avant.<br/>
            3. Les frais d'annulation tardive peuvent s'appliquer.<br/>
            4. Conservez ce reçu pour toute réclamation.<br/>
            """
            story.append(Paragraph(terms, styles["Normal"]))
            
            doc.build(story)
            
            self.receipt_pdf_url = f"{settings.MEDIA_URL}receipts/{filename}"
            self.receipt_generated = True
            self.save(update_fields=['receipt_pdf_url', 'receipt_generated'])
            
            return self.receipt_pdf_url
            
        except Exception as e:
            print(f"Error generating PDF receipt: {e}")
            import traceback
            traceback.print_exc()
            return None

class Promotion(models.Model):
    """Promotional offers and discounts"""
    title = models.CharField(max_length=200, verbose_name="Titre de la promotion")
    subtitle = models.CharField(max_length=300, blank=True, verbose_name="Sous-titre")
    description = models.TextField(verbose_name="Description")
    
    # Multilingual fields
    title_ar = models.CharField(max_length=200, blank=True, verbose_name="Titre de la promotion AR")
    subtitle_ar = models.CharField(max_length=300, blank=True, verbose_name="Sous-titre AR")
    description_ar = models.TextField(blank=True, verbose_name="Description AR")
    
    title_en = models.CharField(max_length=200, blank=True, verbose_name="Promotion title EN")
    subtitle_en = models.CharField(max_length=300, blank=True, verbose_name="Subtitle EN")
    description_en = models.TextField(blank=True, verbose_name="Description EN")
    
    # Pricing
    original_price_mad = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix original (MAD)")
    promotional_price_mad = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix promotionnel (MAD)")
    discount_percentage = models.PositiveIntegerField(verbose_name="Pourcentage de réduction")
    
    # Visual
    background_color = models.CharField(max_length=50, default="#34745C", verbose_name="Couleur de fond")
    text_color = models.CharField(max_length=50, default="#FFFFFF", verbose_name="Couleur du texte")
    badge_text = models.CharField(max_length=50, default="PROMO", verbose_name="Texte du badge")
    
    # Multilingual badge text
    badge_text_ar = models.CharField(max_length=50, blank=True, default="عرض", verbose_name="نص الشارة AR")
    badge_text_en = models.CharField(max_length=50, blank=True, default="PROMO", verbose_name="Badge text EN")
    
    # Settings
    is_active = models.BooleanField(default=True, verbose_name="Active")
    valid_until = models.DateField(verbose_name="Valide jusqu'au")
    max_uses = models.PositiveIntegerField(default=100, verbose_name="Utilisations maximum")
    current_uses = models.PositiveIntegerField(default=0, verbose_name="Utilisations actuelles")
    
    # Associated training
    training = models.ForeignKey(Training, on_delete=models.CASCADE, verbose_name="Formation associée")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    
    class Meta:
        verbose_name = "Promotion"
        verbose_name_plural = "Promotions"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.discount_percentage}% de réduction"
    
    def get_title_lang(self, lang='fr'):
        if lang == 'ar' and self.title_ar:
            return self.title_ar
        elif lang == 'en' and self.title_en:
            return self.title_en
        return self.title
    
    def get_subtitle_lang(self, lang='fr'):
        if lang == 'ar' and self.subtitle_ar:
            return self.subtitle_ar
        elif lang == 'en' and self.subtitle_en:
            return self.subtitle_en
        return self.subtitle
    
    def get_description_lang(self, lang='fr'):
        if lang == 'ar' and self.description_ar:
            return self.description_ar
        elif lang == 'en' and self.description_en:
            return self.description_en
        return self.description
    
    def get_badge_text_lang(self, lang='fr'):
        if lang == 'ar' and self.badge_text_ar:
            return self.badge_text_ar
        elif lang == 'en' and self.badge_text_en:
            return self.badge_text_en
        return self.badge_text
    
    def get_price_in_currency(self, currency_code):
        """Get promotional price in specified currency"""
        try:
            currency_rate = CurrencyRate.objects.filter(currency_code=currency_code).first()
            if currency_rate and currency_rate.rate_to_mad and currency_rate.rate_to_mad > 0:
                converted_price = self.promotional_price_mad * currency_rate.rate_to_mad
                return Decimal(str(round(converted_price, 2)))
            
            default_rates = {'EUR': Decimal('0.093'), 'USD': Decimal('0.100'), 'GBP': Decimal('0.079')}
            rate = default_rates.get(currency_code, Decimal('1.0'))
            return self.promotional_price_mad * rate
            
        except Exception:
            return self.promotional_price_mad
    
    def can_use(self):
        """Check if promotion can still be used"""
        from django.utils import timezone
        return (
            self.is_active and 
            self.current_uses < self.max_uses and 
            (not self.valid_until or self.valid_until >= timezone.now().date())
        )

class City(models.Model):
    """Cities model"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Nom de la ville")
    region = models.CharField(max_length=20, choices=REGION_CHOICES, default='central', verbose_name="Région")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Numéro de téléphone")
    map_x = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="Position X sur la carte (%)")
    map_y = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="Position Y sur la carte (%)")
    is_headquarters = models.BooleanField(default=False, verbose_name="Siège social")
    address = models.TextField(blank=True, verbose_name="Adresse complète")
    is_active = models.BooleanField(default=True, verbose_name="Active")
    
    class Meta:
        verbose_name = "Ville"
        verbose_name_plural = "Villes"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class CompanyBankAccount(models.Model):
    """Company bank account details for wire transfers"""
    
    company_name = models.CharField(max_length=200, default="DIRAY CENTRE", verbose_name="Nom de la société")
    bank_name = models.CharField(max_length=200, default="Attijariwafa Bank", verbose_name="Nom de la banque")
    account_holder = models.CharField(max_length=200, default="DIRAY CENTRE", verbose_name="Titulaire du compte")
    rib = models.CharField(max_length=50, verbose_name="RIB (Relevé d'Identité Bancaire)")
    iban = models.CharField(max_length=50, blank=True, verbose_name="IBAN")
    swift_bic = models.CharField(max_length=20, blank=True, verbose_name="Code SWIFT/BIC")
    branch_name = models.CharField(max_length=200, blank=True, verbose_name="Nom de l'agence")
    branch_code = models.CharField(max_length=20, blank=True, verbose_name="Code agence")
    account_number = models.CharField(max_length=50, blank=True, verbose_name="Numéro de compte")
    
    # Contact info
    confirmation_email = models.EmailField(default="contact@diraycentre.ma", verbose_name="Email de confirmation")
    whatsapp_number = models.CharField(max_length=20, default="+212779259942", verbose_name="Numéro WhatsApp")
    
    is_active = models.BooleanField(default=True, verbose_name="Compte actif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")
    
    class Meta:
        verbose_name = "Compte bancaire d'entreprise"
        verbose_name_plural = "Comptes bancaires d'entreprise"
        ordering = ['-is_active', '-created_at']
    
    def __str__(self):
        return f"{self.company_name} - {self.bank_name}"
    
    @classmethod
    def get_active_account(cls):
        """Get the active bank account"""
        return cls.objects.filter(is_active=True).first()

class ContactRequest(models.Model):
    """Contact form submissions"""
    
    REQUEST_TYPE_CHOICES = [
        ('training', 'Demande de formation'),
        ('migration', 'Service de migration'),
        ('information', 'Demande d\'information'),
        ('partnership', 'Partenariat'),
        ('other', 'Autre'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('card', 'Carte bancaire'),
        ('bank_transfer', 'Virement bancaire'),
        ('cash', 'Paiement sur place'),
    ]
    
    # Contact Information
    full_name = models.CharField(max_length=200, verbose_name="Nom complet")
    email = models.EmailField(verbose_name="Adresse email")
    phone = models.CharField(max_length=20, verbose_name="Téléphone")
    city = models.CharField(max_length=100, verbose_name="Ville")
    country = models.CharField(max_length=100, default="Maroc", verbose_name="Pays")
    
    # Request Details
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPE_CHOICES, verbose_name="Type de demande")
    message = models.TextField(verbose_name="Message")
    
    # Payment Details
    payment_method = models.CharField(
        max_length=20, 
        choices=PAYMENT_METHOD_CHOICES,
        blank=True,
        verbose_name="Méthode de paiement"
    )
    
    # Card details
    card_last_four = models.CharField(max_length=4, blank=True, verbose_name="4 derniers chiffres carte")
    card_expiry = models.CharField(max_length=5, blank=True, verbose_name="Date d'expiration")
    
    # Bank transfer details
    transfer_confirmation = models.TextField(blank=True, verbose_name="Confirmation de virement")
    transfer_screenshot_url = models.URLField(max_length=500, blank=True, verbose_name="URL capture virement")
    transfer_reference = models.CharField(max_length=100, blank=True, verbose_name="Référence virement")
    transfer_date = models.DateField(null=True, blank=True, verbose_name="Date du virement")
    
    # Training specific
    training_title = models.CharField(max_length=200, blank=True, verbose_name="Formation concernée")
    training = models.ForeignKey(Training, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Formation")
    
    # Status and Scoring
    status = models.CharField(max_length=20, choices=[
        ('new', 'Nouveau'),
        ('contacted', 'Contacté'),
        ('processing', 'En traitement'),
        ('completed', 'Traité'),
        ('archived', 'Archivé')
    ], default='new', verbose_name="Statut")
    
    payment_status = models.CharField(max_length=20, choices=[
        ('pending', 'En attente'),
        ('processing', 'En traitement'),
        ('completed', 'Complété'),
        ('failed', 'Échoué'),
    ], default='pending', verbose_name="Statut du paiement")
    
    lead_score = models.PositiveIntegerField(default=0, verbose_name="Score du lead (0-100)")
    is_threat = models.BooleanField(default=False, verbose_name="Menace potentielle")
    threat_reason = models.CharField(max_length=200, blank=True, verbose_name="Raison de la menace")
    
    # Metadata
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de soumission", db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="Adresse IP")
    user_agent = models.TextField(blank=True, verbose_name="User Agent")
    session_id = models.CharField(max_length=100, blank=True, verbose_name="ID de session")
    
    class Meta:
        verbose_name = "Demande de contact"
        verbose_name_plural = "Demandes de contact"
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['status', 'submitted_at']),
            models.Index(fields=['payment_method', 'payment_status']),
            models.Index(fields=['lead_score']),
        ]
    
    def __str__(self):
        return f"Demande de {self.full_name} - {self.get_request_type_display()}"
    
    def generate_receipt_pdf(self):
        """Generate receipt PDF for payment"""
        try:
            receipt_dir = os.path.join(settings.MEDIA_ROOT, 'receipts')
            os.makedirs(receipt_dir, exist_ok=True)
            
            filename = f"receipt_{self.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            filepath = os.path.join(receipt_dir, filename)
            
            doc = SimpleDocTemplate(
                filepath,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            story = []
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                textColor=colors.HexColor('#34745c')
            )
            
            story.append(Paragraph("REÇU DE PAIEMENT", title_style))
            story.append(Spacer(1, 20))
            
            company_info = f"""
            <b>DIRAY CENTRE</b><br/>
            Formation Professionnelle & Services de Migration<br/>
            Téléphone: +212 779 25 99 42<br/>
            Email: contact@diraycentre.ma<br/>
            """
            story.append(Paragraph(company_info, styles["Normal"]))
            story.append(Spacer(1, 20))
            
            receipt_data = [
                ["Référence:", f"RC-{self.id:06d}"],
                ["Date:", self.submitted_at.strftime("%d/%m/%Y %H:%M")],
                ["Client:", self.full_name],
                ["Email:", self.email],
                ["Téléphone:", self.phone],
                ["Formation:", self.training_title or "N/A"],
                ["Méthode de paiement:", self.get_payment_method_display()],
                ["Statut:", self.get_payment_status_display()],
            ]
            
            if self.payment_method == 'bank_transfer' and self.transfer_reference:
                receipt_data.append(["Référence virement:", self.transfer_reference])
            
            table = Table(receipt_data, colWidths=[200, 300])
            table.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 1, colors.grey),
                ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#f8f9fa')),
                ('PADDING', (0,0), (-1,-1), 10),
                ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ]))
            
            story.append(table)
            story.append(Spacer(1, 30))
            
            terms = """
            <b>Conditions générales:</b><br/>
            1. Ce reçu atteste de l'inscription à la formation mentionnée ci-dessus.<br/>
            2. Pour toute annulation, veuillez nous contacter au moins 7 jours avant le début de la formation.<br/>
            3. Les frais d'annulation tardive peuvent s'appliquer.<br/>
            4. Pour toute question, contactez-nous par email ou téléphone.<br/>
            """
            story.append(Paragraph(terms, styles["Normal"]))
            
            doc.build(story)
            
            return f"{settings.MEDIA_URL}receipts/{filename}"
            
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return None

# ========== ANALYTICS MODELS ==========

class PageView(models.Model):
    """Track page views"""
    url = models.CharField(max_length=500, verbose_name="URL visitée")
    page_title = models.CharField(max_length=200, blank=True, verbose_name="Titre de la page")
    referrer = models.CharField(max_length=500, blank=True, verbose_name="Referrer")
    session_id = models.CharField(max_length=100, verbose_name="ID de session")
    ip_address = models.GenericIPAddressField(verbose_name="Adresse IP")
    user_agent = models.TextField(verbose_name="User Agent")
    city = models.CharField(max_length=100, blank=True, verbose_name="Ville détectée")
    country = models.CharField(max_length=100, blank=True, verbose_name="Pays détecté")
    device_type = models.CharField(max_length=50, blank=True, verbose_name="Type d'appareil")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Horodatage", db_index=True)
    
    class Meta:
        verbose_name = "Vue de page"
        verbose_name_plural = "Vues de page"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['session_id', 'timestamp']),
            models.Index(fields=['city', 'timestamp']),
            models.Index(fields=['url', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.url} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

class ClickEvent(models.Model):
    """Track button/link clicks"""
    element_type = models.CharField(max_length=50, verbose_name="Type d'élément")
    element_text = models.CharField(max_length=200, blank=True, verbose_name="Texte de l'élément")
    element_id = models.CharField(max_length=100, blank=True, verbose_name="ID de l'élément")
    url = models.CharField(max_length=500, verbose_name="URL de la page")
    session_id = models.CharField(max_length=100, verbose_name="ID de session")
    ip_address = models.GenericIPAddressField(verbose_name="Adresse IP")
    city = models.CharField(max_length=100, blank=True, verbose_name="Ville")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Horodatage")
    
    class Meta:
        verbose_name = "Événement de clic"
        verbose_name_plural = "Événements de clic"
        ordering = ['-timestamp']

class PhoneCall(models.Model):
    """Track phone calls"""
    phone_number = models.CharField(max_length=20, verbose_name="Numéro appelé")
    caller_city = models.CharField(max_length=100, blank=True, verbose_name="Ville de l'appelant")
    caller_country = models.CharField(max_length=100, blank=True, verbose_name="Pays de l'appelant")
    url = models.CharField(max_length=500, blank=True, verbose_name="URL source")
    session_id = models.CharField(max_length=100, verbose_name="ID de session")
    ip_address = models.GenericIPAddressField(verbose_name="Adresse IP")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Horodatage")
    
    class Meta:
        verbose_name = "Appel téléphonique"
        verbose_name_plural = "Appels téléphoniques"
        ordering = ['-timestamp']

class WhatsAppClick(models.Model):
    """Track WhatsApp button clicks"""
    phone_number = models.CharField(max_length=20, verbose_name="Numéro WhatsApp")
    message_prefill = models.TextField(blank=True, verbose_name="Message pré-rempli")
    url = models.CharField(max_length=500, blank=True, verbose_name="URL source")
    session_id = models.CharField(max_length=100, verbose_name="ID de session")
    ip_address = models.GenericIPAddressField(verbose_name="Adresse IP")
    city = models.CharField(max_length=100, blank=True, verbose_name="Ville")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Horodatage")
    
    class Meta:
        verbose_name = "Clic WhatsApp"
        verbose_name_plural = "Clics WhatsApp"
        ordering = ['-timestamp']

class FormSubmission(models.Model):
    """Track form submissions"""
    form_type = models.CharField(max_length=50, verbose_name="Type de formulaire")
    training_title = models.CharField(max_length=200, blank=True, verbose_name="Formation concernée")
    session_id = models.CharField(max_length=100, verbose_name="ID de session")
    ip_address = models.GenericIPAddressField(verbose_name="Adresse IP")
    city = models.CharField(max_length=100, blank=True, verbose_name="Ville")
    country = models.CharField(max_length=100, blank=True, verbose_name="Pays")
    time_spent = models.IntegerField(default=0, verbose_name="Temps passé sur le formulaire (secondes)")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Horodatage")
    
    class Meta:
        verbose_name = "Soumission de formulaire"
        verbose_name_plural = "Soumissions de formulaire"
        ordering = ['-timestamp']

class VisitorSession(models.Model):
    """Track visitor sessions"""
    session_id = models.CharField(max_length=100, unique=True, verbose_name="ID de session")
    ip_address = models.GenericIPAddressField(verbose_name="Adresse IP")
    user_agent = models.TextField(verbose_name="User Agent")
    city = models.CharField(max_length=100, blank=True, verbose_name="Ville")
    country = models.CharField(max_length=100, blank=True, verbose_name="Pays")
    device_type = models.CharField(max_length=50, blank=True, verbose_name="Type d'appareil")
    browser = models.CharField(max_length=100, blank=True, verbose_name="Navigateur")
    os = models.CharField(max_length=100, blank=True, verbose_name="Système d'exploitation")
    referrer = models.CharField(max_length=500, blank=True, verbose_name="Referrer")
    landing_page = models.CharField(max_length=500, verbose_name="Page d'arrivée")
    start_time = models.DateTimeField(auto_now_add=True, verbose_name="Heure de début", db_index=True)
    last_activity = models.DateTimeField(auto_now=True, verbose_name="Dernière activité")
    page_views = models.IntegerField(default=1, verbose_name="Nombre de pages vues")
    session_duration = models.IntegerField(default=0, verbose_name="Durée de session (secondes)")
    
    class Meta:
        verbose_name = "Session visiteur"
        verbose_name_plural = "Sessions visiteurs"
        ordering = ['-start_time']

class DailyStat(models.Model):
    """Daily aggregated statistics"""
    date = models.DateField(unique=True, verbose_name="Date")
    total_visitors = models.IntegerField(default=0, verbose_name="Visiteurs totaux")
    total_pageviews = models.IntegerField(default=0, verbose_name="Pages vues totales")
    total_form_submissions = models.IntegerField(default=0, verbose_name="Soumissions de formulaire")
    total_phone_calls = models.IntegerField(default=0, verbose_name="Appels téléphoniques")
    total_whatsapp_clicks = models.IntegerField(default=0, verbose_name="Clics WhatsApp")
    avg_session_duration = models.IntegerField(default=0, verbose_name="Durée moyenne de session (s)")
    top_city = models.CharField(max_length=100, blank=True, verbose_name="Ville principale")
    top_training = models.CharField(max_length=200, blank=True, verbose_name="Formation la plus vue")
    
    class Meta:
        verbose_name = "Statistique quotidienne"
        verbose_name_plural = "Statistiques quotidiennes"
        ordering = ['-date']
    
    def __str__(self):
        return f"Stats du {self.date}"

class CurrencyRate(models.Model):
    """Currency exchange rates"""
    currency_code = models.CharField(max_length=3, unique=True, verbose_name="Code devise")
    currency_name = models.CharField(max_length=50, verbose_name="Nom de la devise", default="")
    country = models.CharField(max_length=100, verbose_name="Pays", default="")
    flag = models.CharField(max_length=10, verbose_name="Drapeau", default="🏳️")
    rate_to_mad = models.DecimalField(max_digits=10, decimal_places=6, verbose_name="Taux de change vers MAD", default=Decimal('1.000000'))
    last_updated = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")
    
    class Meta:
        verbose_name = "Taux de change"
        verbose_name_plural = "Taux de change"
        ordering = ['currency_code']
    
    def __str__(self):
        return f"1 {self.currency_code} = {self.rate_to_mad} MAD"

# ========== NEW FEATURES ==========

class TrainingWaitlist(models.Model):
    """Training waitlist for full sessions"""
    training = models.ForeignKey(Training, on_delete=models.CASCADE, verbose_name="Formation", related_name='waitlist')
    email = models.EmailField(verbose_name="Adresse email")
    full_name = models.CharField(max_length=200, verbose_name="Nom complet")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    preferred_session = models.DateField(null=True, blank=True, verbose_name="Session préférée")
    city = models.CharField(max_length=100, verbose_name="Ville")
    notified = models.BooleanField(default=False, verbose_name="Notifié")
    notes = models.TextField(blank=True, verbose_name="Notes")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'inscription")
    
    class Meta:
        verbose_name = "Liste d'attente"
        verbose_name_plural = "Listes d'attente"
        ordering = ['created_at']
        unique_together = ['training', 'email']
    
    def __str__(self):
        return f"{self.full_name} - {self.training.title}"





# In models.py - Update the TrainingReview model
class TrainingReview(models.Model):
    """Training reviews from verified students"""
    training = models.ForeignKey(Training, on_delete=models.CASCADE, verbose_name="Formation", related_name='reviews')
    contact_request = models.ForeignKey(ContactRequest, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Demande originale")
    full_name = models.CharField(max_length=100, verbose_name="Nom complet")
    email = models.EmailField(verbose_name="Email")
    
    # Avatar field - ADD THIS
    avatar = models.CharField(max_length=100, blank=True, default='', verbose_name="Avatar")
    
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Note (1-5)")
    title = models.CharField(max_length=200, verbose_name="Titre du commentaire")
    comment = models.TextField(verbose_name="Commentaire")
    is_verified = models.BooleanField(default=False, verbose_name="Vérifié")
    is_approved = models.BooleanField(default=False, verbose_name="Approuvé pour affichage")
    helpful_count = models.PositiveIntegerField(default=0, verbose_name="Utile")
    not_helpful_count = models.PositiveIntegerField(default=0, verbose_name="Pas utile")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    
    class Meta:
        verbose_name = "Avis sur formation"
        verbose_name_plural = "Avis sur formations"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['training', 'is_approved', 'is_verified']),
            models.Index(fields=['rating', 'is_approved']),
        ]
    
    def __str__(self):
        return f"{self.full_name} - {self.training.title} - {self.rating}★"
    
    def get_helpful_percentage(self):
        """Calculate helpful percentage"""
        total = self.helpful_count + self.not_helpful_count
        if total == 0:
            return 0
        return (self.helpful_count / total) * 100







class ThreatIP(models.Model):
    """Track IP addresses that are potential threats"""
    ip_address = models.GenericIPAddressField(unique=True, verbose_name="Adresse IP")
    reason = models.CharField(max_length=200, verbose_name="Raison")
    threat_level = models.CharField(max_length=20, choices=[('low', 'Faible'), ('medium', 'Moyenne'), ('high', 'Haute')], default='medium', verbose_name="Niveau de menace")
    request_count = models.PositiveIntegerField(default=1, verbose_name="Nombre de requêtes")
    first_detected = models.DateTimeField(auto_now_add=True, verbose_name="Première détection")
    last_detected = models.DateTimeField(auto_now=True, verbose_name="Dernière détection")
    is_blocked = models.BooleanField(default=False, verbose_name="Bloqué")
    
    class Meta:
        verbose_name = "IP Menaçante"
        verbose_name_plural = "IPs Menaçantes"
        ordering = ['-last_detected']
    
    def __str__(self):
        return f"{self.ip_address} - {self.threat_level}"
    
    def increment_request_count(self):
        """Increment request count and update last detected"""
        self.request_count += 1
        self.save(update_fields=['request_count', 'last_detected'])

class RateLimitLog(models.Model):
    """Log rate limit violations"""
    ip_address = models.GenericIPAddressField(verbose_name="Adresse IP")
    endpoint = models.CharField(max_length=200, verbose_name="Endpoint")
    request_count = models.PositiveIntegerField(default=1, verbose_name="Nombre de requêtes")
    period_minutes = models.PositiveIntegerField(default=1, verbose_name="Période (minutes)")
    first_request = models.DateTimeField(auto_now_add=True, verbose_name="Première requête")
    last_request = models.DateTimeField(auto_now=True, verbose_name="Dernière requête")
    is_threat = models.BooleanField(default=False, verbose_name="Menace")
    
    class Meta:
        verbose_name = "Log de Limite de Taux"
        verbose_name_plural = "Logs de Limite de Taux"
        ordering = ['-last_request']
        indexes = [
            models.Index(fields=['ip_address', 'endpoint']),
            models.Index(fields=['is_threat', 'last_request']),
        ]
    
    def __str__(self):
        return f"{self.ip_address} - {self.endpoint}"
# ==========================================
# E-LEARNING EXTENSION MODELS
# ==========================================

class Profile(models.Model):
    """Extended user profile for role management"""
    ROLE_CHOICES = [
        ('STUDENT', 'Étudiant'),
        ('PROFESSOR', 'Professeur'),
        ('ASSISTANT', 'Assistant administratif'),
        ('ADMIN', 'Administrateur'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('ACTIVE', 'Actif'),
        ('SUSPENDED', 'Suspendu'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STUDENT')
    full_name = models.CharField(max_length=200, verbose_name="Nom complet")
    cin_or_passport = models.CharField(max_length=50, unique=True, null=True, blank=True, verbose_name="CIN ou Passeport")
    phone_number = models.CharField(max_length=50, unique=True, verbose_name="Téléphone")
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Ville")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    email_verified = models.BooleanField(default=False, verbose_name="Email vérifié")
    profile_picture = models.URLField(max_length=500, blank=True, default='', verbose_name="Photo de profil")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

class AssistantProfile(models.Model):
    """Specific profile for administrative assistants with city-based responsibility"""
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='assistant_profile', limit_choices_to={'role': 'ASSISTANT'})
    assigned_cities = models.ManyToManyField(City, blank=True, related_name='assistants', verbose_name="Villes assignées")
    notes = models.TextField(blank=True, verbose_name="Notes administratives")

    def __str__(self):
        return f"Assistant: {self.profile.full_name}"

class ProfessorProfile(models.Model):
    """Specific profile for professors"""
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='professor_profile', limit_choices_to={'role': 'PROFESSOR'})
    active = models.BooleanField(default=True, verbose_name="Actif")
    specialization = models.CharField(max_length=200, blank=True, verbose_name="Spécialisation")
    bio = models.TextField(blank=True, verbose_name="Biographie")

    def __str__(self):
        return f"Prof. {self.profile.full_name}"

class Session(models.Model):
    """Classroom session (Live or In-person) - 1 month lifecycle"""
    STATUS_CHOICES = [
        ('CREATED', 'Créée'),
        ('ONGOING', 'En cours'),
        ('COMPLETED', 'Terminée'),
    ]
    
    formations = models.ManyToManyField(Training, related_name='sessions', verbose_name="Formations")
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Ville de la session")
    professor = models.ForeignKey(ProfessorProfile, on_delete=models.PROTECT, related_name='sessions')
    start_date = models.DateField(default=datetime.now, verbose_name="Date de début")
    end_date = models.DateField(default=datetime.now, verbose_name="Date de fin")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CREATED', verbose_name="Statut")
    is_live = models.BooleanField(default=False, verbose_name="Est en direct (Live)")
    is_active = models.BooleanField(default=True, verbose_name="Session active")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name = "Session"
        verbose_name_plural = "Sessions"

    def __str__(self):
        type_str = "LIVE" if self.is_live else (self.city.name if self.city else "Inconnu")
        formation_titles = ", ".join([t.title for t in self.formations.all()[:2]])
        count = self.formations.count()
        if count > 2:
            formation_titles += f" (+{count-2})"
        return f"{formation_titles} - {type_str} - {self.start_date}"

class Seance(models.Model):
    """Individual class seance within a session (2 Theory, 2 Practice)"""
    TYPE_CHOICES = [
        ('THEORIQUE', 'Théorique'),
        ('PRATIQUE', 'Pratique'),
    ]
    
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='seances', verbose_name="Session")
    title = models.CharField(max_length=200, verbose_name="Titre de la séance")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='THEORIQUE', verbose_name="Type")
    date = models.DateField(verbose_name="Date")
    time = models.TimeField(verbose_name="Heure")
    location = models.CharField(max_length=200, blank=True, verbose_name="Lieu/Salle")
    
    class Meta:
        ordering = ['date', 'time']
        verbose_name = "Séance"
        verbose_name_plural = "Séances"

    def __str__(self):
        return f"{self.get_type_display()} - {self.title} ({self.date})"

class StudentProfile(models.Model):
    """Specific profile for students with access control"""
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='student_profile', limit_choices_to={'role': 'STUDENT'})
    authorized_formations = models.ManyToManyField(Training, blank=True, related_name='students', verbose_name="Formations autorisées")
    session = models.ForeignKey(Session, on_delete=models.SET_NULL, null=True, blank=True, related_name='students', verbose_name="Session active")
    
    # Payment Tracking
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Montant payé")
    total_amount_due = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Montant total dû")
    
    def __str__(self):
        return f"Étudiant: {self.profile.full_name}"
        
    @property
    def amount_remaining(self):
        return self.total_amount_due - self.amount_paid

    def calculate_total_amount_due(self):
        """Calculate total amount due based on authorized formations"""
        total = self.authorized_formations.aggregate(total=models.Sum('price_mad'))['total'] or Decimal('0.00')
        if self.total_amount_due != total:
            self.total_amount_due = total
            self.save(update_fields=['total_amount_due'])
        return total

class RecordedVideo(models.Model):
    """VOD content for formations"""
    PROVIDER_CHOICES = [
        ('VDOCIPHER', 'VdoCipher'),
        ('VIMEO', 'Vimeo'),
        ('YOUTUBE', 'YouTube'),
        ('OTHER', 'Autre'),
    ]
    
    training = models.ForeignKey(Training, on_delete=models.CASCADE, related_name='videos')
    title = models.CharField(max_length=200, verbose_name="Titre de la vidéo")
    description = models.TextField(blank=True, verbose_name="Description")
    video_provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES, default='VDOCIPHER', verbose_name="Fournisseur vidéo")
    video_id = models.CharField(max_length=200, blank=True, null=True, verbose_name="ID Vidéo (auprès du fournisseur)")
    duration_seconds = models.IntegerField(default=0, verbose_name="Durée (secondes)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.training.title} - {self.title}"

class LiveRecording(models.Model):
    """Recording of a live stream event"""
    live_stream = models.OneToOneField('Live', on_delete=models.CASCADE, related_name='recording', null=True, blank=True)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='recordings')
    video_provider_id = models.CharField(max_length=200, verbose_name="ID Recording Provider", blank=True)
    recording_url = models.URLField(max_length=500, blank=True, verbose_name="URL de l'enregistrement")
    duration_seconds = models.IntegerField(default=0, verbose_name="Durée (secondes)")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rec: {self.live_stream or self.session}"

class Live(models.Model):
    """Individual live stream event for a session"""
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='lives')
    title = models.CharField(max_length=200, blank=True)
    agora_channel = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Live {self.id} for {self.session}"

class AttendanceLog(models.Model):
    """Log of student attendance in live streams"""
    student = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='attendance_logs', limit_choices_to={'role': 'STUDENT'})
    live_stream = models.ForeignKey(Live, on_delete=models.CASCADE, related_name='attendance_logs', null=True, blank=True)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='attendance_logs')
    join_time = models.DateTimeField()
    leave_time = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(default=0)
    is_muted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.full_name} @ {self.live_stream}"

class VideoProgress(models.Model):
    """Tracking progress on recorded videos"""
    student = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='video_progress', limit_choices_to={'role': 'STUDENT'})
    video = models.ForeignKey(RecordedVideo, on_delete=models.CASCADE, related_name='progress')
    watched_seconds = models.IntegerField(default=0)
    completed = models.BooleanField(default=False)
    last_watched_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'video')

    def __str__(self):
        return f"{self.student.full_name} - {self.video.title} ({self.watched_seconds}s)"

class Question(models.Model):
    """Questions/Comments on videos, scoped to a session"""
    video = models.ForeignKey(RecordedVideo, on_delete=models.CASCADE, related_name='questions')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='questions')
    answered_by = models.ForeignKey(ProfessorProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='answered_questions')
    content = models.TextField()   
    answer_content = models.TextField(blank=True, verbose_name="Réponse")
    is_answered = models.BooleanField(default=False, verbose_name="Répondu")
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Question by {self.student} on {self.video}"

class Notification(models.Model):
    """Global notification system"""
    TYPE_CHOICES = [
        ('info', 'Information'),
        ('success', 'Succès'),
        ('warning', 'Avertissement'),
        ('error', 'Erreur'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    session = models.ForeignKey(Session, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    title = models.CharField(max_length=200, verbose_name="Titre")
    message = models.TextField(verbose_name="Message")
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='info', verbose_name="Type")
    link = models.CharField(max_length=500, blank=True, verbose_name="Lien")
    is_read = models.BooleanField(default=False, verbose_name="Lu")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date")

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.username}"

# ========== SIGNALS FOR AUTOMATED PROFILE CREATION ==========

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically create a Profile whenever a User is created"""
    if created:
        Profile.objects.get_or_create(
            user=instance,
            defaults={
                'full_name': instance.get_full_name() or instance.username,
            }
        )

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Ensure Profile is saved when User is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()

@receiver(post_save, sender=Profile)
def create_role_specific_profile(sender, instance, created, **kwargs):
    """Automatically create sub-profiles based on the Profile role"""
    if instance.role == 'STUDENT':
        StudentProfile.objects.get_or_create(profile=instance)
    elif instance.role == 'PROFESSOR':
        ProfessorProfile.objects.get_or_create(profile=instance)
    elif instance.role == 'ASSISTANT':
        AssistantProfile.objects.get_or_create(profile=instance)
        # Admin doesn't necessarily need a sub-profile, but we can add one if needed
        pass


