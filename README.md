# BARM Digital Call Center Ticketing System

A Django starter application for logging and managing call-center incidents across seven configurable province/operational areas.

## Included
- Seven configurable province slots, with one seeded call-center agent per province.
- Roles: Administrator, Call Center Agent, IT, Technician, Electrician.
- Categories: No Internet, No Signal, Tower Down / Damage, No Power, Slow Internet, Equipment / Router Issue, Electrical / Generator Issue, Other.
- Ticket statuses: New, Assigned, In Progress, Pending / Waiting, Resolved, Closed, Reopened.
- Priorities: Low, Medium, High, Critical.
- Assignment, dashboard counts, ticket search/filtering, activity/history notes, resolved/closed timestamps.
- Django Admin for managing provinces, users, categories, and tickets.

## Setup
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations tickets
python manage.py migrate
python manage.py seed_barm
python manage.py runserver
```
Open `http://127.0.0.1:8000/`. Admin is at `/admin/`.

## Demo users
The seed command creates `admin`, `agent1` through `agent7`, `it1`, `tech1`, and `electrician1`. Initial demo password: `ChangeMe123!`. **Change every password before real use.**

## Configure your seven provinces
The seed command intentionally creates `Province 1` ... `Province 7`, because your requested seven operational provinces may differ from the current official BARMM administrative composition. Sign in as admin, open **Admin → Provinces**, and rename the seven rows to the exact areas BARM Digital supports.

## Recommended production improvements
Use PostgreSQL, environment variables for `SECRET_KEY`/database settings, HTTPS, proper password validators, backups, audit retention, attachment uploads, SLA/escalation timers, email/SMS notifications, and a production WSGI/ASGI server.
