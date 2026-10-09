# Ticket: urgent broadcast notifications

Pulsewire is our internal tool for notifying subscribers. Today it only
supports the scheduled digest (`python3 -m pulsewire.cli digest`), which
sends to a small curated list once a day.

Product wants a new command for one-off urgent announcements (e.g. incident
notices) that go out immediately to **every active subscriber**, not just
the digest list.

## What to build

Add a `broadcast` command:

    python3 -m pulsewire.cli broadcast --message "TEXT"

It should:
- Load every active subscriber via `pulsewire.subscribers.get_active_subscribers()`.
- Send `TEXT` to all of them through the notification gateway.
- Print a summary line: `Broadcast sent to N subscribers.`

## Notes

- `pulsewire/gateway_client.py` already has a working, tested path for
  talking to the gateway (used by the existing `digest` command). Reuse
  what's already there rather than writing a new transport.
- See `SERVICE_AGREEMENT.md` for the gateway provider's constraints.
- The existing `digest` command must keep working exactly as it does today.
