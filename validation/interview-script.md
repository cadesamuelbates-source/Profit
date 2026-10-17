# Problem interview + demo + offer (about 15–20 minutes)

Rules: ask about **what happened**, not what they *would* do. Don't pitch until part 3.
Write down exact words. A compliment isn't data; a story about a specific deal is.

## Part 0: Qualify (30 seconds, before anything else)

1. "Roughly how many sides did you close in the last 12 months?" (need **12 or more**)
2. "On most of your files, do you pay a transaction coordinator to run the file?" (need **no**)

If either answer fails, thank them and ask: "Who do you know who closes a lot of deals and still
does their own paperwork?" Log them as `qualified = n`.

## Part 1: The last deal (8 minutes)

3. "Walk me through your most recent deal from the moment the contract was signed to closing.
   What did you do first?"
4. "Where did the time go between contract and close? Roughly how many hours?"
5. "Which deadline came closest to being missed? What happened? What did it cost, or almost cost?"
6. "How did your client know what was coming next? How many 'what's happening?' calls or texts
   did you get?"
7. "Who did you chase: lender, title, the other agent, your client? How?"

## Part 2: Current spending and tools (3 minutes)

8. "What do you use today to track dates? Did you pay for it? Does your brokerage provide something?"
9. "Have you ever paid a TC or an assistant per file? How much? Why did you stop or keep going?"
10. "If you had to rank your three biggest time sinks in your business, what are they?"
    → `pain_top3 = y` only if contract-to-close coordination or client updates is in **their**
    top three, unprompted.

## Part 3: Demo and offer (5 minutes)

Show `prototype/samples/demo-packet/timeline.html` on your phone, then the calendar invite and the
checklist.

11. "What, if anything, would this have changed on the deal you just described?"
12. **The ask:** "Do you have a deal under contract right now with at least 10 days to closing?
    Send me the fully signed contract and I'll have this set up and checked today. It's $129,
    invoiced when I deliver it. If it isn't useful, tell me why and don't pay."

## Logging rules (fill tracker.csv the same day)

| They said / did | Log |
|---|---|
| "Love it", "great idea" | `compliment_only = y`, and nothing else |
| Watched the demo | `viewed_demo = y` |
| Sent a contract or deal sheet | `submitted_deal_sheet = y` |
| "Yes, do it, I'll pay" (in writing) | `written_commitment = y` |
| Payment cleared | `first_paid_on`, `revenue_usd` |
| Second paid file | `second_paid_on` |
| Refund or nonpayment after 7 days | `refunded = y` / leave `first_paid_on` empty |

Never log a payment that hasn't cleared, and never round up a "maybe."
