# Exness Signup Attempt — 26/05/2026

## Credentials Created
- Email: robertosantos.una@gmail.com
- Password: H3rmesEx2026!
- Country: Brazil

## What failed (all automated approaches)
1. **CDP `el.value = '...'` + React** → React clears values on submit (controlled inputs).
2. **CDP `Input.dispatchKeyEvent` type='char'** → values appear but React validation rejects on submit.
3. **Desktop Daemon `ydotool type`** → ABNT2 layout corrupts @ and !.
4. **Desktop Daemon `xdotool type`** → types correctly but React still rejects (reCAPTCHA Enterprise).
5. **Google OAuth button** → Brave blocks popup, no new tab opens.

## What works
**ONLY manual human signup.** The user must open my.exness.com in their real browser and complete the form. reCAPTCHA Enterprise passes when real human interacts.

## Blockers identified
- `my.exness.com` uses **reCAPTCHA Enterprise** (invisible, embedded via iframe)
- React controlled inputs require genuine keyboard events (not synthetic)
- ABNT2 keyboard layout breaks ydotool for any special character
- Google OAuth popup blocked by Brave's popup blocker

## Next Steps
1. User completes manual signup at https://my.exness.com/
2. Opens demo account (instant, no deposit)
3. Provides: account number + MT5 server name
4. Agent installs MT5 Exness in separate Wine prefix
5. Agent deploys hermes_bridge EA
6. Agent configures bot for dual-broker (IC Markets + Exness)
