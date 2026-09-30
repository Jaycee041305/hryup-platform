# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added (Phase 1)
- Project skeleton and dependency configurations (`requirements.txt`, `build.sh`, `.env.example`).
- Split settings architecture (`base.py`, `dev.py`, `prod.py`).
- Core app with abstract `TenantModel` and multi-tenant manager.
- Security mixins (`RoleRequiredMixin`, `CompanyAccessMixin`, `TenantQuerySetMixin`, etc.).
- Custom `User` model using email for authentication.
- Role-based access control (Admin, Staff, Client Manager, Client Employee).
- Companies app with `Company`, `SubscriptionPackage`, and `Subscription` models.
- Audit app with `AuditLog` model and authentication signals.
- Complete Bootstrap 5 frontend template suite (Landing, Login, Signup, Dashboards, Layouts).
- Professional UI theme matching the HRyUp logo (Navy & Gold).
- Management commands: `create_initial_admin`, `seed_packages`, `backup_db`.
- Comprehensive test suite for Phase 1 models, permissions, and audit logging (100% pass).
