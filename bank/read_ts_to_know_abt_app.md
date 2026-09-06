# Banking System API

A production-style banking backend built as a learning project to master full-stack development, API security, and relational database design. Built with FastAPI, SQLAlchemy, and SQLite.

## Features

- **Authentication**: JWT-based auth with bcrypt password hashing, session invalidation via a token blocklist, and email verification + 2FA on every login
- **Accounts**: Checking and savings accounts with auto-generated 10-digit account numbers, overdraft limits, and interest rates
- **ACID P2P Transfers**: Atomic, race-condition-safe money transfers using row-level locking (`SELECT ... FOR UPDATE`) and a double-entry-style debit/credit ledger
- **Fraud Detection**: Daily transfer caps, velocity limits (rapid-fire transfer detection), and automatic flagging of high-value transfers
- **Audit Logging**: An immutable, insert-only log of security-relevant events (logins, account creation, flagged transfers), including IP address capture
- **Analytics**: Balance history and spending breakdown endpoints, ready to power chart visualizations
- **PDF Statements**: Downloadable, formatted account statements generated with ReportLab
- **Scheduled Jobs**: Simulated interest compounding and recurring auto-payments
- **Hardened**: Rate-limited login (brute-force protection), CORS configured, admin-only endpoints protected by a shared secret

## Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy ORM, Pydantic
- **Database**: SQLite (with foreign key enforcement enabled)
- **Auth**: JWT (python-jose), bcrypt
- **PDF Generation**: ReportLab
- **Rate Limiting**: SlowAPI

## Key Engineering Decisions

- **Money is stored as integer cents, never floats** — avoids floating-point rounding errors in financial calculations.
- **Every transfer produces two linked transaction rows** (a debit and a credit sharing a `transfer_id`), rather than a single row — mirroring real double-entry bookkeeping and making balance history/statements straightforward to reconstruct.
- **Row-level locking (`with_for_update()`) prevents race conditions** where two simultaneous transfers could both read a stale balance and over-withdraw funds.
- **Authentication vs. Authorization are treated as separate concerns** throughout — every resource-fetching endpoint verifies both "who are you" and "do you own this," closing IDOR (Insecure Direct Object Reference) vulnerabilities.
- **Audit log entries are never committed independently of the action they describe** — they're added to the same database transaction as the real event, so the audit trail can never contain a record of something that didn't actually happen.
- **A known limitation**: the scheduled-jobs endpoints are triggered manually (no real cron/Celery integration), since this is a local dev project. If a job hasn't run in a long time, it will "catch up" by processing every missed cycle rather than skipping ahead — acceptable for a demo, but would need a catch-up cap in production.
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
4. Run the server:
```bash
   uvicorn app.main:app --reload
```
5. Explore the interactive API docs at `http://127.0.0.1:8000/docs`.

## API Overview

| Area | Endpoints |
|---|---|
| Auth | `POST /auth/register`, `POST /auth/verify-email`, `POST /auth/login`, `POST /auth/login/verify-2fa`, `GET /auth/me`, `POST /auth/logout` |
| Accounts | `POST /accounts/`, `GET /accounts/`, `GET /accounts/{id}` |
| Transfers | `POST /transactions/transfer` |
| Analytics | `GET /analytics/accounts/{id}/balance-history`, `GET /analytics/accounts/{id}/spending-breakdown`, `GET /analytics/accounts/{id}/statement` |
| Admin (secret-protected) | `POST /accounts/run-interest-job`, `POST /accounts/run-scheduled-payments-job` |

## Status

Backend complete (Phases 1–10 of development). A frontend web UI is in progress.

## Disclaimer

This is an educational project, not a real financial product. It has not undergone professional security auditing and should not be used to handle real money or real personal data.