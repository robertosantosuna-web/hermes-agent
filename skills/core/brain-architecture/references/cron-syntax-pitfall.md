# Cron Syntax Pitfall (discovered 28/05/2026)

## The Bug

ChatGPT detected a critical flaw: `*/15 * * 1-5` means days 1-5 of the month, NOT Monday-Friday.

**Wrong:**
```
*/15 * * 1-5        # runs on days 1,2,3,4,5 of month → NO TRADES for 25 days!
```

**Correct:**
```
*/15 * * * 1-5      # runs Monday-Friday
```

## Cron Field Order (5 fields)

```
minute hour day-of-month month day-of-week
*/15   *    *            *     1-5
```

## Impact

This affected all forex cron jobs — they were only running in the first 5 days of each month. All corrected on 28/05/2026.

## Rule
Always use 5 fields for cron schedules. `day-of-week` is the 5th field. The 3rd field is `day-of-month`.
