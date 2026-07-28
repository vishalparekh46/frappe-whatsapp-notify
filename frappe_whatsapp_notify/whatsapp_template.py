"""
whatsapp_template.py
--------------------
WhatsApp Business API template management for frappe-whatsapp-notify.

Handles rendering approved templates with variable substitution,
validating template bodies, listing cached templates, and syncing
approved templates from the WhatsApp Business API.
"""

import re
import frappe

# WhatsApp Business API body character limit
_MAX_BODY_LENGTH = 1024

# Positional variable pattern: {{1}}, {{2}}, ...
_VAR_RE = re.compile(r"\{\{(\d+)\}\}")


def render_template(template_name, variables):
    """Return rendered body with positional variables substituted."""
    tmpl = _get_template(template_name)
    if not tmpl.enabled:
        frappe.throw(f"WhatsApp template '{template_name}' is disabled.")
    required = _count_vars(tmpl.body)
    if len(variables) < required:
        raise ValueError(
            f"Template '{template_name}' needs {required} var(s), got {len(variables)}."
        )
    return _VAR_RE.sub(lambda m: str(variables[int(m.group(1)) - 1]), tmpl.body)


def validate_template(body):
    """Validate a template body: non-empty, within 1024 chars, no gap in {{n}} vars."""
    errors = []
    if not body or not body.strip():
        return {"valid": False, "errors": ["Body must not be empty."], "variable_count": 0}
    if len(body) > _MAX_BODY_LENGTH:
        errors.append(f"Body exceeds {_MAX_BODY_LENGTH} chars (got {len(body)}).")
    indices = sorted(set(int(m.group(1)) for m in _VAR_RE.finditer(body)))
    if indices:
        missing = set(range(1, max(indices) + 1)) - set(indices)
        if missing:
            errors.append("Missing vars: " + ", ".join(f"{{{{{n}}}}}" for n in sorted(missing)))
    return {"valid": not errors, "errors": errors, "variable_count": len(indices)}


def list_approved_templates():
    """Return all enabled WhatsApp Template docs from Frappe."""
    rows = frappe.get_all(
        "WhatsApp Template",
        filters={"enabled": 1},
        fields=["name", "template_name", "language", "category", "body"],
        order_by="template_name asc",
    )
    return [
        {
            "name": r["name"],
            "template_name": r["template_name"],
            "language": r["language"],
            "category": r["category"],
            "variable_count": _count_vars(r["body"]),
        }
        for r in rows
    ]


def sync_templates_from_api():
    """Fetch approved templates from the WhatsApp Business API and
    upsert them as WhatsApp Template documents in Frappe.

    Returns:
        dict: {"created": int, "updated": int, "skipped": int}
    """
    import requests

    settings = frappe.get_doc("WhatsApp Settings", "WhatsApp Settings")
    if not settings.enabled:
        frappe.throw("WhatsApp integration is disabled.")

    base = settings.api_endpoint.rstrip("/").rsplit("/messages", 1)[0]
    headers = {"Authorization": f"Bearer {settings.api_token}"}

    try:
        resp = requests.get(f"{base}/message_templates", headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        frappe.log_error(message=str(exc), title="WhatsApp Template Sync Error")
        frappe.throw(f"API fetch failed: {exc}")

    created = updated = skipped = 0
    for tmpl in data.get("data", []):
        if tmpl.get("status") != "APPROVED":
            skipped += 1
            continue
        body = next(
            (c.get("text", "") for c in tmpl.get("components", []) if c["type"] == "BODY"),
            "",
        )
        if not body:
            skipped += 1
            continue
        existing = frappe.db.exists("WhatsApp Template", {"template_name": tmpl["name"]})
        if existing:
            doc = frappe.get_doc("WhatsApp Template", existing)
            doc.body = body
            doc.language = tmpl.get("language", "en")
            doc.save(ignore_permissions=True)
            updated += 1
        else:
            doc = frappe.new_doc("WhatsApp Template")
            doc.template_name = tmpl["name"]
            doc.language = tmpl.get("language", "en")
            doc.category = tmpl.get("category", "")
            doc.body = body
            doc.enabled = 1
            doc.insert(ignore_permissions=True)
            created += 1

    frappe.db.commit()
    return {"created": created, "updated": updated, "skipped": skipped}


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _get_template(template_name):
    try:
        return frappe.get_doc("WhatsApp Template", {"template_name": template_name})
    except frappe.DoesNotExistError:
        frappe.throw(f"WhatsApp template '{template_name}' not found.")


def _count_vars(body):
    return len(set(int(m.group(1)) for m in _VAR_RE.finditer(body)))
