# Uptime Monitor — User Guide

## What is this?
Uptime Monitor helps you monitor websites or APIs and alerts you when they go **DOWN** and when they come back **UP**.

---

## 11) Analytics (optional)
Product analytics and session replay are disabled by default. They are enabled only when:
- `APP_ENV=production`
- The relevant keys are provided (PostHog, Clarity, GA4)

---

## 12) CI/CD
GitHub Actions runs:
- Python compile checks
- Pytest
- Docker build

## 1) Create an account
1. Open the website
2. Click **Register**
3. Enter your email and password
4. Confirm

Then log in using **Login**.

---

## 2) Dashboard overview
The **Dashboard** shows:
- Your list of monitors
- Current status of each monitor:
  - **UP** → the site is reachable
  - **DOWN** → the site is not responding or returned an error
- Check interval (how often the site is checked)
- Recent check history

---

## 3) Add a monitor (monitor a website)
1. Go to **Dashboard**
2. Click **Add Monitor**
3. Fill in:
   - **Name** → example: “Main Website”
   - **URL** → example: `https://example.com`
   - **Timeout** → max wait time (e.g. 5–10 seconds)
4. Click **Create**

➡️ The monitor is immediately activated and checked automatically.

---

## 4) Edit a monitor
1. Open a monitor from the list
2. Click **Edit**
3. Update name, URL, timeout, or status
4. Click **Save**

---

## 5) Pause / Resume monitoring
You can temporarily stop checks:
- Disable the monitor
- Enable it again anytime

---

## 6) Delete a monitor
1. Open the monitor
2. Click **Delete**
3. Confirm

⚠️ Deleting a monitor may remove its history.

---

## 7) Notifications
When a monitor goes **DOWN** or comes back **UP**, you can receive alerts.

Available notification methods:
- **Email**
- **Telegram** (if configured)

If you don’t receive notifications, check your notification settings.

---

## 8) Pro plan (if available)
The Pro plan allows:
- More monitors
- Faster check intervals

To upgrade:
1. Open **Upgrade / Pro**
2. Click **Buy / Subscribe**
3. Complete payment via **Stripe**
4. You will be redirected back to the dashboard

---

## 9) Understanding DOWN alerts
A DOWN status can be caused by:
- The website being offline
- Wrong URL
- Firewall blocking the server
- Timeout too low
- Temporary network issues

Tip: Always test the URL manually when you receive a DOWN alert.

---

## 10) Best practices
- Monitor a dedicated health endpoint if available (`/health`, `/status`)
- Use reasonable timeouts (10 seconds recommended)
- Give clear names to your monitors
- Start with a small number of monitors

---
