# pharmacy_management/management/commands/populate_pharmacy_data.py

import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from user_management.models import CustomUser
from patient_management.models import Patient
from pharmacy_management.models import (
    Medication, MedicationStock, Supplier, PurchaseOrder, PurchaseOrderItem,
    Prescription, PrescriptionItem
)

class Command(BaseCommand):
    help = 'Generate sample pharmacy management data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Generating sample pharmacy management data...')

        # Create sample medications if they don't exist
        medications = [
            {'name': 'Paracetamol', 'generic_name': 'Acetaminophen', 'description': 'Pain reliever and a fever reducer', 'dosage_form': 'Tablet', 'strength': '500mg', 'manufacturer': 'Pharma Inc.', 'price': Decimal('0.50')},
            {'name': 'Ibuprofen', 'generic_name': 'Ibuprofen', 'description': 'Nonsteroidal anti-inflammatory drug', 'dosage_form': 'Tablet', 'strength': '200mg', 'manufacturer': 'Health Corp.', 'price': Decimal('0.30')},
            {'name': 'Amoxicillin', 'generic_name': 'Amoxicillin', 'description': 'Antibiotic', 'dosage_form': 'Capsule', 'strength': '250mg', 'manufacturer': 'MedLife', 'price': Decimal('1.00')},
        ]
        for med in medications:
            medication, created = Medication.objects.get_or_create(
                name=med['name'],
                defaults={
                    'generic_name': med['generic_name'],
                    'description': med['description'],
                    'dosage_form': med['dosage_form'],
                    'strength': med['strength'],
                    'manufacturer': med['manufacturer'],
                    'price': med['price'],
                    'requires_prescription': True,
                    'is_active': True
                }
            )
            if created:
                MedicationStock.objects.create(medication=medication, quantity=random.randint(50, 200), reorder_level=10)

        # Create sample suppliers if they don't exist
        suppliers = [
            {'name': 'Supplier A', 'contact_person': 'John Doe', 'email': 'john@example.com', 'phone': '1234567890', 'address': '123 Main St, City, Country'},
            {'name': 'Supplier B', 'contact_person': 'Jane Smith', 'email': 'jane@example.com', 'phone': '0987654321', 'address': '456 Elm St, City, Country'},
        ]
        for sup in suppliers:
            Supplier.objects.get_or_create(
                name=sup['name'],
                defaults={
                    'contact_person': sup['contact_person'],
                    'email': sup['email'],
                    'phone': sup['phone'],
                    'address': sup['address'],
                    'is_active': True
                }
            )

        # Fetch all medications, suppliers, patients, and staff
        medications = Medication.objects.all()
        suppliers = Supplier.objects.all()
        patients = Patient.objects.all()
        doctors = CustomUser.objects.filter(role='DOCTOR')
        pharmacists = CustomUser.objects.filter(role='PHARMACIST')

        # Generate sample purchase orders
        for _ in range(10):  # Generate 10 sample purchase orders
            supplier = random.choice(suppliers)
            created_by = random.choice(pharmacists)
            total_amount = Decimal('0.00')
            purchase_order = PurchaseOrder.objects.create(
                supplier=supplier,
                status=random.choice(['PENDING', 'ORDERED', 'RECEIVED', 'CANCELLED']),
                total_amount=total_amount,
                expected_delivery_date=timezone.now().date() + timezone.timedelta(days=random.randint(1, 30)),
                created_by=created_by
            )
            for _ in range(random.randint(1, 5)):  # Add 1 to 5 items to each purchase order
                medication = random.choice(medications)
                quantity = random.randint(10, 100)
                unit_price = medication.price
                total_amount += unit_price * quantity
                PurchaseOrderItem.objects.create(
                    purchase_order=purchase_order,
                    medication=medication,
                    quantity=quantity,
                    unit_price=unit_price
                )
            purchase_order.total_amount = total_amount
            purchase_order.save()

        # Generate sample prescriptions
        for _ in range(20):  # Generate 20 sample prescriptions
            patient = random.choice(patients)
            doctor = random.choice(doctors)
            prescription = Prescription.objects.create(
                patient=patient,
                doctor=doctor,
                status=random.choice(['PENDING', 'FILLED', 'PARTIALLY_FILLED', 'CANCELLED']),
                notes='Sample prescription notes'
            )
            for _ in range(random.randint(1, 3)):  # Add 1 to 3 items to each prescription
                medication = random.choice(medications)
                PrescriptionItem.objects.create(
                    prescription=prescription,
                    medication=medication,
                    dosage='1 tablet',
                    frequency='Twice a day',
                    duration='7 days',
                    quantity=random.randint(10, 30),
                    instructions='Take after meals'
                )

        self.stdout.write(self.style.SUCCESS('Successfully generated sample pharmacy management data'))