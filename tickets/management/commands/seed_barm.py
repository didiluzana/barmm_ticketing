from django.core.management.base import BaseCommand
from tickets.models import Province, TicketCategory, User

class Command(BaseCommand):
    help = "Create 7 province slots, ticket categories, agents and support users."
    def handle(self, *args, **options):
        provinces = []
        for i in range(1, 8):
            p, _ = Province.objects.get_or_create(name=f"Province {i}")
            provinces.append(p)
        categories = [
            ("No Internet", User.Role.IT),
            ("No Signal", User.Role.TECHNICIAN),
            ("Tower Down / Damage", User.Role.TECHNICIAN),
            ("No Power", User.Role.ELECTRICIAN),
            ("Slow Internet", User.Role.IT),
            ("Equipment / Router Issue", User.Role.IT),
            ("Electrical / Generator Issue", User.Role.ELECTRICIAN),
            ("Other", ""),
        ]
        for name, team in categories:
            TicketCategory.objects.get_or_create(name=name, defaults={"default_team": team})
        for i, province in enumerate(provinces, 1):
            u, created = User.objects.get_or_create(username=f"agent{i}", defaults={
                "first_name": "Province", "last_name": f"{i} Agent", "role": User.Role.AGENT, "province": province, "is_staff": False
            })
            if created: u.set_password("ChangeMe123!"); u.save()
        staff = [("it1", User.Role.IT), ("tech1", User.Role.TECHNICIAN), ("electrician1", User.Role.ELECTRICIAN)]
        for username, role in staff:
            u, created = User.objects.get_or_create(username=username, defaults={"role": role})
            if created: u.set_password("ChangeMe123!"); u.save()
        admin, created = User.objects.get_or_create(username="admin", defaults={"role": User.Role.ADMIN, "is_staff": True, "is_superuser": True})
        if created: admin.set_password("ChangeMe123!"); admin.save()
        self.stdout.write(self.style.SUCCESS("Seed complete. Demo password: ChangeMe123! (change immediately)."))
