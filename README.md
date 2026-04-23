# 📲 frappe-whatsapp-notify

> Send WhatsApp notifications automatically from ERPNext — on Sales Order confirmation, Invoice generation, Payment receipt, and overdue payment reminders.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Frappe](https://img.shields.io/badge/Frappe-v14%2B-blue)](https://frappe.io)
[![ERPNext](https://img.shields.io/badge/ERPNext-v14%2B-1abc9c)](https://erpnext.com)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)

---

## ✨ Features

- ✅ **Sales Order confirmation** — auto WhatsApp when order is submitted
- 🧾 **Invoice notification** — send invoice details on submission
- 💰 **Payment receipt** — confirm payment via WhatsApp instantly
- ⚠️ **Overdue reminders** — daily scheduled task for unpaid invoices
- 🔌 Powered by **Twilio WhatsApp API** (easy to swap for WABA direct)

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

## 🔑 Configuration

1. Go to **ERPNext → Settings → WhatsApp Settings**
2. Fill in your **Twilio Account SID**, **Auth Token**, and **From Number**
3. Enable the setting and save

> ⚠️ Auth Token is stored encrypted using Frappe's built-in password field.

---

## 🛠️ How It Works

The app hooks into ERPNext document events via `hooks.py`:

| Event | Trigger |
|---|---|
| Sales Order submitted | WhatsApp order confirmation to customer |
| Sales Invoice submitted | Invoice amount & due date notification |
| Payment Entry submitted | Payment receipt confirmation |
| Daily scheduler | Overdue invoice reminders |

---

## 📁 Project Structure

```
frappe_whatsapp_notify/
├── api/
│   ├── whatsapp.py       # Core message sending + doc event handlers
│   └── scheduler.py      # Daily overdue reminder task
├── doctype/              # WhatsApp Settings DocType
├── hooks.py              # Frappe hooks — doc events & scheduler
└── __init__.py
```

---

## 🤝 Contributing

Pull requests are welcome! Please:

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit with clear messages (`feat: add template support`)
4. Open a PR against `develop`

---

## 📄 License

MIT — see [LICENSE](LICENSE)

---

## 👤 Author

**Vishal Parekh** — ERPNext & Frappe Developer at [Aavatto](https://aavatto.com)

- GitHub: [@vishalparekh46](https://github.com/vishalparekh46)
- LinkedIn: [vishalparekh46](https://linkedin.com/in/vishalparekh46)
- Forum: [discuss.frappe.io](https://discuss.frappe.io)
