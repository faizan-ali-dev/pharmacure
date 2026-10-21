from django.core.management.base import BaseCommand
from store.models import Specialization, Doctor
from decimal import Decimal


class Command(BaseCommand):
    help = 'Create sample specializations and doctors data'

    def handle(self, *args, **options):
        """Create sample specializations and doctors"""
        
        # Create Specializations
        specializations_data = [
            {'name': 'General Medicine', 'description': 'Primary healthcare and general medical conditions', 'icon': '🩺'},
            {'name': 'Cardiology', 'description': 'Heart and cardiovascular diseases', 'icon': '❤️'},
            {'name': 'Dermatology', 'description': 'Skin, hair, and nail conditions', 'icon': '🧴'},
            {'name': 'Pediatrics', 'description': 'Medical care for infants, children, and adolescents', 'icon': '👶'},
            {'name': 'Orthopedics', 'description': 'Bone, joint, and muscle disorders', 'icon': '🦴'},
            {'name': 'Neurology', 'description': 'Nervous system disorders', 'icon': '🧠'},
            {'name': 'Gynecology', 'description': 'Women\'s reproductive health', 'icon': '🌸'},
            {'name': 'ENT', 'description': 'Ear, nose, and throat conditions', 'icon': '👂'},
            {'name': 'Psychiatry', 'description': 'Mental health and behavioral disorders', 'icon': '🧘'},
            {'name': 'Ophthalmology', 'description': 'Eye care and vision problems', 'icon': '👁️'},
        ]
        
        specializations = {}
        self.stdout.write("Creating specializations...")
        for spec_data in specializations_data:
            spec, created = Specialization.objects.get_or_create(
                name=spec_data['name'],
                defaults={
                    'description': spec_data['description'],
                    'icon': spec_data['icon']
                }
            )
            specializations[spec_data['name']] = spec
            self.stdout.write(f"{'Created' if created else 'Found'}: {spec.name}")
        
        # Create Sample Doctors
        doctors_data = [
            {
                'title': 'Dr.',
                'first_name': 'Ahmed',
                'last_name': 'Ali',
                'gender': 'M',
                'license_number': 'PMC12345',
                'specializations': ['General Medicine', 'Cardiology'],
                'experience': '5-10',
                'education': 'MBBS from King Edward Medical University, Lahore\nMD in Internal Medicine',
                'phone_number': '+92-321-1234567',
                'email': 'dr.ahmed.ali@pharmacure.com',
                'clinic_address': '123 Main Street, Gulberg III, Lahore, Punjab 54000',
                'consultation_fee': Decimal('2000.00'),
                'consultation_hours': 'Mon-Fri: 9:00 AM - 5:00 PM, Sat: 9:00 AM - 1:00 PM',
                'languages_spoken': 'Urdu, English, Punjabi',
                'about': 'Dr. Ahmed Ali is an experienced physician with over 8 years of practice in general medicine and cardiology. He specializes in preventive care and chronic disease management.',
                'achievements': 'Gold Medalist in MBBS, Published researcher in cardiology journals',
                'is_available': True,
                'online_consultation': True,
                'emergency_availability': False,
                'featured': True,
            },
            {
                'title': 'Dr.',
                'first_name': 'Fatima',
                'last_name': 'Khan',
                'gender': 'F',
                'license_number': 'PMC23456',
                'specializations': ['Dermatology', 'General Medicine'],
                'experience': '10-15',
                'education': 'MBBS from Dow University\nDiploma in Dermatology',
                'phone_number': '+92-321-2345678',
                'email': 'dr.fatima.khan@pharmacure.com',
                'clinic_address': '456 University Road, Karachi, Sindh 75270',
                'consultation_fee': Decimal('2500.00'),
                'consultation_hours': 'Mon-Sat: 10:00 AM - 6:00 PM',
                'languages_spoken': 'Urdu, English, Sindhi',
                'about': 'Dr. Fatima Khan is a board-certified dermatologist with 12 years of experience treating various skin conditions. She is known for her expertise in cosmetic dermatology.',
                'achievements': 'Fellowship in Advanced Dermatology, Award for Best Dermatologist 2023',
                'is_available': True,
                'online_consultation': True,
                'emergency_availability': True,
                'featured': True,
            },
            {
                'title': 'Dr.',
                'first_name': 'Muhammad',
                'last_name': 'Hassan',
                'gender': 'M',
                'license_number': 'PMC34567',
                'specializations': ['Pediatrics'],
                'experience': '3-5',
                'education': 'MBBS from Allama Iqbal Medical College\nSpecialization in Pediatrics',
                'phone_number': '+92-321-3456789',
                'email': 'dr.hassan@pharmacure.com',
                'clinic_address': '789 Children Hospital Road, Faisalabad, Punjab 38000',
                'consultation_fee': Decimal('1800.00'),
                'consultation_hours': 'Mon-Fri: 8:00 AM - 4:00 PM, Emergency: 24/7',
                'languages_spoken': 'Urdu, English',
                'about': 'Dr. Muhammad Hassan is a dedicated pediatrician who loves working with children. He provides comprehensive healthcare for infants, children, and adolescents.',
                'achievements': 'Best Young Doctor Award 2024, Certified in Pediatric Emergency Care',
                'is_available': True,
                'online_consultation': False,
                'emergency_availability': True,
                'featured': False,
            },
            {
                'title': 'Prof.',
                'first_name': 'Sarah',
                'last_name': 'Ahmad',
                'gender': 'F',
                'license_number': 'PMC45678',
                'specializations': ['Gynecology', 'General Medicine'],
                'experience': '15+',
                'education': 'MBBS from Lahore Medical College\nMS in Gynecology and Obstetrics\nFellowship in Reproductive Medicine',
                'phone_number': '+92-321-4567890',
                'email': 'prof.sarah.ahmad@pharmacure.com',
                'clinic_address': '321 Women Hospital, Model Town, Lahore, Punjab 54700',
                'consultation_fee': Decimal('3000.00'),
                'consultation_hours': 'Mon-Thu: 9:00 AM - 3:00 PM, Fri: 9:00 AM - 1:00 PM',
                'languages_spoken': 'Urdu, English',
                'about': 'Prof. Sarah Ahmad is a renowned gynecologist with over 18 years of experience. She specializes in high-risk pregnancies and reproductive health.',
                'achievements': 'Department Head at Women\'s Hospital, Published 50+ research papers, International speaker',
                'is_available': True,
                'online_consultation': True,
                'emergency_availability': True,
                'featured': True,
            },
            {
                'title': 'Dr.',
                'first_name': 'Usman',
                'last_name': 'Sheikh',
                'gender': 'M',
                'license_number': 'PMC56789',
                'specializations': ['Orthopedics'],
                'experience': '10-15',
                'education': 'MBBS from Nishtar Medical College\nMS in Orthopedic Surgery',
                'phone_number': '+92-321-5678901',
                'email': 'dr.usman.sheikh@pharmacure.com',
                'clinic_address': '654 Hospital Road, Multan, Punjab 60000',
                'consultation_fee': Decimal('2200.00'),
                'consultation_hours': 'Mon-Sat: 2:00 PM - 8:00 PM',
                'languages_spoken': 'Urdu, English, Saraiki',
                'about': 'Dr. Usman Sheikh is an expert orthopedic surgeon specializing in joint replacement and sports injuries. He has performed over 1000 successful surgeries.',
                'achievements': 'Fellowship in Joint Replacement Surgery, Sports Medicine Certification',
                'is_available': True,
                'online_consultation': False,
                'emergency_availability': False,
                'featured': False,
            },
        ]
        
        self.stdout.write("\nCreating doctors...")
        for doctor_data in doctors_data:
            # Extract specializations
            spec_names = doctor_data.pop('specializations')
            # Remove fields that no longer exist on Doctor model
            for _k in ('consultation_fee', 'consultation_hours', 'is_available', 'online_consultation', 'emergency_availability', 'featured', 'experience'):
                doctor_data.pop(_k, None)
            
            # Create or get doctor
            doctor, created = Doctor.objects.get_or_create(
                license_number=doctor_data['license_number'],
                defaults=doctor_data
            )
            
            # Add specializations
            if created:
                for spec_name in spec_names:
                    if spec_name in specializations:
                        doctor.specializations.add(specializations[spec_name])
            
            self.stdout.write(f"{'Created' if created else 'Found'}: {doctor.title} {doctor.first_name} {doctor.last_name}")
        
        self.stdout.write(f"\n{self.style.SUCCESS('Sample data created successfully!')}")
        self.stdout.write(f"Specializations: {Specialization.objects.count()}")
        self.stdout.write(f"Doctors: {Doctor.objects.count()}")