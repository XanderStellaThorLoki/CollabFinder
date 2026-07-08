# Outside Experts — program design

The Outside Expert directory is the revenue layer of CollabFinder: when the
org's internal expertise map can't answer (or a team wants outside firepower),
CollabFinder surfaces vetted external consultants and earns a commission on
the business it refers. This document is the operating process; the demo
implements the attribution layer and directory schema, and marks the payment
mechanics as post-hackathon build.

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
- **Rate + agreement** — signed referral agreement (commission percentage,
  currently 15%) and conduct standards.

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

## 4. Commission collection (post-hackathon)

The platform fee is charged to the **expert**, not the person booking —
the org's employees never pay to use CollabFinder suggestions.

Planned mechanics, in order of build:

1. **Invoice reconciliation (launch)** — monthly statement to each expert
   listing ref-tagged bookings; expert remits the commission percentage.
   Simple, auditable, no payment infrastructure required.
2. **Stripe Connect (scale)** — experts onboard to a connected account;
   bookings flow through the platform checkout and the application fee is
   withheld automatically at booking time. Removes trust dependency.
3. **Deposit/escrow option** — high-volume experts maintain a small deposit
   balance drawn down per referral, refundable on exit. Only if
   reconciliation friction demands it.

Non-negotiable boundary at every stage: **consultation payment happens on
the expert's own checkout.** CollabFinder handles attribution and the
platform fee — it is never custodian of the client's consultation money.

## 5. Quality loop

- Post-consult, the booking employee gets a 1–5 rating prompt in Slack.
- Ratings feed directory ranking (matched_on overlap × rating).
- Two consecutive ratings ≤2 triggers review; substantiated misconduct →
  `suspended`.
