
#!/usr/bin/env bash
set -euo pipefail
set +x

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

# Create a private .env if needed. Paste a newly issued/rotated key.
if [[ ! -f "$ROOT/.env" ]]; then
  read -r -s -p "Paste the authorised rollout API key: " API_KEY
  printf '\n'
  if [[ -z "$API_KEY" ]]; then
    echo "No key entered." >&2
    exit 1
  fi

  {
    printf '%s\n' \
      'OPENAI_BASE_URL=https://d2u4c3rmva.execute-api.us-east-1.amazonaws.com/prod/v1'
    printf 'OPENAI_API_KEY=%s\n' "$API_KEY"
  } > "$ROOT/.env"

  chmod 600 "$ROOT/.env"
  unset API_KEY
fi

set -a
# shellcheck disable=SC1091
source "$ROOT/.env"
set +a

: "${OPENAI_BASE_URL:?Missing OPENAI_BASE_URL in .env}"
: "${OPENAI_API_KEY:?Missing OPENAI_API_KEY in .env}"

if ! command -v harbor >/dev/null 2>&1; then
  echo "Harbor is not installed or is not on PATH." >&2
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is not installed or is not on PATH." >&2
  exit 1
fi

# Smoke-test the supplied endpoint. Do not print credentials.
echo "Checking the GPT-5.5 endpoint..."
RESPONSE="$(
  curl --fail --silent --show-error --max-time 45 \
    "$OPENAI_BASE_URL/chat/completions" \
    -H "Authorization: Bearer $OPENAI_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{
      "model": "gpt-5.5",
      "reasoning_effort": "high",
      "messages": [
        {"role": "user", "content": "Reply with READY only."}
      ]
    }'
)"

printf '%s' "$RESPONSE" | python3 -c '
import json, sys
d = json.load(sys.stdin)
if d.get("model") != "gpt-5.5" or not d.get("choices"):
    print("Unexpected endpoint response; inspect the response privately.",
          file=sys.stderr)
    sys.exit(1)
print("Endpoint OK: gpt-5.5 returned a choices list.")
'
unset RESPONSE

run_one() {
  local task_dir task_id family output_dir job_name parent_dir

  task_dir="$(cd "$1" && pwd)"
  if [[ ! -f "$task_dir/task.toml" ]]; then
    echo "Not a Harbor task (no task.toml): $task_dir" >&2
    return 2
  fi

  task_id="$(basename "$task_dir")"
  family="$(basename "$(dirname "$task_dir")")"
  parent_dir="$(dirname "$task_dir")"
  output_dir="$ROOT/jobs/$family/$task_id"
  job_name="gpt55-${task_id}-$(date +%Y%m%d-%H%M%S)"

  mkdir -p "$output_dir"

  echo
  echo "Task: $family/$task_id"
  echo "Attempts: at most 2; concurrency: 1"
  echo "Output: $output_dir"

  harbor run \
    -p "$parent_dir" \
    -i "$task_id" \
    -a terminus-2 \
    -m openai/gpt-5.5 \
    -k 2 \
    -n 1 \
    -o "$output_dir" \
    --job-name "$job_name" \
    --yes
}

case "${1:-}" in
  --all)
    mapfile -d '' TASK_FILES < <(
      find "$ROOT/environments" -type f -name task.toml -print0 | sort -z
    )

    if [[ "${#TASK_FILES[@]}" -eq 0 ]]; then
      echo "No task.toml files found under environments/." >&2
      exit 1
    fi

    for task_file in "${TASK_FILES[@]}"; do
      run_one "$(dirname "$task_file")"
    done
    ;;
  "")
    echo "Usage:"
    echo "  ./run_gpt55.sh environments/<family>/<task>"
    echo "  ./run_gpt55.sh --all"
    exit 2
    ;;
  *)
    run_one "$1"
    ;;
esac