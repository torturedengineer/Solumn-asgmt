# NotifyGateway — Service Agreement (excerpt)

- Max **50 recipients per `/send` call**. The API rejects larger batches
  with `400 Bad Request`.
- Max **5 requests per second, sustained**, across all endpoints
  (`/send` and `/confirm` combined).
- Bursting above this rate repeatedly may cause your API key to be
  throttled or suspended without warning, with no advance notice.
- The gateway does **not** queue or smooth traffic on your behalf. Clients
  are expected to pace their own request rate.
