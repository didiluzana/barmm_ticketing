from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


# =========================================================
# PROVINCE
# =========================================================

class Province(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


# =========================================================
# USER
# =========================================================

class User(AbstractUser):

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Administrator"
        AGENT = "AGENT", "Call Center Agent"
        IT = "IT", "IT"
        TECHNICIAN = "TECHNICIAN", "Technician"
        ELECTRICIAN = "ELECTRICIAN", "Electrician"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.AGENT,
    )

    province = models.ForeignKey(
        Province,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="users",
    )

    def __str__(self):

        full_name = self.get_full_name().strip()

        if full_name:
            return full_name

        return self.username


# =========================================================
# TICKET CATEGORY
# =========================================================

class TicketCategory(models.Model):

    name = models.CharField(
        max_length=100,
        unique=True,
    )

    default_team = models.CharField(
        max_length=20,
        choices=[
            (
                User.Role.IT,
                "IT",
            ),
            (
                User.Role.TECHNICIAN,
                "Technician",
            ),
            (
                User.Role.ELECTRICIAN,
                "Electrician",
            ),
        ],
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        verbose_name_plural = "Ticket categories"

    def __str__(self):
        return self.name


# =========================================================
# TICKET
# =========================================================

class Ticket(models.Model):

    class Status(models.TextChoices):
        NEW = "NEW", "New"
        ASSIGNED = "ASSIGNED", "Assigned"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        PENDING = "PENDING", "Pending / Waiting"
        RESOLVED = "RESOLVED", "Resolved"
        CLOSED = "CLOSED", "Closed"
        REOPENED = "REOPENED", "Reopened"

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        CRITICAL = "CRITICAL", "Critical"

    ticket_no = models.CharField(
        max_length=30,
        unique=True,
        blank=True,
    )

    province = models.ForeignKey(
        Province,
        on_delete=models.PROTECT,
        related_name="tickets",
    )

    caller_name = models.CharField(
        max_length=150,
    )

    caller_contact = models.CharField(
        max_length=100,
        blank=True,
    )

    site_location = models.CharField(
        max_length=255,
    )

    category = models.ForeignKey(
        TicketCategory,
        on_delete=models.PROTECT,
    )

    subject = models.CharField(
        max_length=200,
    )

    description = models.TextField()

    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
    )

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_tickets",
    )

    logged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="logged_tickets",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    closed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):

        # Automatically mark ticket as assigned
        # when an assignee is selected.
        if (
            self.assigned_to
            and self.status == self.Status.NEW
        ):
            self.status = self.Status.ASSIGNED

        # Record resolved time.
        if (
            self.status == self.Status.RESOLVED
            and not self.resolved_at
        ):
            self.resolved_at = timezone.now()

        # Record closed time.
        if (
            self.status == self.Status.CLOSED
            and not self.closed_at
        ):
            self.closed_at = timezone.now()

        super().save(*args, **kwargs)

        # Generate ticket number after the first save,
        # so the database primary key is available.
        if not self.ticket_no:

            self.ticket_no = (
                f"BARM-{self.created_at:%Y}-{self.pk:06d}"
            )

            type(self).objects.filter(
                pk=self.pk
            ).update(
                ticket_no=self.ticket_no
            )

    def __str__(self):

        if self.ticket_no:
            return self.ticket_no

        return f"Ticket {self.pk}"


# =========================================================
# TICKET UPDATE / ACTIVITY HISTORY
# =========================================================

class TicketUpdate(models.Model):

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name="updates",
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
    )

    note = models.TextField()

    old_status = models.CharField(
        max_length=20,
        blank=True,
    )

    new_status = models.CharField(
        max_length=20,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):

        return (
            f"{self.ticket.ticket_no} - "
            f"{self.author}"
        )


# =========================================================
# TICKET STATUS / ASSIGNMENT HISTORY
# =========================================================

class TicketStatusHistory(models.Model):

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name="status_history",
    )

    old_status = models.CharField(
        max_length=30,
        blank=True,
        null=True,
    )

    new_status = models.CharField(
        max_length=30,
    )

    # Person assigned to the ticket
    # at the time of this history entry.
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ticket_status_assignments",
    )

    # User who performed the change.
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ticket_status_changes",
    )

    remarks = models.TextField(
        blank=True,
    )

    changed_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["changed_at"]
        verbose_name_plural = "Ticket status histories"

    def __str__(self):

        return (
            f"{self.ticket.ticket_no}: "
            f"{self.old_status} → {self.new_status}"
        )