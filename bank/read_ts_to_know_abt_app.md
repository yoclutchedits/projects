# Banking System API

A production-style banking backend (with an in-progress frontend) built as a learning project to master full-stack development, API security, and relational database design. Built with FastAPI, SQLAlchemy, and SQLite.

## Features

- **Authentication**: JWT-based auth with bcrypt password hashing, session invalidation via a token blocklist, and email verification + optional 2FA on login
- **Settings**: Per-user 2FA toggle (password-confirmed), editable profile name, notification preferences, all via a partial-update settings endpoint
- **Accounts**: Checking and savings accounts with auto-generated 10-digit account numbers, overdraft limits, and interest rates
- **ACID P2P Transfers**: Atomic, race-condition-safe money transfers using row-level locking (`SELECT ... FOR UPDATE`) and a double-entry-style debit/credit ledger
- **Fraud Detection**: Daily transfer caps, velocity limits (rapid-fire transfer detection), and automatic flagging of high-value transfers
- **Audit Logging**: An immutable, insert-only log of security-relevant events (logins, account creation, flagged transfers), including IP address capture
- **Analytics**: Balance history and spending breakdown endpoints, ready to power chart visualizations
- **PDF Statements**: Downloadable, formatted account statements generated with ReportLab
- **Scheduled Jobs**: Simulated interest compounding and recurring auto-payments, protected behind an admin secret header
- **Real Email**: Verification and 2FA codes are sent via real Gmail SMTP, not simulated
- **Hardened**: Rate-limited login (brute-force protection), CORS configured, admin-only endpoints protected by a shared secret
- **Frontend (in progress)**: A vanilla HTML/CSS/JS login and registration flow, served directly by FastAPI's static file mount (no build step, no CORS complexity)

## Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy ORM, Pydantic
- **Database**: SQLite (with foreign key enforcement enabled)
- **Auth**: JWT (python-jose), bcrypt
- **Email**: Gmail SMTP via `smtplib`
- **PDF Generation**: ReportLab
- **Rate Limiting**: SlowAPI
- **Frontend**: HTML5, CSS, vanilla JavaScript (Fetch API), served as static files by FastAPI

## Key Engineering Decisions

- **Money is stored as integer cents, never floats** — avoids floating-point rounding errors in financial calculations.
- **Every transfer produces two linked transaction rows** (a debit and a credit sharing a `transfer_id`), rather than a single row — mirroring real double-entry bookkeeping and making balance history/statements straightforward to reconstruct.
- **Row-level locking (`with_for_update()`) prevents race conditions** where two simultaneous transfers could both read a stale balance and over-withdraw funds.
- **Authentication vs. Authorization are treated as separate concerns** throughout — every resource-fetching endpoint verifies both "who are you" and "do you own this," closing IDOR (Insecure Direct Object Reference) vulnerabilities.
- **Audit log entries are never committed independently of the action they describe** — they're added to the same database transaction as the real event, so the audit trail can never contain a record of something that didn't actually happen.
- **2FA is opt-out, not opt-in** — new users default to `two_fa_enabled = True`; disabling it requires re-entering the current password, since it's a security-sensitive change.
- **Settings updates use a partial-update pattern** (`is not None` checks, not truthy checks) — this correctly distinguishes "the client didn't send this field" from "the client explicitly set this field to `false`," a common source of silent bugs in PATCH endpoints.
- **The frontend is served same-origin via FastAPI's `StaticFiles` mount** rather than a separate dev server, deliberately avoiding CORS complexity for a project with no build step.
- **A known limitation**: the scheduled-jobs endpoints are triggered manually (no real cron/Celery integration), since this is a local dev project. If a job hasn't run in a long time, it will "catch up" by processing every missed cycle rather than skipping ahead — acceptable for a demo, but would need a catch-up cap in production.
- **Schema migrations are done by hand** (`ALTER TABLE`) rather than with a tool like Alembic, since this is a single-developer learning project. A real production system with multiple developers should use a proper migration tool instead.
- **SQLite vs. production databases**: this project uses SQLite for simplicity, but the locking strategy (`with_for_update()`) is written to be portable to a database with real row-level concurrency (e.g. PostgreSQL) with no code changes.

## Setup

1. Clone the repo and navigate to the project folder.
2. Create a virtual environment and install dependencies:
```bash
   pip install -r requirements.txt
```
3. Copy `.env.example` to `.env` and fill in real values:
```bash
   cp .env.example .env
```
   Generate secrets with:
```bash
   python -c "import secrets; print(secrets.token_hex(32))"
```
   For `GMAIL_ADDRESS`/`GMAIL_APP_PASSWORD`, enable 2-Step Verification on a Gmail account, then generate an App Password under Google Account → Security → App Passwords.
4. Run the server:
```bash
   uvicorn app.main:app --reload
```
5. Explore the interactive API docs at `http://127.0.0.1:8000/docs`, or the web UI at `http://127.0.0.1:8000/static/index.html`.

## API Overview

| Area | Endpoints |
|---|---|
| Auth | `POST /auth/register`, `POST /auth/verify-email`, `POST /auth/login`, `POST /auth/login/verify-2fa`, `GET /auth/me`, `POST /auth/logout` |
| Settings | `PATCH /auth/settings`, `POST /auth/toggle-2fa` |
| Accounts | `POST /accounts/`, `GET /accounts/`, `GET /accounts/{id}` |
| Transfers | `POST /transactions/transfer` |
| Analytics | `GET /analytics/accounts/{id}/balance-history`, `GET /analytics/accounts/{id}/spending-breakdown`, `GET /analytics/accounts/{id}/statement` |
| Admin (secret-protected) | `POST /accounts/run-interest-job`, `POST /accounts/run-scheduled-payments-job` |

## Status

Backend complete. Frontend in progress: login and registration flows are functional; dashboard, account views, transfers, charts, statements, and settings pages are still being built.

## Disclaimer

This is an educational project, not a real financial product. It has not undergone professional security auditing and should not be used to handle real money or real personal data.