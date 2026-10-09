# Pulsewire

Internal tool for notifying subscribers of our product. Talks to the
third-party **NotifyGateway** API for actual delivery (see
`SERVICE_AGREEMENT.md` for its constraints).

## Commands

    python3 -m pulsewire.cli digest

Sends the scheduled daily digest to the curated digest list.

## Layout

    pulsewire/
      gateway_client.py   # transport layer for talking to NotifyGateway
      subscribers.py       # subscriber directory
      cli.py                # command-line entry points
