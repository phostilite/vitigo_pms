# pharmacy_management/management/commands/populate_pharmacy_data.py

import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker
from user_management.models import CustomUser
from pharmacy_management.models import (
    Medication, MedicationStock, Supplier, PurchaseOrder, PurchaseOrderItem
)
from access_control.models import Role

class Command(BaseCommand):
    help = 'Generate sample pharmacy management data'

    def add_arguments(self, parser):
        parser.add_argument('--medications', type=int, default=50, help='Number of medications to create')
        parser.add_argument('--suppliers', type=int, default=20, help='Number of suppliers to create')
        parser.add_argument('--purchases', type=int, default=50, help='Number of purchase orders to create')

    def handle(self, *args, **kwargs):
        fake = Faker()
        self.stdout.write('Generating sample pharmacy management data...')

        # Get roles
        pharmacist_role = Role.objects.get(name='PHARMACIST')

        # Create medications
        medication_forms = ['Tablet', 'Capsule', 'Syrup', 'Injection', 'Cream', 'Ointment', 'Drops']
        manufacturers = [fake.company() for _ in range(10)]
        
        for _ in range(kwargs['medications']):
            strength_units = ['mg', 'g', 'ml', 'mcg', '%']
            med = Medication.objects.create(
                name=fake.unique.word() + ' ' + fake.word(),
                generic_name=fake.word(),
                description=fake.text(max_nb_chars=200),
                dosage_form=random.choice(medication_forms),
                strength=f"{random.randint(1, 1000)}{random.choice(strength_units)}",
                manufacturer=random.choice(manufacturers),
                price=Decimal(str(random.uniform(0.1, 1000.0))).quantize(Decimal('0.01')),
                requires_prescription=random.choice([True, False]),
                is_active=True
            )
            MedicationStock.objects.create(
                medication=med,
                quantity=random.randint(0, 1000),
                reorder_level=random.randint(10, 100)
            )

        # Create suppliers
        for _ in range(kwargs['suppliers']):
            Supplier.objects.create(
                name=fake.company(),
                contact_person=fake.name(),
                email=fake.company_email(),
                phone=fake.phone_number(),
                address=fake.address(),
                is_active=True
            )

        # Fetch required data
        medications = list(Medication.objects.all())
        suppliers = list(Supplier.objects.all())
        pharmacists = list(CustomUser.objects.filter(role=pharmacist_role))

        if not all([medications, suppliers, pharmacists]):
            self.stdout.write(self.style.ERROR('Missing required data. Ensure you have medications, suppliers, and pharmacists.'))
            return

        # Generate purchase orders
        for _ in range(kwargs['purchases']):
            po_items = []
            supplier = random.choice(suppliers)
            created_by = random.choice(pharmacists)
            total_amount = Decimal('0.00')
            
            purchase_order = PurchaseOrder.objects.create(
                supplier=supplier,
                status=random.choice(['PENDING', 'ORDERED', 'RECEIVED', 'CANCELLED']),
                total_amount=total_amount,
                expected_delivery_date=fake.date_between(start_date='today', end_date='+30d'),
                created_by=created_by
            )

            for _ in range(random.randint(1, 10)):
                medication = random.choice(medications)
                quantity = random.randint(10, 500)
                unit_price = medication.price
                total_amount += unit_price * quantity
                po_items.append(PurchaseOrderItem(
                    purchase_order=purchase_order,
                    medication=medication,
                    quantity=quantity,
                    unit_price=unit_price
                ))

            PurchaseOrderItem.objects.bulk_create(po_items)
            purchase_order.total_amount = total_amount
            purchase_order.save()

        self.stdout.write(self.style.SUCCESS('Successfully generated sample pharmacy management data'))