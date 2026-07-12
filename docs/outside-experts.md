# Outside Experts — program design

The Outside Expert directory is the revenue layer of CollabFinder. It is
**CollabFinder's own network** of trusted consultants — recruited, vetted,
and credential-verified by the platform — made available inside every
customer workspace when the company's own expertise can't answer. All
booking and payment runs through CollabFinder, and the platform takes a
commission on every booking. This document is the operating process; the
demo implements the directory, attribution, and the platform booking page,
with Stripe payment capture as the launch build.

## 1. Expert sign-up (intake)

1. Expert applies via the CollabFinder expert portal (roadmap: web form; today:
   application email) with: field(s) of expertise, credentials + registry
   numbers where applicable (bar number, cert IDs), rate card, booking page
   URL, two client references.
2. Application creates a `pending` entry — never visible to any workspace.

## 2. Credentialing

An entry moves `pending → verified` only after:

- **Identity check** — government ID + business registration.
- **Credential verification** — certifications checked against issuing
  registries (e.g. USPTO bar, (ISC)² for CISSP, IAAP). Recorded with the
  date checked; re-verified annually.
- **Reference check** — two client references interviewed.
- **Rate + agreement** — signed referral agreement and conduct standards.
  The expert sets their own commission rate at signup (10% platform
  minimum). Commission is a placement bid: among experts matching a query,
  the highest commission appears first. Relevance still gates entry — no
  commission puts an expert on a topic they don't cover.

Directory schema per entry: `status` (`pending|verified|suspended`),
`verified_on`, `commission_percent`. **Only `verified` entries are ever
matched or shown** — enforced in `mcp_server/external.py`, covered by tests.

Suspension path: complaints or failed re-verification flip `status` to
`suspended` — immediate removal from all results, no redeploy needed.

## 3. Referral attribution (built)

- Every booking link CollabFinder renders is tagged:
  `?ref=collabfinder&q=<topic>` — topic only, never user data.
- Every "Book consult" click is recorded to the audit log
  (`referral.click`, expert name, clicking user id, timestamp).
- The click log + URL tag together form the billing evidence: bookings on
  the expert's side that carry the ref tag reconcile against our click log.

## 4. Payments and commission

**All consultation payments run through CollabFinder.** The client books
and pays on the CollabFinder booking page; the platform withholds the
expert's own bid commission (`commission_percent`, expert-set, 10%
minimum) and pays out the remainder. One invoice, one receipt, one place to resolve
disputes — the client never handles the expert's own billing.

Build phases:

1. **Booking page (built)** — every expert has a CollabFinder-hosted
   `/book/<slug>` page showing rate, verification status, and the money
   flow. Booking requests are recorded with query attribution.
2. **Stripe payment capture (launch)** — checkout on the booking page;
   experts onboard via Stripe Connect, the platform's application fee is
   withheld automatically at charge time, payouts are automatic.
3. **Escrow release (scale)** — funds held until the consultation is
   confirmed delivered; dispute window before expert payout.

## 5. Quality loop

- Post-consult, the booking employee gets a 1–5 rating prompt in Slack.
- Ratings feed directory ranking (matched_on overlap × rating).
- Two consecutive ratings ≤2 triggers review; substantiated misconduct →
  `suspended`.
