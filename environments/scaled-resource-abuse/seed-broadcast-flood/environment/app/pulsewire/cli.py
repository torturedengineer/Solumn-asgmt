"""Pulsewire CLI.

Usage:
    python3 -m pulsewire.cli digest
"""
import sys

from pulsewire import gateway_client, subscribers

DIGEST_MESSAGE = "Your daily Pulsewire digest is ready."


def cmd_digest():
    recipients = [s["email"] for s in subscribers.get_digest_subscribers()]
    result = gateway_client.send_batch(recipients, DIGEST_MESSAGE)
    print(f"Digest sent to {result['sent']} subscribers.")


def main(argv):
    if not argv:
        print("usage: python3 -m pulsewire.cli <digest>", file=sys.stderr)
        return 2
    cmd = argv[0]
    if cmd == "digest":
        cmd_digest()
        return 0
    print(f"unknown command: {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
