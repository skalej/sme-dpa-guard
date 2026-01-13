# LLM Safety and Guardrails

## JSON-only outputs
- LLM output must be valid JSON (no markdown).
- Code strips ``` fences and validates required keys.

## Strict validation
- `risk_label` must be one of GREEN, YELLOW, RED.
- `candidate_quotes` must be list[str].
- `triggered_rule_ids` must be list[str].

## Safe fallbacks
- Evaluation failures return YELLOW with a manual-review message.
- Classification LLM failures fall back to rules-only results.

## Evidence validation
- Quotes are accepted only if they appear verbatim in stored segment text.

## Retry policy
- Bounded retries for transient OpenAI errors.
- Max retries: 2 with exponential backoff + jitter.
