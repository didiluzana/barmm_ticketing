from django import forms

from .models import (
    Ticket,
    TicketCategory,
    User,
)


# =========================================================
# CREATE TICKET FORM
# =========================================================

class TicketForm(forms.ModelForm):

    class Meta:
        model = Ticket

        fields = [
            "caller_name",
            "caller_contact",
            "site_location",
            "category",
            "subject",
            "description",
            "priority",
            "assigned_to",
        ]

        widgets = {

            "caller_name": forms.TextInput(
                attrs={
                    "placeholder": "Caller name",
                }
            ),

            "caller_contact": forms.TextInput(
                attrs={
                    "placeholder": "Phone number / contact",
                }
            ),

            "site_location": forms.TextInput(
                attrs={
                    "placeholder": (
                        "Tower, site, village or location"
                    ),
                }
            ),

            "category": forms.Select(),

            "subject": forms.TextInput(
                attrs={
                    "placeholder": (
                        "Short summary of reported issue"
                    ),
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": (
                        "Describe the reported problem..."
                    ),
                }
            ),

            "priority": forms.Select(),

            "assigned_to": forms.Select(),

        }

    def __init__(
        self,
        *args,
        user=None,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        self.user = user

        # =================================================
        # ACTIVE TICKET CATEGORIES
        # =================================================

        self.fields[
            "category"
        ].queryset = (
            TicketCategory.objects
            .filter(
                is_active=True
            )
            .order_by(
                "name"
            )
        )

        # =================================================
        # ASSIGNABLE USERS
        # =================================================

        assigned_queryset = (
            User.objects
            .filter(
                is_active=True,
                role__in=[
                    User.Role.IT,
                    User.Role.TECHNICIAN,
                    User.Role.ELECTRICIAN,
                ],
            )
        )

        # Only show technical staff
        # belonging to the Call Agent's province.
        if (
            user
            and user.province_id
        ):
            assigned_queryset = (
                assigned_queryset
                .filter(
                    province=user.province
                )
            )

        self.fields[
            "assigned_to"
        ].queryset = (
            assigned_queryset
            .order_by(
                "role",
                "first_name",
                "last_name",
                "username",
            )
        )

        self.fields[
            "assigned_to"
        ].required = False

        self.fields[
            "assigned_to"
        ].empty_label = "Unassigned"


# =========================================================
# UPDATE TICKET FORM
# =========================================================

class TicketActionForm(forms.Form):

    status = forms.ChoiceField(
        choices=Ticket.Status.choices,
    )

    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        empty_label="Unassigned",
    )

    note = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder": (
                    "Add remarks or details "
                    "about this update..."
                ),
            }
        ),
    )

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        self.fields[
            "assigned_to"
        ].queryset = (
            User.objects
            .filter(
                is_active=True,
                role__in=[
                    User.Role.IT,
                    User.Role.TECHNICIAN,
                    User.Role.ELECTRICIAN,
                ],
            )
            .order_by(
                "role",
                "first_name",
                "last_name",
                "username",
            )
        )