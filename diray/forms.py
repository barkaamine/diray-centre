import re
from django import forms
from django.core.validators import MinLengthValidator, EmailValidator
from .models import ContactRequest, TrainingReview , TrainingWaitlist, Profile, City
from django.contrib.auth.models import User

class ContactRequestForm(forms.ModelForm):
    """Contact request form with validation"""
    class Meta:
        model = ContactRequest
        fields = ['full_name', 'email', 'phone', 'city', 'country', 
                  'request_type', 'message', 'training_title']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Votre nom complet',
                'minlength': '3',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'email@exemple.com',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '+212 6 12 34 56 78',
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Décrivez votre demande...',
                'rows': 4,
            }),
            'request_type': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def clean_full_name(self):
        full_name = self.cleaned_data.get('full_name', '').strip()
        if len(full_name) < 3:
            raise forms.ValidationError("Le nom doit contenir au moins 3 caractères.")
        return full_name
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        # Basic phone validation
        if phone and not any(char.isdigit() for char in phone):
            raise forms.ValidationError("Veuillez entrer un numéro de téléphone valide.")
        return phone

class TrainingReviewForm(forms.ModelForm):
    """Training review form"""
    class Meta:
        model = TrainingReview
        fields = ['full_name', 'email', 'rating', 'title', 'comment']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Votre nom',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'Votre email',
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Titre de votre avis',
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Partagez votre expérience...',
                'rows': 4,
            }),
            'rating': forms.RadioSelect(choices=[(i, i) for i in range(1, 6)]),
        }
    
    def clean_comment(self):
        comment = self.cleaned_data.get('comment', '').strip()
        if len(comment) < 10:
            raise forms.ValidationError("Le commentaire doit contenir au moins 10 caractères.")
        return comment

class WaitlistForm(forms.ModelForm):
    """Waitlist form"""
    class Meta:
        model = TrainingWaitlist
        fields = ['email', 'full_name', 'phone', 'city']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'email@exemple.com',
            }),
            'full_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Votre nom complet',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '+212 6 12 34 56 78',
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Votre ville',
            }),
        }

class TrainingInquiryForm(forms.Form):
    """Training inquiry form"""
    training_id = forms.IntegerField(widget=forms.HiddenInput())
    full_name = forms.CharField(max_length=200, min_length=3)
    email = forms.EmailField()
    phone = forms.CharField(max_length=20)
    city = forms.CharField(max_length=100)
    country = forms.CharField(max_length=100, initial='Maroc')
    message = forms.CharField(widget=forms.Textarea, required=False)

class MigrationInquiryForm(forms.Form):
    """Migration inquiry form"""
    first_name = forms.CharField(max_length=100, min_length=2)
    last_name = forms.CharField(max_length=100, min_length=2)
    email = forms.EmailField()
    current_country = forms.CharField(max_length=100)
    target_country = forms.CharField(max_length=100)
    profession = forms.CharField(max_length=100)
    message = forms.CharField(widget=forms.Textarea, required=False)

class StudentRegistrationForm(forms.ModelForm):
    """Public registration form for students"""
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': 'form-input', 'placeholder': 'Mot de passe'
        })
    )
    confirm_password = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': 'form-input', 'placeholder': 'Confirmer le mot de passe'
        })
    )
    
    class Meta:
        model = Profile
        fields = ['full_name', 'cin_or_passport', 'phone_number', 'city']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nom complet'}),
            'cin_or_passport': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'CIN ou Passeport'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Téléphone'}),
        }
    
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'email@exemple.com'})
    )

    city = forms.ModelChoiceField(
        queryset=City.objects.all(),
        label="Ville",
        widget=forms.Select(attrs={'class': 'auth-input'}),
        empty_label="Sélectionnez votre ville"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cin_or_passport'].required = False
        self.fields['cin_or_passport'].widget.attrs['placeholder'] = 'CIN ou Passeport (Optionnel)'

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Cet email est déjà utilisé.")
        return email

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone and Profile.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError("Ce numéro de téléphone est déjà utilisé.")
        return phone

    def clean_cin_or_passport(self):
        cin = self.cleaned_data.get('cin_or_passport')
        if cin:
            cin = cin.strip().upper()
            # 🧠 Rule: 1 or 2 letters followed by exactly 6 digits
            cin_regex = r'^[A-Z]{1,2}[0-9]{6}$'
            if not re.match(cin_regex, cin):
                raise forms.ValidationError("Format CIN invalide. Utilisez 1 ou 2 lettres suivies de 6 chiffres (ex: AB123456).")
            
            if Profile.objects.filter(cin_or_passport=cin).exists():
                raise forms.ValidationError("Ce numéro CIN ou Passeport est déjà utilisé.")
        return cin


    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return cleaned_data