from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import random

from accounts.models import Profile, Skill
from projects.models import Category, Project
from bids.models import Bid
from payments.models import Wallet, PaymentMethod, Transaction

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate the database with sample data for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create categories
        categories = self.create_categories()
        
        # Create skills
        skills = self.create_skills()
        
        # Create users
        freelancers = self.create_freelancers()
        employers = self.create_employers()
        
        # Create projects
        projects = self.create_projects(employers, categories)
        
        # Create bids
        self.create_bids(freelancers, projects)
        
        # Create payment methods and wallets
        self.create_payment_data(freelancers + employers)
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created sample data!')
        )

    def create_categories(self):
        categories_data = [
            {'name': 'Web Development', 'description': 'Website and web application development', 'icon': 'fas fa-code'},
            {'name': 'Mobile Development', 'description': 'Mobile app development for iOS and Android', 'icon': 'fas fa-mobile-alt'},
            {'name': 'Graphic Design', 'description': 'Logo design, branding, and visual identity', 'icon': 'fas fa-paint-brush'},
            {'name': 'Writing & Translation', 'description': 'Content writing, copywriting, and translation', 'icon': 'fas fa-pen'},
            {'name': 'Digital Marketing', 'description': 'SEO, social media marketing, and advertising', 'icon': 'fas fa-bullhorn'},
            {'name': 'Video & Animation', 'description': 'Video production, animation, and motion graphics', 'icon': 'fas fa-video'},
            {'name': 'Data Science', 'description': 'Data analysis, machine learning, and AI', 'icon': 'fas fa-chart-line'},
            {'name': 'Business', 'description': 'Business consulting, strategy, and operations', 'icon': 'fas fa-briefcase'},
        ]
        
        categories = []
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            categories.append(category)
            if created:
                self.stdout.write(f'Created category: {category.name}')
        
        return categories

    def create_skills(self):
        skills_data = [
            'Python', 'JavaScript', 'React', 'Vue.js', 'Angular', 'Node.js', 'Django', 'Flask',
            'PHP', 'Laravel', 'WordPress', 'Drupal', 'HTML', 'CSS', 'Bootstrap', 'Tailwind CSS',
            'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Docker', 'AWS', 'Azure', 'Google Cloud',
            'iOS', 'Android', 'React Native', 'Flutter', 'Swift', 'Kotlin', 'Java',
            'Photoshop', 'Illustrator', 'Figma', 'Sketch', 'InDesign', 'After Effects',
            'Content Writing', 'Copywriting', 'Technical Writing', 'Blog Writing', 'SEO Writing',
            'Social Media Marketing', 'Google Ads', 'Facebook Ads', 'Email Marketing', 'Analytics',
            'Video Editing', 'Motion Graphics', '3D Animation', 'Premiere Pro', 'Final Cut Pro',
            'Machine Learning', 'Data Analysis', 'Python', 'R', 'SQL', 'Tableau', 'Power BI',
            'Business Strategy', 'Project Management', 'Agile', 'Scrum', 'Consulting'
        ]
        
        skills = []
        for skill_name in skills_data:
            skill, created = Skill.objects.get_or_create(
                name=skill_name,
                defaults={'category': random.choice(['Development', 'Design', 'Marketing', 'Business', 'Data'])}
            )
            skills.append(skill)
        
        return skills

    def create_freelancers(self):
        freelancers_data = [
            {
                'first_name': 'John', 'last_name': 'Smith', 'email': 'john.smith@email.com',
                'username': 'johnsmith', 'bio': 'Full-stack developer with 5+ years of experience in web development.',
                'skills': 'Python, Django, React, JavaScript, PostgreSQL',
                'hourly_rate': 75, 'experience_years': 5, 'location': 'New York, NY'
            },
            {
                'first_name': 'Sarah', 'last_name': 'Johnson', 'email': 'sarah.johnson@email.com',
                'username': 'sarahjohnson', 'bio': 'Creative graphic designer specializing in branding and UI/UX design.',
                'skills': 'Photoshop, Illustrator, Figma, UI/UX Design, Branding',
                'hourly_rate': 60, 'experience_years': 3, 'location': 'Los Angeles, CA'
            },
            {
                'first_name': 'Mike', 'last_name': 'Chen', 'email': 'mike.chen@email.com',
                'username': 'mikechen', 'bio': 'Mobile app developer with expertise in React Native and Flutter.',
                'skills': 'React Native, Flutter, JavaScript, iOS, Android',
                'hourly_rate': 80, 'experience_years': 4, 'location': 'San Francisco, CA'
            },
            {
                'first_name': 'Emily', 'last_name': 'Davis', 'email': 'emily.davis@email.com',
                'username': 'emilydavis', 'bio': 'Content writer and digital marketing specialist.',
                'skills': 'Content Writing, SEO, Social Media Marketing, Copywriting',
                'hourly_rate': 45, 'experience_years': 2, 'location': 'Chicago, IL'
            },
            {
                'first_name': 'David', 'last_name': 'Wilson', 'email': 'david.wilson@email.com',
                'username': 'davidwilson', 'bio': 'Data scientist and machine learning engineer.',
                'skills': 'Python, Machine Learning, Data Analysis, SQL, TensorFlow',
                'hourly_rate': 90, 'experience_years': 6, 'location': 'Austin, TX'
            }
        ]
        
        freelancers = []
        for data in freelancers_data:
            user, created = User.objects.get_or_create(
                email=data['email'],
                defaults={
                    'username': data['username'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'role': 'freelancer'
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                
                # Create profile
                profile, _ = Profile.objects.get_or_create(
                    user=user,
                    defaults={
                        'bio': data['bio'],
                        'skills': data['skills'],
                        'hourly_rate': data['hourly_rate'],
                        'experience_years': data['experience_years'],
                        'location': data['location']
                    }
                )
                
                # Create wallet
                Wallet.objects.get_or_create(user=user)
                
                freelancers.append(user)
                self.stdout.write(f'Created freelancer: {user.full_name}')
        
        return freelancers

    def create_employers(self):
        employers_data = [
            {
                'first_name': 'Alice', 'last_name': 'Brown', 'email': 'alice.brown@company.com',
                'username': 'alicebrown', 'company_name': 'TechStart Inc.', 'company_size': '11-50',
                'location': 'Seattle, WA'
            },
            {
                'first_name': 'Robert', 'last_name': 'Taylor', 'email': 'robert.taylor@company.com',
                'username': 'roberttaylor', 'company_name': 'Design Studio', 'company_size': '1-10',
                'location': 'Miami, FL'
            },
            {
                'first_name': 'Lisa', 'last_name': 'Anderson', 'email': 'lisa.anderson@company.com',
                'username': 'lisaanderson', 'company_name': 'Marketing Pro', 'company_size': '51-200',
                'location': 'Denver, CO'
            }
        ]
        
        employers = []
        for data in employers_data:
            user, created = User.objects.get_or_create(
                email=data['email'],
                defaults={
                    'username': data['username'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'role': 'employer'
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                
                # Create profile
                profile, _ = Profile.objects.get_or_create(
                    user=user,
                    defaults={
                        'company_name': data['company_name'],
                        'company_size': data['company_size'],
                        'location': data['location']
                    }
                )
                
                # Create wallet
                Wallet.objects.get_or_create(user=user)
                
                employers.append(user)
                self.stdout.write(f'Created employer: {user.full_name}')
        
        return employers

    def create_projects(self, employers, categories):
        projects_data = [
            {
                'title': 'E-commerce Website Development',
                'description': 'Need a modern e-commerce website with payment integration, user authentication, and admin panel. Should be responsive and SEO-friendly.',
                'category': 'Web Development',
                'budget_min': 2000, 'budget_max': 5000, 'budget_type': 'fixed',
                'skills_required': 'Python, Django, React, PostgreSQL, Stripe',
                'experience_level': 'intermediate'
            },
            {
                'title': 'Mobile App for Food Delivery',
                'description': 'Looking for a mobile app developer to create a food delivery app for both iOS and Android. Features include user registration, restaurant listings, order tracking, and payment processing.',
                'category': 'Mobile Development',
                'budget_min': 5000, 'budget_max': 10000, 'budget_type': 'fixed',
                'skills_required': 'React Native, JavaScript, Firebase, Payment Integration',
                'experience_level': 'expert'
            },
            {
                'title': 'Logo Design and Brand Identity',
                'description': 'Need a professional logo design and complete brand identity package for a new tech startup. Includes logo, business cards, letterhead, and brand guidelines.',
                'category': 'Graphic Design',
                'budget_min': 500, 'budget_max': 1500, 'budget_type': 'fixed',
                'skills_required': 'Logo Design, Branding, Illustrator, Photoshop',
                'experience_level': 'intermediate'
            },
            {
                'title': 'Content Writing for Tech Blog',
                'description': 'Looking for a skilled content writer to create engaging articles about technology trends, programming tutorials, and industry insights. 20 articles per month.',
                'category': 'Writing & Translation',
                'budget_min': 800, 'budget_max': 1200, 'budget_type': 'fixed',
                'skills_required': 'Content Writing, SEO, Technical Writing, WordPress',
                'experience_level': 'intermediate'
            },
            {
                'title': 'Social Media Marketing Campaign',
                'description': 'Need a digital marketing expert to manage our social media presence across Facebook, Instagram, and LinkedIn. Create content calendar and run paid advertising campaigns.',
                'category': 'Digital Marketing',
                'budget_min': 1000, 'budget_max': 2000, 'budget_type': 'monthly',
                'skills_required': 'Social Media Marketing, Facebook Ads, Content Creation, Analytics',
                'experience_level': 'intermediate'
            }
        ]
        
        projects = []
        for data in projects_data:
            category = Category.objects.get(name=data['category'])
            employer = random.choice(employers)
            deadline = timezone.now() + timedelta(days=random.randint(7, 30))
            
            project, created = Project.objects.get_or_create(
                title=data['title'],
                employer=employer,
                defaults={
                    'description': data['description'],
                    'category': category,
                    'budget_min': data['budget_min'],
                    'budget_max': data['budget_max'],
                    'budget_type': data['budget_type'],
                    'deadline': deadline,
                    'skills_required': data['skills_required'],
                    'experience_level': data['experience_level'],
                    'is_featured': random.choice([True, False])
                }
            )
            if created:
                projects.append(project)
                self.stdout.write(f'Created project: {project.title}')
        
        return projects

    def create_bids(self, freelancers, projects):
        for project in projects:
            # Create 2-4 bids per project
            num_bids = random.randint(2, 4)
            selected_freelancers = random.sample(freelancers, min(num_bids, len(freelancers)))
            
            for freelancer in selected_freelancers:
                bid_amount = random.randint(project.budget_min, project.budget_max)
                delivery_time = random.randint(3, 14)
                
                bid, created = Bid.objects.get_or_create(
                    project=project,
                    freelancer=freelancer,
                    defaults={
                        'amount': bid_amount,
                        'delivery_time': delivery_time,
                        'proposal': f'I am excited to work on this project. With my experience in {freelancer.profile.skills.split(",")[0]}, I can deliver high-quality results within the specified timeline. I have {freelancer.profile.experience_years} years of experience and have completed similar projects successfully.',
                        'status': random.choice(['pending', 'accepted', 'rejected'])
                    }
                )
                if created:
                    self.stdout.write(f'Created bid: {freelancer.full_name} -> {project.title}')

    def create_payment_data(self, users):
        for user in users:
            # Create sample payment methods
            payment_types = ['credit_card', 'debit_card', 'paypal', 'bank_transfer']
            for i, payment_type in enumerate(payment_types[:2]):  # Create 2 payment methods per user
                PaymentMethod.objects.get_or_create(
                    user=user,
                    payment_type=payment_type,
                    defaults={
                        'card_brand': 'Visa' if 'card' in payment_type else '',
                        'card_last_four': str(random.randint(1000, 9999)),
                        'expiry_month': random.randint(1, 12),
                        'expiry_year': random.randint(2024, 2028),
                        'is_default': i == 0
                    }
                )
            
            # Add some funds to wallets
            wallet = Wallet.objects.get(user=user)
            if wallet.balance == 0:
                wallet.add_funds(random.randint(100, 1000))
                
                # Create transaction record
                Transaction.objects.create(
                    user=user,
                    transaction_type='deposit',
                    amount=wallet.balance,
                    status='completed',
                    description='Initial deposit',
                    completed_at=timezone.now()
                )
        
        self.stdout.write('Created payment data for all users')
