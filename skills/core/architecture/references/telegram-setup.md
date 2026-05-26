# Telegram Setup — Lessons Learned

Session: 2026-05-17 ENTIDADE reconstruction

## Phone Number Format
- Telethon requires FULL international format: `+55XXXXXXXXXXX`
- Plain number without country code (e.g., `31982125758`) returns `PhoneNumberInvalidError`
- With `+55` prefix: code request succeeds and sends confirmation to Telegram app

## API Credentials
- Must be obtained from https://my.telegram.org/auth
- Login requires phone number + confirmation code (sent via Telegram, not SMS)
- Default embedded credentials (api_id=2040) work but are shared — creating own app is preferred
- `ApiIdInvalidError` means the api_id/api_hash pair is wrong — regenerate at my.telegram.org

## Browser Login Flow
1. Navigate to https://my.telegram.org/auth
2. Enter phone in international format
3. Confirmation code arrives in Telegram Desktop
4. After login, navigate to "API Development Tools"
5. Create new app to get api_id and api_hash

## Pitfalls
- Brave browser not blocked by my.telegram.org (no User-Agent check)
- Session is per-browser — logging in on Brave doesn't transfer to Edge
- Code may take 30-60s to arrive; if it doesn't, request re-send

## Automated Login (via browser tools)
1. `browser_navigate("https://my.telegram.org/auth")`
2. `browser_type` phone number in international format
3. `browser_click` Next
4. Wait for user to provide confirmation code (cannot be automated — arrives in Telegram app)
5. `browser_type` code
6. `browser_click` Sign In
7. Navigate to API page and extract api_id/api_hash from DOM
