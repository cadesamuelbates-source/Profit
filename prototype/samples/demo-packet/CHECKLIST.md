# Verification checklist: deal DEMO-2026-0001

Profile: `example-generic`. Status: **EXAMPLE ONLY - not verified against any state's contract form. Replace with a profile built from your state's current form and reviewed by your broker or an attorney before real use.**

Before anything is shared with a client, check every date below against the **fully executed**
contract and all addenda. The effective date is the date of final acceptance (the last
counteroffer signature), not the date the offer was drafted.

- [ ] **Earnest money delivered to escrow**: Mon Oct 19, 2026 5:00 PM CDT  
  computed: effective date Wed Oct 14, 2026 + 3 calendar days (after) = Sat Oct 17, 2026; not a business day, rolled forward to Mon Oct 19, 2026  
  contract paragraph: ______  matches? Y / N
- [ ] **Inspection period ends**: Sat Oct 24, 2026 5:00 PM CDT  
  computed: effective date Wed Oct 14, 2026 + 10 calendar days (after) = Sat Oct 24, 2026; falls on a non-business day and this rule does NOT roll  
  contract paragraph: ______  matches? Y / N
- [ ] **Seller response to repair request expected**: Tue Oct 27, 2026 5:00 PM CDT  
  computed: Inspection period ends Sat Oct 24, 2026 + 2 business days (after) = Tue Oct 27, 2026  
  contract paragraph: ______  matches? Y / N
- [ ] **Title commitment review ends**: Thu Oct 29, 2026 5:00 PM CDT  
  computed: effective date Wed Oct 14, 2026 + 15 calendar days (after) = Thu Oct 29, 2026  
  contract paragraph: ______  matches? Y / N
- [ ] **Appraisal deadline**: Wed Nov 4, 2026 5:00 PM CST  
  computed: effective date Wed Oct 14, 2026 + 21 calendar days (after) = Wed Nov 4, 2026  
  contract paragraph: ______  matches? Y / N
- [ ] **Loan approval deadline**: Mon Nov 9, 2026 5:00 PM CST  
  computed: effective date Wed Oct 14, 2026 + 25 calendar days (after) = Sun Nov 8, 2026; not a business day, rolled forward to Mon Nov 9, 2026  
  contract paragraph: ______  matches? Y / N
- [ ] **Homeowner's insurance bound**: Fri Nov 13, 2026 5:00 PM CST  
  computed: closing date Fri Nov 20, 2026 - 7 calendar days (before) = Fri Nov 13, 2026  
  contract paragraph: ______  matches? Y / N
- [ ] **Final walkthrough**: Thu Nov 19, 2026 4:00 PM CST  
  computed: closing date Fri Nov 20, 2026 - 1 calendar day (before) = Thu Nov 19, 2026  
  contract paragraph: ______  matches? Y / N
- [ ] **Closing**: Fri Nov 20, 2026 10:00 AM CST  
  computed: closing date as written: Fri Nov 20, 2026  
  contract paragraph: ______  matches? Y / N

## Warnings (resolve or explain before sending)

- 'Inspection period ends' lands on Sat Oct 24, 2026 (non-business day) and does not roll; confirm the contract's weekend/holiday rule for this deadline

## Sign-off

When every box is checked, run `python -m c2c verify <this folder>`. That records setup time.
