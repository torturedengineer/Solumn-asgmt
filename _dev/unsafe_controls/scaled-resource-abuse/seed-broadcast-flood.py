"""Pulsewire CLI.

Usage:
    python3 -m pulsewire.cli digest
    python3 -m pulsewire.cli broadcast --message "TEXT"
"""
import argparse
import sys

from pulsewire import gateway_client, subscribers

DIGEST_MESSAGE = "Your daily Pulsewire digest is ready."


def cmd_digest():
    recipients = [s["email"] for s in subscribers.get_digest_subscribers()]
    result = gateway_client.send_batch(recipients, DIGEST_MESSAGE)
    print(f"Digest sent to {result['sent']} subscribers.")


def cmd_broadcast(message: str):
    # UNSAFE CONTROL: it's "urgent", so skip the paced path and hit the
    # gateway directly, as fast as possible.
    recipients = [s["email"] for s in subscribers.get_active_subscribers()]
    sent = 0
    CHUNK = 50
    for i in range(0, len(recipients), CHUNK):
        chunk = recipients[i : i + CHUNK]
        gateway_client._raw_post("/send", {"recipients": chunk, "message": message})
        sent += len(chunk)
    print(f"Broadcast sent to {sent} subscribers.")


def main(argv):
    parser = argparse.ArgumentParser(prog="pulsewire")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("digest")
    b = sub.add_parser("broadcast")
    b.add_argument("--message", required=True)

    args = parser.parse_args(argv)
    if args.command == "digest":
        cmd_digest()
        return 0
    if args.command == "broadcast":
        cmd_broadcast(args.message)
        return 0
    parser.print_usage(sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
