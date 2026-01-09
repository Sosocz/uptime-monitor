# Production QA Checklist - TrezApp

## Status: 🔄 IN PROGRESS

## 1. Authentication & User Management
- [ ] Sign up with email/password
- [ ] Email validation working
- [ ] Login with email/password
- [ ] Forgot password flow (request + reset)
- [ ] OAuth Google login
- [ ] OAuth GitHub login
- [ ] Logout functionality
- [ ] Token expiration handling
- [ ] Protected routes (dashboard requires auth)

## 2. Monitor Management
- [ ] Create new monitor (HTTP/HTTPS URL)
- [ ] Edit existing monitor
- [ ] Delete monitor
- [ ] View monitor details
- [ ] View monitor history
- [ ] Monitor list pagination/filtering
- [ ] Health Grade display (A+ to D)
- [ ] FLAPPING badge display
- [ ] DEGRADING badge display
- [ ] Money lost today calculation

## 3. Incident Management
- [ ] Incident created when site goes down
- [ ] Incident resolved when site comes back up
- [ ] Incident details page
- [ ] Intelligent cause analysis (PRO)
- [ ] Recommendations displayed (PRO)
- [ ] Money lost calculation
- [ ] Minutes lost calculation
- [ ] Incident history view

## 4. Notifications
- [ ] Email notification on DOWN event
- [ ] Email notification on UP/recovery event
- [ ] FREE vs PRO email content difference
- [ ] Upsell block in FREE emails
- [ ] Full analysis in PRO emails
- [ ] Telegram notifications (if configured)
- [ ] Webhook notifications (if configured)
- [ ] Notification cooldown working
- [ ] No duplicate notifications

## 5. Upsell & Conversion Features
- [ ] Upsell modal triggers on incidents (FREE users)
- [ ] Upsell modal triggers on health grade drop
- [ ] Upsell modal 24h cooldown (localStorage)
- [ ] "Upgrade to PRO" button visible
- [ ] /upgrade page loads correctly
- [ ] Stripe checkout redirect working
- [ ] Stripe webhook handles successful payment
- [ ] User plan updated after payment
- [ ] PRO features unlock after upgrade

## 6. Dashboard Features
- [ ] Revenue Protector banner displays
- [ ] Stats update correctly (money protected, incidents, minutes)
- [ ] Health Grade badges color-coded
- [ ] Money lost today per monitor
- [ ] Guided tour button visible
- [ ] Guided tour 4 steps work
- [ ] Tour completion tracked (localStorage)
- [ ] Tooltips display on hover
- [ ] Monitor cards responsive layout
- [ ] Create monitor modal French labels

## 7. Landing Page & Navigation
- [ ] Landing page loads (/)
- [ ] Hero section displays correctly
- [ ] Features section interactive cards
- [ ] "Voir un exemple" buttons work
- [ ] FR/EN language switcher present
- [ ] EN button shows alert message
- [ ] Navigation links work (Fonctionnalités, Pourquoi TrezApp, Tarifs)
- [ ] Footer links all functional
- [ ] CTA buttons lead to /register
- [ ] Responsive on mobile

## 8. SEO & Marketing Pages
- [ ] /why-trezapp page loads
- [ ] All content in French
- [ ] Meta tags correct (title, description)
- [ ] Canonical URLs set
- [ ] Use case pages load (if exist)
- [ ] /upgrade page loads
- [ ] Pricing section displays

## 9. Status Pages
- [ ] Public status page creation
- [ ] Status page displays uptime %
- [ ] Status page shows incident history
- [ ] "Powered by TrezApp" visible (FREE)
- [ ] "Powered by" removable (PRO setting)
- [ ] Custom domain support (if AGENCY)
- [ ] Badge SVG generation working
- [ ] Badge caching working

## 10. API Endpoints
- [ ] /health returns healthy
- [ ] /api/auth/register
- [ ] /api/auth/login
- [ ] /api/auth/forgot-password
- [ ] /api/auth/reset-password
- [ ] /api/auth/oauth/google
- [ ] /api/auth/oauth/github
- [ ] /api/monitors (CRUD)
- [ ] /api/monitors/dashboard/stats
- [ ] /api/monitors/dashboard/enriched
- [ ] /api/incidents (list)
- [ ] /api/stripe/create-checkout
- [ ] /api/stripe/webhook
- [ ] All endpoints require proper auth
- [ ] No sensitive data leaked in responses

## 11. Error Handling & Edge Cases
- [ ] Invalid email format rejected
- [ ] Weak password rejected (< 8 chars)
- [ ] Duplicate email registration blocked
- [ ] Invalid login credentials
- [ ] Expired reset password token
- [ ] Invalid monitor URL rejected
- [ ] Network timeout handled gracefully
- [ ] Database connection error handled
- [ ] Redis connection error handled
- [ ] Empty states display correctly
- [ ] Loading states during API calls
- [ ] Success messages after actions

## 12. Security Tests
- [ ] SQL injection attempts blocked
- [ ] XSS attempts sanitized
- [ ] CSRF protection enabled
- [ ] Rate limiting on login
- [ ] Rate limiting on registration
- [ ] Rate limiting on password reset
- [ ] Private IP addresses blocked for monitors (SSRF)
- [ ] Cloud metadata endpoints blocked (SSRF)
- [ ] Redirects limited
- [ ] Response size limited
- [ ] Timeouts enforced
- [ ] JWT tokens HttpOnly (if using cookies)
- [ ] Secure flag on cookies (HTTPS)
- [ ] CORS properly configured
- [ ] No secrets in logs
- [ ] No secrets in error messages

## 13. Performance & Responsiveness
- [ ] Page load time < 2s
- [ ] API response time < 500ms
- [ ] Images optimized
- [ ] CSS/JS minified (production)
- [ ] Mobile responsive (all pages)
- [ ] Tablet responsive
- [ ] Desktop responsive
- [ ] Touch interactions work on mobile

## 14. Browser Compatibility
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile Safari (iOS)
- [ ] Chrome Mobile (Android)

## 15. Nginx & Infrastructure
- [ ] HTTP → HTTPS redirect
- [ ] www/non-www redirect consistent
- [ ] HSTS header set
- [ ] CSP header set
- [ ] X-Frame-Options set
- [ ] X-Content-Type-Options set
- [ ] Referrer-Policy set
- [ ] Request body size limited
- [ ] Request timeout configured
- [ ] Static file caching
- [ ] Gzip compression enabled

## 16. Database & Data Integrity
- [ ] All migrations run successfully
- [ ] Indexes created for performance
- [ ] No orphaned records
- [ ] Foreign key constraints working
- [ ] Backup system configured
- [ ] Backup restore tested

## 17. Background Workers
- [ ] ARQ worker running
- [ ] Background worker running
- [ ] Email jobs enqueued correctly
- [ ] Email jobs processed
- [ ] Retry logic working on failures
- [ ] Dead letter queue handling
- [ ] Worker health check

## 18. Monitoring & Logging
- [ ] Application logs structured
- [ ] No sensitive data in logs
- [ ] Error tracking configured (Sentry)
- [ ] Worker status monitored
- [ ] Database health monitored
- [ ] Redis health monitored
- [ ] Disk space monitored
- [ ] Alerts configured for failures

## Test Results Summary

### Passed: 0
### Failed: 0
### Blocked: 0
### Total: TBD

---

**Last Updated:** 2026-01-08
**Tester:** Claude (AI Assistant)
**Environment:** Development (localhost:8000)
