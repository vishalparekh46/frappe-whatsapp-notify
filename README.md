# 📱 frappe-whatsapp-notify

> Send WhatsApp notifications automatically from ERPNext – on Sales Order confirmation, Invoice generation, Payment receipt, and overdue payment reminders.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Frappe](https://img.shields.io/badge/Frappe-v14%2B-blue)](https://frappe.io)
[![ERPNext](https://img.shields.io/badge/ERPNext-v14%2B-1abc9c)](https://erpnext.com)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)

---

## ✨ Features

- ✅ **Sales Order confirmation** – auto WhatsApp when order is submitted
- 🧾 **Invoice notification** – send invoice details on submission
- 💰 **Payment receipt** – confirm payment via WhatsApp instantly
- ⚠️ **Overdue reminders** – daily scheduled task for unpaid invoices
- 🔌 Powered by **Twilio WhatsApp API** (easy to swap for WABA direct)

---

## ⚙️ How It Works

The app hooks into Frappe's document event system. When key business documents are submitted in ERPNext, the corresponding WhatsApp message fires automatically via Twilio.

| DocType | Event | Trigger | Message Sent |
|---|---|---|---|
| **Sales Order** | `on_submit` | Order confirmed by user | "Your Sales Order {name} for ₹{amount} has been confirmed." |
| **Sales Invoice** | `on_submit` | Invoice saved & submitted | "Invoice {name} of ₹{amount} is ready. Due: {due_date}." |
| **Payment Entry** | `on_submit` | Payment received/recorded | "Payment of ₹{amount} received against {invoice}. Thank you!" |
| **Scheduler** | `daily` | Runs every night at midnight | Sends overdue reminders for all unpaid invoices past due date |

### Doc Event Flow

```
ERPNext Submit → hooks.py doc_events → api/whatsapp.py → Twilio API → Customer WhatsApp
```

### Scheduler Flow

```
Frappe Scheduler (daily) → hooks.py scheduler_events → api/scheduler.py
  → frappe.get_all(Sales Invoice, overdue) → send_whatsapp_message() per invoice
```

### Phone Number Handling

All phone numbers are normalised to E.164 format (+91XXXXXXXXXX) by `utils.normalise_phone()` before sending. Invalid or missing numbers are logged and skipped gracefully.

---

## 📋 Requirements

- Frappe v14+
- ERPNext v14+
- Twilio account with WhatsApp sender enabled

---

## ⚙️ Installation

```bash
# Navigate to your frappe-bench directory
cd ~/frappe-bench

# Get the app
bench get-app https://github.com/vishalparekh46/frappe-whatsapp-notify

# Install on your site
bench --site your-site.local install-app frappe_whatsapp_notify

# Run migrations
bench --site your-site.local migrate
```

---

## 🔧 Configuration

1. Go to **WhatsApp Settings** in ERPNext
2. Enable the app (toggle **Enabled**)
3. Enter your Twilio **Account SID** and **Auth Token**
4. Enter your Twilio WhatsApp **From Number** (e.g. `whatsapp:+14155238886`)
5. Save

---

## 🧪 Running Tests

```bash
bench --site your-site.local run-tests --app frappe_whatsapp_notify
```

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on branch naming, commit format, and how to add new notification triggers.

---

## 📄 License

MIT — see [LICENSE](LICENSE)
