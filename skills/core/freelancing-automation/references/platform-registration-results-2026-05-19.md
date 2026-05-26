# Platform Registration Results — 19/05/2026

Session log of autonomous multi-platform registration via Edge CDP.

## Successful (Google OAuth)

### TimeBucks
- URL: https://timebucks.com/
- Method: "Continue with Google" button → Google account chooser → consent → auto-redirect
- Result: ✅ Dashboard loaded, UserID 228886019, $0.30 bonus
- Cash out: $2.70 minimum, PayPal/Payoneer
- Pitfall: None. Google OAuth via CDP perfect.

### Toloka
- URL: https://we.toloka.ai/
- Method: "Continue with Google" → account chooser → consent → phone verification
- Result: ✅ Explore page loaded, profile "Roberto Santos"
- Phone: +55 31 98212-5758 (user completed SMS manually)
- Pitfall: Phone verification required manual SMS code input

## Successful Registration / Email Confirmation Missing

### Neevo
- URL: https://neevo.definedcrowd.com/en-us/account/register/
- Method: Email registration form (FirstName, LastName, Email, Password)
- Form fill: ✅ All fields accepted
- Privacy consent: ✅ Checkboxes checked, "Confirm" clicked
- Result: ⚠️ Stuck at "confirmation email sent" page
- Email check: 0 emails from neevo.ai / definedcrowd.com in INBOX, Spam, or All Mail
- Resend: Clicked "Resend email" — still 0 emails after 30s wait
- Root cause: Gmail appears to block the domain at server level (not user filter)
- Credentials: robertosantos.una@gmail.com / Ne3v0!iHUJgWTng4zb

## Blocked by Bootstrap-select

### Clickworker
- URL: https://workplace.clickworker.com/en/users/new/
- Form: Rails multi-step (Step 1: gender/name/email/password, Step 2: birthday/country, Step 3: languages/address/T&C)
- Text fields: ✅ All filled successfully
- Bootstrap-select fields: Country, Native Language, State — JS value setter + change/input events don't register
- Result: Form filled but can't submit — Bootstrap-select validation fails
- Credentials: robertosantos.una@gmail.com / Cw0rk!OYELp6Abgo / username: robertor_mpbvqz2r

### OneForma
- URL: https://my.oneforma.com/center/signup
- Form: Single page (name, legal name, email, country, password, checkboxes)
- Text fields: ✅ Partially filled
- Country select: Bootstrap or similar custom component — JS setter fails
- Credentials: robertosantos.una@gmail.com / OneF0rm!KCyWyah3

### SproutGigs
- URL: https://sproutgigs.com/signup.php
- Form: Name, nickname, email, password, country
- All fields: ✅ Filled via JS
- Country select: Bootstrap — JS value "br" set but UI shows "Select Country"
- Submit: form.submit() returns to same page (validation fails on country)
- Credentials: robertosantos.una@gmail.com / Spr0ut!Dh27tTiW / nickname: robertor03

## Key Learnings

1. **Google OAuth via CDP works reliably** — the Edge session's Google cookies are inherited
2. **Bootstrap-select is a systemic blocker** for JS automation — needs mouse interaction or jQuery API
3. **React virtualized lists** (Neevo language picker) don't have off-screen items in DOM
4. **Gmail can silently block domains** — no bounce, no spam, just nothing
5. **Standard HTML/Rails forms** accept JS value setters without issues
