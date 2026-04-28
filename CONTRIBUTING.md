# Contributing to frappe-whatsapp-notify

Thanks for your interest in contributing! Here's how to get started.

## Reporting Bugs

- Open an issue with your Frappe/ERPNext version, Twilio account type, and a clear description
- Include any error messages from the Frappe Error Log

## Submitting a Pull Request

1. Fork the repo and create a descriptive branch:
   ```bash
   git checkout -b feat/waba-template-support
   ```

2. Make your changes and test on a local bench:
   ```bash
   bench --site your-site.local install-app frappe_whatsapp_notify
   bench --site your-site.local migrate
   ```

3. Commit using Conventional Commits:
   ```
   feat(whatsapp): add support for WABA message templates
   fix(scheduler): handle missing mobile number gracefully
   ```

4. Open a PR against `develop` with a clear description

## Adding New Notification Triggers

1. Add your handler in `frappe_whatsapp_notify/api/whatsapp.py`
2. Register the doc event in `frappe_whatsapp_notify/hooks.py`
3. Always use `_get_customer_mobile()` and wrap sends in try/except

## Code Style

- Follow PEP 8 for Python
- Use `frappe.log_error()` for errors, `frappe.logger()` for debug/info
- Never store credentials in plain text — use Frappe Password fields

## Questions?

Open an issue or post on [discuss.frappe.io](https://discuss.frappe.io)
