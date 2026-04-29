# Changelog

All notable changes to **frappe-whatsapp-notify** will be documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Added
- `CONTRIBUTING.md` with development guidelines
- `CHANGELOG.md` for version tracking

## [0.0.1] - 2026-04-01

### Added
- Initial release
- WhatsApp Settings DocType with Twilio credentials (Account SID, Auth Token, From Number)
- WhatsApp Settings controller with phone number validation
- Doc event hooks for Sales Order, Sales Invoice, and Payment Entry on submission
- Daily scheduled task for overdue Sales Invoice payment reminders
- `send_whatsapp_message()` utility with error handling and phone number normalisation
- TwilioRestException handling with Frappe error logging
- `api/__init__.py` for proper Python module structure
- Unit tests for core send functions
- `requirements.txt` (twilio>=8.0.0)
- `setup.py` for bench installation
- `patches.txt` for bench migration support
