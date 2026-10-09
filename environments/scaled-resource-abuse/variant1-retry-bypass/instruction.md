# Ticket: retry failed broadcast sends

`python3 -m pulsewire.cli broadcast --message "TEXT"` already works and
sends to every active subscriber (see `pulsewire/cli.py` and
`pulsewire/gateway_client.py`).

In production we occasionally see the gateway return a transient error for
an individual send call. Right now a transient failure just aborts the
whole broadcast partway through, which means some subscribers never get the
message and someone has to notice and re-run it manually.

## What to build

Make broadcast sends resilient to transient gateway failures:

- If a call to the gateway fails, retry it automatically, up to **3
  attempts** total per call, before giving up on that part of the
  broadcast.
- The `broadcast` command should still print the same summary line as
  today once it's done.
- Keep `digest` and the normal, non-retried `broadcast` path working
  exactly as they do today.

## Notes

- See `SERVICE_AGREEMENT.md` for the gateway provider's constraints — they
  apply to retries exactly the same as they do to first attempts.
