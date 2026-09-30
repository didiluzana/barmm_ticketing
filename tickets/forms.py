from django import forms

from .models import (
    Ticket,
    TicketCategory,
    User,
)


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
        **kwargs
    ):

        super().__init__(
            *args,
            **kwargs
        )

        self.user = user


        # =================================================
        # ACTIVE CATEGORIES ONLY
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
        # ASSIGNED TO
        #
        # Only:
        # - IT
        # - Technician
        # - Electrician
        #
        # from the SAME PROVINCE
        # as the logged-in Call Center Agent.
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


        # =================================================
        # SAME PROVINCE FILTER
        # =================================================

        if (
            user
            and
            user.province_id
        ):

            assigned_queryset = (
                assigned_queryset
                .filter(
                    province_id=
                    user.province_id
                )
            )

        else:

            # If the logged-in user has no province,
            # do not display technical personnel.
            assigned_queryset = (
                assigned_queryset.none()
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
        ].empty_label = (
            "Unassigned"
        )


    # =====================================================
    # VALIDATE ASSIGNED PERSON
    # =====================================================

    def clean_assigned_to(self):

        assigned_to = (
            self.cleaned_data.get(
                "assigned_to"
            )
        )


        # Unassigned is allowed.

        if not assigned_to:

            return None


        # =================================================
        # USER MUST HAVE A PROVINCE
        # =================================================

        if (
            not self.user
            or
            not self.user.province_id
        ):

            raise forms.ValidationError(
                "Your account is not assigned "
                "to a province."
            )


        # =================================================
        # SAME PROVINCE CHECK
        # =================================================

        if (
            assigned_to.province_id
            !=
            self.user.province_id
        ):

            raise forms.ValidationError(
                "You can only assign this ticket "
                "to IT, Technician, or Electrician "
                "personnel from your province."
            )


        # =================================================
        # ROLE CHECK
        # =================================================

        allowed_roles = [
            User.Role.IT,
            User.Role.TECHNICIAN,
            User.Role.ELECTRICIAN,
        ]


        if (
            assigned_to.role
            not in allowed_roles
        ):

            raise forms.ValidationError(
                "Tickets can only be assigned "
                "to IT, Technician, or Electrician "
                "personnel."
            )


        return assigned_to



# =========================================================
# TICKET UPDATE / REASSIGNMENT FORM
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
        province=None,
        **kwargs
    ):

        super().__init__(
            *args,
            **kwargs
        )

        self.province = province


        # =================================================
        # ASSIGNED TO
        #
        # Restrict reassignment to personnel
        # from the ticket's province.
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


        if province:

            assigned_queryset = (
                assigned_queryset
                .filter(
                    province=province
                )
            )

        else:

            assigned_queryset = (
                assigned_queryset.none()
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


    def clean_assigned_to(self):

        assigned_to = (
            self.cleaned_data.get(
                "assigned_to"
            )
        )


        if not assigned_to:

            return None


        if not self.province:

            raise forms.ValidationError(
                "This ticket does not have "
                "a valid province."
            )


        if (
            assigned_to.province_id
            !=
            self.province.id
        ):

            raise forms.ValidationError(
                "This ticket can only be assigned "
                "to personnel from the same province."
            )


        allowed_roles = [
            User.Role.IT,
            User.Role.TECHNICIAN,
            User.Role.ELECTRICIAN,
        ]


        if (
            assigned_to.role
            not in allowed_roles
        ):

            raise forms.ValidationError(
                "Tickets can only be assigned "
                "to IT, Technician, or Electrician "
                "personnel."
            )


        return assigned_to