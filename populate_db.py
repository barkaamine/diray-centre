# populate_data.py
import os
import django
import random
from datetime import datetime, timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Project.settings')
django.setup()

from diray.models import Training, City, CurrencyRate, ContactRequest

def create_currency_rates():
    """Create currency exchange rates"""
    try:
        CurrencyRate.objects.create(
            base_currency='MAD',
            eur_rate=0.093,
            usd_rate=0.100
        )
        print("✅ Currency rates created")
    except:
        print("ℹ️ Currency rates already exist")

def create_cities():
    """Create sample cities for Morocco"""
    cities_data = [
        {'name': 'Casablanca', 'region': 'central', 'phone': '+212522000000', 
         'map_x': 55.00, 'map_y': 32.00, 'is_headquarters': True, 
         'address': 'Casablanca Finance City'},
        {'name': 'Rabat', 'region': 'central', 'phone': '+212537000000', 
         'map_x': 52.00, 'map_y': 28.00, 'is_headquarters': False,
         'address': 'Centre Ville Rabat'},
        {'name': 'Tanger', 'region': 'north', 'phone': '+212539000000',
         'map_x': 48.00, 'map_y': 35.00, 'is_headquarters': False,
         'address': 'Tanger City Center'},
        {'name': 'Marrakech', 'region': 'south', 'phone': '+212524000000',
         'map_x': 45.00, 'map_y': 40.00, 'is_headquarters': False,
         'address': 'Gueliz, Marrakech'},
        {'name': 'Agadir', 'region': 'coast', 'phone': '+212528000000',
         'map_x': 40.00, 'map_y': 45.00, 'is_headquarters': False,
         'address': 'Agadir Centre'},
    ]
    
    created = 0
    for city_data in cities_data:
        obj, created_flag = City.objects.get_or_create(
            name=city_data['name'],
            defaults=city_data
        )
        if created_flag:
            created += 1
    
    print(f"✅ {created} cities created/updated")

def create_trainings():
    """Create training programs based on Prolean data"""
    
    # Sample gallery images (using placeholder URLs)
    gallery_images = [
        {'url': 'https://i.ibb.co/4RYPCBVz/Lucid-Origin-Ultrarealistic-photograph-of-four-construction-an-1.jpg', 'caption': 'Salle de formation moderne'},
        {'url': 'https://i.ibb.co/4RYPCBVz/Lucid-Origin-Ultrarealistic-photograph-of-four-construction-an-1.jpg', 'caption': 'Pratique en atelier'},
        {'url': 'https://i.ibb.co/4RYPCBVz/Lucid-Origin-Ultrarealistic-photograph-of-four-construction-an-1.jpg', 'caption': 'Équipement professionnel'},
    ]
    
    # Sample certificates
    certificates = [
        {
            'url': 'https://i.ibb.co/4RYPCBVz/Lucid-Origin-Ultrarealistic-photograph-of-four-construction-an-1.jpg',
            'name': 'Certificat Officiel CACES',
            'description': 'Certification reconnue internationalement',
            'issuing_body': 'Ministère du Travail',
            'validity_duration': '5 ans'
        },
        {
            'url': 'https://i.ibb.co/4RYPCBVz/Lucid-Origin-Ultrarealistic-photograph-of-four-construction-an-1.jpg',
            'name': 'Certificat Officiel CACES',
            'description': 'Certification reconnue internationalement',
            'issuing_body': 'Ministère du Travail',
            'validity_duration': '5 ans'
        },
        {
            'url': 'https://i.ibb.co/4RYPCBVz/Lucid-Origin-Ultrarealistic-photograph-of-four-construction-an-1.jpg',
            'name': 'Certificat Officiel CACES',
            'description': 'Certification reconnue internationalement',
            'issuing_body': 'Ministère du Travail',
            'validity_duration': '5 ans'
        }
    ]
    
    # Sample testimonials in Darija (Moroccan Arabic)
    testimonials = [
        {
            'name': 'Mohamed L.',
            'review': 'L\'formation m3a Diray Centre kanet mzyana bzf. L\'mou3almin kaychebho welli, kayfhemo. Jebt certificat w l9it khedma bs7. Chokran bzf!',
            'rating': 5,
            'position': 'Opérateur CACES',
            'city': 'Casablanca'
        },
        {
            'name': 'Fatima Z.',
            'review': 'M3a Diray Centre, l\'formation b7al dar. Kaykhdo wa9t bach yfhemok w y3awenk. Daba khdama f l\'Europe, chokran!',
            'rating': 5,
            'position': 'Soudeuse Certifiée',
            'city': 'Rabat'
        }
    ]
    
    # Sample FAQs
    faqs = [
        {
            'question': 'Combien de temps dure la formation ?',
            'answer': 'La durée varie selon la formation : 2-4 semaines pour les formations intensives, 1-2 mois pour les programmes complets.'
        },
        {
            'question': 'Les certificats sont-ils reconnus internationalement ?',
            'answer': 'Oui, nos certifications sont reconnues dans plus de 40 pays dont la France, le Canada et plusieurs pays européens.'
        }
    ]
    
    # Main training data based on Prolean website
    trainings_data = [
        # ========== CACES FORMATIONS ==========
        {
            'title': 'Formation CACES R489 – Chariots Élévateurs',
            'short_description': 'Formation complète pour la conduite sécurisée des chariots élévateurs frontaux et gerbeurs.',
            'detailed_description': '''Cette formation CACES R489 vous prépare à la conduite professionnelle et sécurisée des chariots élévateurs. 
            
**Programme de formation :**
- Règles de sécurité et prévention des risques
- Conduite pratique des chariots élévateurs
- Maintenance de base et vérifications préalables
- Manutention des charges et stabilité
- Signalisation et communication sur chantier
- Réglementation CACES et obligations légales

**Durée :** 1 mois (les dimanches uniquement)
**Lieu :** Tous nos centres au Maroc
**Certification :** Certificat CACES R489 reconnu internationalement''',
            'price_mad': 2400.00,
            'duration_days': 30,
            'success_rate': 98,
            'max_students': 15,
            'badge': 'popular',
            'is_featured': True,
            'thumbnail': 'https://i.ibb.co/4RYPCBVz/Lucid-Origin-Ultrarealistic-photograph-of-four-construction-an-1.jpg',
            'available_casablanca': True,
            'available_rabat': True,
            'available_tanger': True,
            'available_marrakech': True,
            'available_agadir': True,
            'category_caces': True,
            'stat_employment_rate': '96%',
            'stat_student_satisfaction': '4.8/5',
            'stat_exam_success': '98%',
            'stat_average_salary': '8500 MAD',
            'next_session': datetime.now().date() + timedelta(days=14),
        },
        {
            'title': 'Formation CACES R482 – Engins de Chantier',
            'short_description': 'Conduite professionnelle des engins de chantier : pelles, bulldozers, compacteurs, etc.',
            'detailed_description': 'Formation complète pour la conduite sécurisée des engins de chantier avec certification reconnue.',
            'price_mad': 2500.00,
            'duration_days': 35,
            'success_rate': 97,
            'max_students': 12,
            'badge': 'new',
            'is_featured': True,
            'thumbnail': 'https://i.ibb.co/4RYPCBVz/Lucid-Origin-Ultrarealistic-photograph-of-four-construction-an-1.jpg',
            'available_casablanca': True,
            'available_rabat': True,
            'available_tanger': False,
            'available_marrakech': True,
            'available_agadir': False,
            'category_caces': True,
            'stat_employment_rate': '95%',
            'stat_student_satisfaction': '4.7/5',
            'stat_exam_success': '97%',
            'stat_average_salary': '9000 MAD',
            'next_session': datetime.now().date() + timedelta(days=21),
        },
        {
            'title': 'Formation CACES R485 – Chariots Élévateurs Télescopiques',
            'short_description': 'Manœuvre des gerbeurs automoteurs accompagnants avec formation pratique intensive.',
            'detailed_description': 'Spécialisation dans la conduite des chariots télescopiques avec focus sur la sécurité.',
            'price_mad': 1900.00,
            'duration_days': 25,
            'success_rate': 96,
            'max_students': 10,
            'badge': 'none',
            'is_featured': False,
            'thumbnail': 'https://i.ibb.co/4RYPCBVz/Lucid-Origin-Ultrarealistic-photograph-of-four-construction-an-1.jpg',
            'available_casablanca': True,
            'available_rabat': True,
            'available_tanger': False,
            'available_marrakech': False,
            'available_agadir': False,
            'category_caces': True,
            'next_session': datetime.now().date() + timedelta(days=30),
        },
        {
            'title': 'Formation CACES R490 – Grues de Chargement',
            'short_description': 'Manipulation des grues hydrauliques de chargement sur camions.',
            'detailed_description': 'Formation spécialisée pour les grues de chargement avec certification.',
            'price_mad': 2800.00,
            'duration_days': 40,
            'success_rate': 95,
            'max_students': 8,
            'badge': 'none',
            'is_featured': False,
            'thumbnail': 'https://i.ibb.co/4RYPCBVz/Lucid-Origin-Ultrarealistic-photograph-of-four-construction-an-1.jpg',
            'available_casablanca': True,
            'available_rabat': False,
            'available_tanger': True,
            'available_marrakech': False,
            'available_agadir': True,
            'category_caces': True,
            'next_session': datetime.now().date() + timedelta(days=45),
        },
        
        # ========== ÉLECTRICITÉ ==========
        {
            'title': 'Formation Électricien Bâtiment',
            'short_description': 'Acquisition des bases essentielles des installations électriques domestiques et industrielles.',
            'detailed_description': '''Formation complète en électricité de bâtiment pour devenir électricien professionnel.

**Contenu de la formation :**
- Notions fondamentales d\'électricité
- Lecture des plans et schémas électriques
- Installation des réseaux électriques
- Mise en conformité NFC 15-100
- Dépannage et maintenance
- Sécurité électrique et prévention des risques

**Certification :** Diplôme d\'électricien bâtiment reconnu par l\'État''',
            'price_mad': 2500.00,
            'duration_days': 42,
            'success_rate': 96,
            'max_students': 20,
            'badge': 'popular',
            'is_featured': True,
            'thumbnail': 'https://i.ibb.co/4RYPCBVz/Lucid-Origin-Ultrarealistic-photograph-of-four-construction-an-1.jpg',
            'available_casablanca': True,
            'available_rabat': True,
            'available_tanger': True,
            'available_marrakech': True,
            'available_agadir': True,
            'category_electricite': True,
            'stat_employment_rate': '94%',
            'stat_student_satisfaction': '4.6/5',
            'stat_exam_success': '96%',
            'stat_average_salary': '7500 MAD',
            'next_session': datetime.now().date() + timedelta(days=7),
        },
        
        # ========== SOUDAGE ==========
        {
            'title': 'Formation Soudage',
            'short_description': 'Acquisition des techniques fondamentales d\'assemblage des métaux selon les normes internationales.',
            'detailed_description': 'Formation pratique intensive en techniques de soudage avec certification reconnue.',
            'price_mad': 1500.00,
            'duration_days': 56,
            'success_rate': 95,
            'max_students': 15,
            'badge': 'promo',
            'is_featured': True,
            'thumbnail': 'https://i.ibb.co/4RYPCBVz/Lucid-Origin-Ultrarealistic-photograph-of-four-construction-an-1.jpg',
            'available_casablanca': True,
            'available_rabat': True,
            'available_tanger': True,
            'available_marrakech': False,
            'available_agadir': True,
            'category_soudage': True,
            'stat_employment_rate': '92%',
            'stat_student_satisfaction': '4.5/5',
            'stat_exam_success': '95%',
            'stat_average_salary': '8000 MAD',
            'next_session': datetime.now().date() + timedelta(days=10),
        },
        
        # ========== QUALITÉ ==========
        {
            'title': 'Formation Management de la Qualité',
            'short_description': 'Maîtrise des principes fondamentaux du management de la qualité selon les normes ISO.',
            'detailed_description': 'Formation complète en gestion de la qualité pour les professionnels souhaitant obtenir des certifications ISO.',
            'price_mad': 1500.00,
            'duration_days': 35,
            'success_rate': 97,
            'max_students': 25,
            'badge': 'new',
            'is_featured': False,
            'thumbnail': 'https://i.ibb.co/4RYPCBVz/Lucid-Origin-Ultrarealistic-photograph-of-four-construction-an-1.jpg',
            'available_casablanca': True,
            'available_rabat': True,
            'available_tanger': False,
            'available_marrakech': True,
            'available_agadir': False,
            'category_management': True,
            'stat_employment_rate': '93%',
            'stat_student_satisfaction': '4.7/5',
            'stat_exam_success': '97%',
            'next_session': datetime.now().date() + timedelta(days=28),
        },
        
        # ========== SÉCURITÉ ==========
        {
            'title': 'Formation Sécurité Industrielle HSE',
            'short_description': 'Formation complète en Hygiène, Sécurité et Environnement pour les sites industriels.',
            'detailed_description': 'Certification HSE pour les responsables sécurité en milieu industriel.',
            'price_mad': 3000.00,
            'duration_days': 60,
            'success_rate': 96,
            'max_students': 30,
            'badge': 'none',
            'is_featured': False,
            'thumbnail': 'https://i.ibb.co/4RYPCBVz/Lucid-Origin-Ultrarealistic-photograph-of-four-construction-an-1.jpg',
            'available_casablanca': True,
            'available_rabat': True,
            'available_tanger': False,
            'available_marrakech': False,
            'available_agadir': True,
            'category_securite': True,
            'next_session': datetime.now().date() + timedelta(days=60),
        },
    ]
    
    # Add common features, FAQs, and testimonials to each training
    common_features = [
        'Certification reconnue internationalement',
        'Formateurs experts du secteur',
        'Matériel pédagogique inclus',
        'Plateforme en ligne d\'accompagnement',
        'Suivi personnalisé pendant 6 mois'
    ]
    
    created = 0
    for i, data in enumerate(trainings_data):
        # Create slug from title
        slug = data['title'].lower().replace(' ', '-').replace('–', '').replace(',', '').replace('.', '')
        
        # Set gallery images (different for each training)
        gallery_start_idx = i % 3
        
        # Create training
        training, created_flag = Training.objects.get_or_create(
            title=data['title'],
            defaults={
                'slug': slug[:200],
                'short_description': data['short_description'],
                'detailed_description': data.get('detailed_description', data['short_description']),
                'price_mad': data['price_mad'],
                'duration_days': data['duration_days'],
                'success_rate': data['success_rate'],
                'max_students': data['max_students'],
                'badge': data['badge'],
                'is_featured': data['is_featured'],
                'is_active': True,
                'thumbnail': data['thumbnail'],
                
                # Gallery images
                'gallery_image_1': gallery_images[gallery_start_idx]['url'] if gallery_start_idx == 0 else '',
                'gallery_caption_1': gallery_images[gallery_start_idx]['caption'] if gallery_start_idx == 0 else '',
                'gallery_image_2': gallery_images[(gallery_start_idx + 1) % 3]['url'] if gallery_start_idx == 1 else '',
                'gallery_caption_2': gallery_images[(gallery_start_idx + 1) % 3]['caption'] if gallery_start_idx == 1 else '',
                'gallery_image_3': gallery_images[(gallery_start_idx + 2) % 3]['url'] if gallery_start_idx == 2 else '',
                'gallery_caption_3': gallery_images[(gallery_start_idx + 2) % 3]['caption'] if gallery_start_idx == 2 else '',
                
                # Certificates
                'certificate_image_1': certificates[0]['url'],
                'certificate_name_1': certificates[0]['name'],
                'certificate_desc_1': certificates[0]['description'],
                
                # License images
                'license_recto_url': 'https://i.ibb.co/4RYPCBVz/Lucid-Origin-Ultrarealistic-photograph-of-four-construction-an-1.jpg',
                'license_verso_url': 'https://i.ibb.co/4RYPCBVz/Lucid-Origin-Ultrarealistic-photograph-of-four-construction-an-1.jpg',
                
                # City availability
                'available_casablanca': data['available_casablanca'],
                'available_rabat': data['available_rabat'],
                'available_tanger': data['available_tanger'],
                'available_marrakech': data['available_marrakech'],
                'available_agadir': data['available_agadir'],
                'available_fes': False,
                'available_meknes': False,
                'available_oujda': False,
                'available_laayoune': False,
                'available_dakhla': False,
                'available_other': True,
                
                # Statistics
                'stat_employment_rate': data.get('stat_employment_rate', '95%'),
                'stat_student_satisfaction': data.get('stat_student_satisfaction', '4.5/5'),
                'stat_exam_success': data.get('stat_exam_success', '96%'),
                'stat_average_salary': data.get('stat_average_salary', '8000 MAD'),
                'stat_company_partnerships': '50+',
                
                # Features
                'feature_1': common_features[0],
                'feature_2': common_features[1],
                'feature_3': common_features[2],
                'feature_4': common_features[3],
                'feature_5': common_features[4],
                
                # FAQs
                'faq_question_1': faqs[0]['question'] if i < 4 else 'Quels sont les prérequis ?',
                'faq_answer_1': faqs[0]['answer'] if i < 4 else 'Être âgé d\'au moins 18 ans et avoir le niveau collégial minimum.',
                'faq_question_2': faqs[1]['question'] if i < 4 else 'Y a-t-il des sessions en soirée ?',
                'faq_answer_2': faqs[1]['answer'] if i < 4 else 'Oui, nous proposons des sessions en soirée et le week-end.',
                
                # Testimonials
                'testimonial_name_1': testimonials[0]['name'] if i % 2 == 0 else testimonials[1]['name'],
                'testimonial_review_1': testimonials[0]['review'] if i % 2 == 0 else testimonials[1]['review'],
                'testimonial_rating_1': testimonials[0]['rating'] if i % 2 == 0 else testimonials[1]['rating'],
                'testimonial_position_1': testimonials[0]['position'] if i % 2 == 0 else testimonials[1]['position'],
                
                # Categories
                'category_caces': data.get('category_caces', False),
                'category_electricite': data.get('category_electricite', False),
                'category_soudage': data.get('category_soudage', False),
                'category_securite': data.get('category_securite', False),
                'category_management': data.get('category_management', False),
                'category_autre': data.get('category_autre', False),
                
                # Next session
                'next_session': data.get('next_session'),
            }
        )
        
        if created_flag:
            created += 1
    
    print(f"✅ {created} training programs created/updated")
    return created

def create_sample_contact_requests():
    """Create sample contact requests for testing"""
    sample_requests = [
        {
            'full_name': 'Ahmed Benali',
            'email': 'ahmed.benali@example.com',
            'phone': '+212612345678',
            'city': 'Casablanca',
            'country': 'Maroc',
            'request_type': 'training',
            'message': 'Bonjour, je souhaite des informations sur la formation CACES R489.',
            'training_title': 'Formation CACES R489 – Chariots Élévateurs',
            'status': 'new'
        },
        {
            'full_name': 'Fatima Zahra',
            'email': 'fatima.zahra@example.com',
            'phone': '+212698765432',
            'city': 'Rabat',
            'country': 'Maroc',
            'request_type': 'migration',
            'message': 'Je cherche des informations sur les possibilités de migration après formation.',
            'current_country': 'Maroc',
            'target_country': 'Canada',
            'profession': 'Électricien',
            'status': 'contacted'
        },
    ]
    
    created = 0
    for request_data in sample_requests:
        obj, created_flag = ContactRequest.objects.get_or_create(
            email=request_data['email'],
            phone=request_data['phone'],
            defaults=request_data
        )
        if created_flag:
            created += 1
    
    print(f"✅ {created} sample contact requests created")
    return created

def main():
    """Main function to populate all data"""
    print("🚀 Starting data population for Diray Centre...")
    print("=" * 50)
    
    # Create currency rates
    create_currency_rates()
    
    # Create cities
    create_cities()
    
    # Create training programs
    training_count = create_trainings()
    
    # Create sample contact requests
    contact_count = create_sample_contact_requests()
    
    print("=" * 50)
    print(f"🎉 Data population completed successfully!")
    print(f"📊 Summary:")
    print(f"   - Currency rates: 1 entry")
    print(f"   - Cities: 5 entries")
    print(f"   - Training programs: {training_count} entries")
    print(f"   - Contact requests: {contact_count} entries")
    print("=" * 50)
    print("\n💡 Next steps:")
    print("1. Run the script: python populate_data.py")
    print("2. Check Django admin: http://localhost:8000/admin")
    print("3. Verify all data is correctly populated")
    print("4. Adjust prices, descriptions, or images as needed")

if __name__ == "__main__":
    main()