from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Province, Ticket, TicketCategory, TicketUpdate, User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("BARM Helpdesk", {"fields": ("role", "province")}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("BARM Helpdesk", {"fields": ("role", "province")}),)
    list_display = ("username", "first_name", "last_name", "role", "province", "is_active")
    list_filter = ("role", "province", "is_active")

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("ticket_no", "subject", "province", "category", "priority", "status", "assigned_to", "created_at")
    list_filter = ("province", "category", "priority", "status")
    search_fields = ("ticket_no", "caller_name", "subject", "description", "site_location")
    readonly_fields = ("ticket_no", "created_at", "updated_at", "resolved_at", "closed_at")

admin.site.register(Province)
admin.site.register(TicketCategory)
admin.site.register(TicketUpdate)
admin.site.site_header = "BARM Digital Ticketing Administration"
