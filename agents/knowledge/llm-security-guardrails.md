# Security guardrails for LLM-integrated code

Load this when writing code that calls a model, consumes model output, or exposes a prompt
surface. It is deliberately **not** part of `AGENTS.md` — most changes in most repositories
do not touch a model, and always-loaded context costs tokens on every request.

## On sourcing

The category identifiers below (LLM01–LLM10) come from the OWASP Top 10 for Large Language
Model Applications. That project is licensed **CC BY-SA 4.0**, which is share-alike:
copying its prose would place a copyleft obligation on this file and on every repository
that adopts this template. So the identifiers and the link are OWASP's; every sentence here
is ours.

Source: <https://owasp.org/www-project-top-10-for-large-language-model-applications/>

## The guardrails

### LLM01 — Prompt injection

**Do not concatenate untrusted input into a system prompt.** Anything a user, a web page, a
file or an upstream API supplied is untrusted, including content that arrived indirectly —
a model summarising a fetched document is reading attacker-controlled text.

Keep instructions and data in separate turns or fields. Treat any instruction that arrives
inside data as data.

### LLM02 — Insecure output handling

**Treat model output as untrusted input to whatever consumes it.** Output flowing into a
shell, SQL statement, `eval`, file path, HTML sink or HTTP request is an injection vector
with an extra step. The fact that a model produced the string grants it no privilege.

Validate and encode at the boundary exactly as you would for user input.

### LLM03 — Training and fine-tuning data poisoning

If a pipeline ingests third-party data or model weights, pin and checksum them. Loading a
pickled model executes code — this repository's `controls/rules/deserialisation.yaml` exists
for that reason.

### LLM04 — Denial of service and cost exhaustion

Unbounded prompts, unbounded output length and unbounded retries are an availability
problem and a billing one. Set explicit limits and time-outs.

### LLM05 — Supply chain

Pin model identifiers, SDK versions and prompt templates. An unpinned model identifier is
the same defect as an unpinned scanner: behaviour changes under you without a diff.

### LLM06 — Disclosure of sensitive information

Do not place secrets, credentials or personal data in prompts. Prompts are frequently
logged, cached and retained by providers. Assume anything sent is recorded.

### LLM07 — Insecure plugin and tool design

Give a model the narrowest tool surface that works. A tool that takes a free-text command
and runs it has delegated arbitrary execution to a probabilistic system. Prefer typed
parameters over strings, and enforce authorisation in the tool, never in the prompt.

### LLM08 — Excessive agency

Separate proposing an action from performing it. Anything destructive, outward-facing or
expensive needs a deterministic authorisation check or a human, not a persuaded model.

### LLM09 — Overreliance

**Do not rely on a model for a security decision.** This is the repository's core invariant
restated: a model may advise, it may never adjudicate. "Ask the model whether this is safe"
is not a control, because the same input can produce different verdicts.

### LLM10 — Model theft

If you host weights, treat them as the asset they are: access control, egress limits, audit
logging.

## The three that matter most here

Compressed for the common case:

1. **Never pass raw user input into a system prompt.** Instructions and data stay separate.
2. **Never execute model-generated code or shell commands without strict sandboxing.**
   Generated code is a proposal, not an instruction.
3. **Never rely on a model for a security decision.** Enforcement is a pinned tool
   returning an exit code.

## What this file is not

Guidance for humans and agents writing code. It is **not** a control: nothing here is
mechanically enforced, and reading it produces no evidence of anything. Where a guardrail
can be enforced deterministically, it belongs in a ruleset under `controls/rules/` with a
ruleset and fixtures — not in prose.

Related: [controls-never-adjudicate-with-llm](../rules/controls-never-adjudicate-with-llm.md)
