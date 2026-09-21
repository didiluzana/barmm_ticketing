from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from .forms import (
    TicketActionForm,
    TicketForm,
)

from .models import (
    Ticket,
    TicketStatusHistory,
    TicketUpdate,
    User,
)


# =========================================================
# TICKET VISIBILITY
# =========================================================

def visible_tickets(user):

    qs = Ticket.objects.select_related(
        "province",
        "category",
        "assigned_to",
        "logged_by",
    )

    # Admin / Superuser can see everything.
    if (
        user.is_superuser
        or user.role == User.Role.ADMIN
    ):
        return qs

    # Non-admin users require a province.
    if not user.province_id:
        return qs.none()

    # Call agents can see tickets
    # in their province.
    if user.role == User.Role.AGENT:

        return qs.filter(
            province=user.province
        )

    # IT / Technician / Electrician
    # can see all tickets in their province.
    if user.role in [
        User.Role.IT,
        User.Role.TECHNICIAN,
        User.Role.ELECTRICIAN,
    ]:

        return qs.filter(
            province=user.province
        )

    return qs.none()


# =========================================================
# DASHBOARD
@login_required
def dashboard(request):
    qs = visible_tickets(request.user)

    # =====================================================
    # UNRESOLVED STATUSES
    # =====================================================

    unresolved_statuses = [
        Ticket.Status.NEW,
        Ticket.Status.ASSIGNED,
        Ticket.Status.IN_PROGRESS,
        Ticket.Status.PENDING,
        Ticket.Status.REOPENED,
    ]

    # =====================================================
    # DASHBOARD COUNTS
    # These counts are based on all tickets visible
    # to the logged-in user.
    # =====================================================

    total = qs.count()

    new_count = qs.filter(
        status=Ticket.Status.NEW
    ).count()

    active_count = qs.filter(
        status__in=unresolved_statuses
    ).count()

    resolved_count = qs.filter(
        status__in=[
            Ticket.Status.RESOLVED,
            Ticket.Status.CLOSED,
        ]
    ).count()

    critical_count = (
        qs.filter(
            priority=Ticket.Priority.CRITICAL
        )
        .exclude(
            status=Ticket.Status.CLOSED
        )
        .count()
    )

    closed_count = qs.filter(
        status=Ticket.Status.CLOSED
    ).count()

    # =====================================================
    # FILTER
    # all
    # unresolved
    # closed
    # =====================================================

    ticket_filter = request.GET.get(
        "filter",
        "unresolved",
    )

    if ticket_filter == "all":

        displayed_tickets = qs

    elif ticket_filter == "closed":

        displayed_tickets = qs.filter(
            status=Ticket.Status.CLOSED
        )

    else:

        # Default dashboard view:
        # unresolved tickets only.
        ticket_filter = "unresolved"

        displayed_tickets = qs.filter(
            status__in=unresolved_statuses
        )

    # =====================================================
    # SEARCH
    # Partial search is supported.
    # =====================================================

    search_query = request.GET.get(
        "q",
        "",
    ).strip()

    if search_query:

        displayed_tickets = displayed_tickets.filter(

            Q(
                ticket_no__icontains=search_query
            )

            |

            Q(
                site_location__icontains=search_query
            )

            |

            Q(
                subject__icontains=search_query
            )

            |

            Q(
                description__icontains=search_query
            )

            |

            Q(
                caller_name__icontains=search_query
            )

            |

            Q(
                caller_contact__icontains=search_query
            )

            |

            Q(
                category__name__icontains=search_query
            )

            |

            Q(
                province__name__icontains=search_query
            )

        )

    # =====================================================
    # SORT BY DATE
    # OLDEST FIRST
    # =====================================================

    displayed_tickets = displayed_tickets.order_by(
        "created_at"
    )

    # =====================================================
    # CONTEXT
    # =====================================================

    context = {

        "total":
            total,

        "new_count":
            new_count,

        "active_count":
            active_count,

        "resolved_count":
            resolved_count,

        "critical_count":
            critical_count,

        "closed_count":
            closed_count,

        "displayed_tickets":
            displayed_tickets,

        "ticket_filter":
            ticket_filter,

        "search_query":
            search_query,

        "unresolved_statuses":
            unresolved_statuses,
    }

    return render(
        request,
        "tickets/dashboard.html",
        context,
    )


# =========================================================
# TICKET LIST
# =========================================================

@login_required
def ticket_list(request):

    qs = visible_tickets(
        request.user
    )

    status = request.GET.get(
        "status",
        "",
    )

    priority = request.GET.get(
        "priority",
        "",
    )

    q = request.GET.get(
        "q",
        "",
    ).strip()

    if status:

        qs = qs.filter(
            status=status
        )

    if priority:

        qs = qs.filter(
            priority=priority
        )

    if q:

        qs = qs.filter(

            Q(
                ticket_no__icontains=q
            )

            | Q(
                caller_name__icontains=q
            )

            | Q(
                caller_contact__icontains=q
            )

            | Q(
                subject__icontains=q
            )

            | Q(
                site_location__icontains=q
            )

            | Q(
                description__icontains=q
            )

        )

    qs = qs.order_by(
        "-created_at"
    )

    context = {

        "tickets":
            qs,

        "statuses":
            Ticket.Status.choices,

        "priorities":
            Ticket.Priority.choices,

        "search_query":
            q,

        "selected_status":
            status,

        "selected_priority":
            priority,

    }

    return render(
        request,
        "tickets/ticket_list.html",
        context,
    )


# =========================================================
# CREATE / LOG TICKET
# =========================================================

@login_required
def ticket_create(request):

    # Only Call Center Agents
    # can log new calls.
    if (
        request.user.role
        != User.Role.AGENT
    ):

        messages.error(
            request,
            (
                "Access denied. Only Call Center "
                "Agents can log calls."
            ),
        )

        return redirect(
            "dashboard"
        )

    # Agent must belong to a province.
    if not request.user.province_id:

        messages.error(
            request,
            (
                "Your account is not assigned "
                "to a province. Please contact "
                "the administrator."
            ),
        )

        return redirect(
            "dashboard"
        )

    if request.method == "POST":

        form = TicketForm(
            request.POST,
            user=request.user,
        )

        if form.is_valid():

            ticket = form.save(
                commit=False
            )

            # Automatically record
            # the Call Center Agent.
            ticket.logged_by = (
                request.user
            )

            # Province is always forced
            # to the Call Agent's province.
            ticket.province = (
                request.user.province
            )

            ticket.save()


            # =============================================
            # INITIAL STATUS HISTORY
            # =============================================

            TicketStatusHistory.objects.create(

                ticket=ticket,

                old_status="",

                new_status=(
                    ticket.status
                ),

                assigned_to=(
                    ticket.assigned_to
                ),

                changed_by=(
                    request.user
                ),

                remarks=(
                    "Call logged and ticket created."
                ),

            )


            # =============================================
            # INITIAL ACTIVITY HISTORY
            # =============================================

            activity_text = (
                "Call logged and ticket created."
            )

            if ticket.assigned_to:

                activity_text += (
                    " Assigned to "
                    f"{get_user_display_name(ticket.assigned_to)}."
                )


            TicketUpdate.objects.create(

                ticket=ticket,

                author=request.user,

                note=activity_text,

                old_status="",

                new_status=(
                    ticket.status
                ),

            )


            messages.success(
                request,
                (
                    f"Ticket {ticket.ticket_no} "
                    "created successfully."
                ),
            )


            return redirect(
                "ticket_detail",
                pk=ticket.pk,
            )

    else:

        form = TicketForm(
            user=request.user
        )


    return render(
        request,
        "tickets/ticket_form.html",
        {
            "form": form,
        },
    )


# =========================================================
# TICKET DETAIL / UPDATE
# =========================================================

@login_required
def ticket_detail(
    request,
    pk,
):

    ticket = get_object_or_404(
        visible_tickets(
            request.user
        ),
        pk=pk,
    )


    if request.method == "POST":

        form = TicketActionForm(
            request.POST
        )


        if form.is_valid():

            # =============================================
            # OLD VALUES
            # =============================================

            old_status = (
                ticket.status
            )

            old_assigned_to = (
                ticket.assigned_to
            )


            # =============================================
            # NEW VALUES
            # =============================================

            new_status = (
                form.cleaned_data[
                    "status"
                ]
            )

            new_assigned_to = (
                form.cleaned_data[
                    "assigned_to"
                ]
            )

            note = (
                form.cleaned_data.get(
                    "note",
                    "",
                )
                or ""
            ).strip()


            # =============================================
            # DETECT CHANGES
            # =============================================

            status_changed = (
                old_status
                != new_status
            )

            assignment_changed = (
                old_assigned_to
                != new_assigned_to
            )


            # =============================================
            # SAVE TICKET
            # =============================================

            ticket.status = (
                new_status
            )

            ticket.assigned_to = (
                new_assigned_to
            )

            ticket.save()


            # =============================================
            # STATUS / ASSIGNMENT HISTORY
            # =============================================

            if (
                status_changed
                or assignment_changed
            ):

                if (
                    status_changed
                    and assignment_changed
                ):

                    history_remark = (
                        note
                        or (
                            "Ticket status and "
                            "assignment changed."
                        )
                    )

                elif status_changed:

                    history_remark = (
                        note
                        or "Ticket status changed."
                    )

                else:

                    history_remark = (
                        note
                        or "Ticket assignment changed."
                    )


                TicketStatusHistory.objects.create(

                    ticket=ticket,

                    old_status=(
                        old_status
                    ),

                    new_status=(
                        new_status
                    ),

                    # Save new assignment
                    # into the history row.
                    assigned_to=(
                        new_assigned_to
                    ),

                    changed_by=(
                        request.user
                    ),

                    remarks=(
                        history_remark
                    ),

                )


            # =============================================
            # ACTIVITY HISTORY
            # =============================================

            activity_notes = []


            if status_changed:

                activity_notes.append(
                    (
                        "Status changed from "
                        f"{get_status_label(old_status)} "
                        "to "
                        f"{get_status_label(new_status)}."
                    )
                )


            if assignment_changed:

                old_name = (
                    get_user_display_name(
                        old_assigned_to
                    )
                    if old_assigned_to
                    else "Unassigned"
                )

                new_name = (
                    get_user_display_name(
                        new_assigned_to
                    )
                    if new_assigned_to
                    else "Unassigned"
                )

                activity_notes.append(
                    (
                        "Assignment changed from "
                        f"{old_name} to "
                        f"{new_name}."
                    )
                )


            if note:

                activity_notes.append(
                    note
                )


            if not activity_notes:

                activity_notes.append(
                    "Ticket updated."
                )


            TicketUpdate.objects.create(

                ticket=ticket,

                author=request.user,

                note=" ".join(
                    activity_notes
                ),

                old_status=(
                    old_status
                ),

                new_status=(
                    new_status
                ),

            )


            # =============================================
            # SUCCESS MESSAGES
            # =============================================

            if (
                new_status
                == Ticket.Status.CLOSED
            ):

                messages.success(
                    request,
                    (
                        f"Ticket {ticket.ticket_no} "
                        "has been closed."
                    ),
                )


            elif (
                new_status
                == Ticket.Status.RESOLVED
            ):

                messages.success(
                    request,
                    (
                        f"Ticket {ticket.ticket_no} "
                        "has been resolved."
                    ),
                )


            elif (
                status_changed
                and assignment_changed
            ):

                messages.success(
                    request,
                    (
                        f"Ticket {ticket.ticket_no} "
                        "status and assignment were "
                        "updated successfully."
                    ),
                )


            elif assignment_changed:

                if new_assigned_to:

                    messages.success(
                        request,
                        (
                            f"Ticket {ticket.ticket_no} "
                            "was assigned to "
                            f"{get_user_display_name(new_assigned_to)}."
                        ),
                    )

                else:

                    messages.success(
                        request,
                        (
                            f"Ticket {ticket.ticket_no} "
                            "is now unassigned."
                        ),
                    )


            elif status_changed:

                messages.success(
                    request,
                    (
                        f"Ticket {ticket.ticket_no} "
                        "status updated to "
                        f"{get_status_label(new_status)}."
                    ),
                )


            else:

                messages.success(
                    request,
                    "Ticket updated successfully.",
                )


            # =============================================
            # ACCESS CHECK AFTER UPDATE
            # =============================================

            if visible_tickets(
                request.user
            ).filter(
                pk=ticket.pk
            ).exists():

                return redirect(
                    "ticket_detail",
                    pk=ticket.pk,
                )


            return redirect(
                "ticket_list"
            )


    else:

        form = TicketActionForm(

            initial={

                "status":
                    ticket.status,

                "assigned_to":
                    ticket.assigned_to,

            }

        )


    # =====================================================
    # STATUS HISTORY
    # =====================================================

    status_history = (

        ticket.status_history

        .select_related(
            "changed_by",
            "assigned_to",
        )

        .order_by(
            "changed_at"
        )

    )


    # =====================================================
    # ACTIVITY HISTORY
    # =====================================================

    activity_history = (

        ticket.updates

        .select_related(
            "author"
        )

        .order_by(
            "-created_at"
        )

    )


    context = {

        "ticket":
            ticket,

        "form":
            form,

        "status_history":
            status_history,

        "activity_history":
            activity_history,

    }


    return render(
        request,
        "tickets/ticket_detail.html",
        context,
    )


# =========================================================
# HELPERS
# =========================================================

def get_status_label(status):

    labels = dict(
        Ticket.Status.choices
    )

    return labels.get(
        status,
        status,
    )


def get_user_display_name(user):

    if not user:
        return "Unassigned"

    full_name = (
        user.get_full_name().strip()
    )

    if full_name:
        return full_name

    return user.username