# Multi-Platform Registration Results — 2026-05-19

## Summary

Automated registration across 7 platforms via Edge CDP. 5 platforms successfully registered or partially registered.
2 platforms cancelled (low priority). Main blocker: **Bootstrap-select custom dropdowns** that don't respond to JS value setters.

## Results

| Platform | Type | Status | Blocker |
|----------|------|--------|---------|
| Neevo | Email signup | ✅ Active | Confirmation email didn't arrive initially; resolved after resend + manual confirmation |
| Toloka | Google OAuth | ✅ Active | Phone verification completed by user (SMS) |
| TimeBucks | Google OAuth | ✅ Active | Instant — Google OAuth completed silently in background tab |
| SproutGigs | Email signup | ⚠️ Pending | Bootstrap-select country dropdown — JS setter doesn't trigger React UI |
| Clickworker | Email signup | ⚠️ Pending | Bootstrap-select country/language/state dropdowns (3 fields) |
| OneForma | Email signup | ⚠️ Pending | Bootstrap-select country + checkboxes |
| GoTranscript | — | ❌ Cancelled | Low priority |
| GetNinjas | — | ❌ Cancelled | Low priority |

## Bootstrap-Select Problem (Detailed)

**Platforms affected:** SproutGigs, Clickworker, OneForma

**What was tried:**
1. `select.value = "br"` + `dispatchEvent(new Event("change"))` → FAIL
2. `select.options[i].selected = true` + `dispatchEvent` → FAIL
3. Native setter: `Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value').set.call(select, "br")` → FAIL
4. jQuery: `$(select).selectpicker('val', 'br')` → jQuery not available in page context
5. `Input.dispatchKeyEvent` typing country name → FAIL (custom React component, not native input)

**Root cause:** Bootstrap-select wraps the native `<select>` with a custom UI component. The JS value setter updates the hidden native select, but the Bootstrap-select widget only responds to its own internal API or direct mouse clicks.

**Workaround:** User must manually click the dropdown and select the option. CDP mouse click on the Bootstrap-select button + click on the dropdown option could work but requires precise coordinate targeting and the option may not be in the viewport.

## Neevo Language Test (Timed Interactive)

**Risk level: HIGH** — Do NOT automate.

The Neevo Writing Test:
- 5 sections, 24 questions, ~30 minutes total
- Each section is TIMED (~5 min)
- Cannot be paused once started
- Interactive elements: click on blanks in text, select incorrect words with mouse
- Failed attempt = wasted certification opportunity

**Recommendation:** Report to user and recommend manual completion.
