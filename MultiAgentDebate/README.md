# Two-Agent Philosophy Debate (Ollama)

Two local LLM agents argue philosophy with each other until you tell them to stop.
Fully offline, no cloud calls, no agent framework — just two independent message
histories driven by one loop.

The point isn't the plumbing. It's the prompt design: the two agents get
*incompatible methodologies*, not just different opinions, so they generate real
friction instead of nodding at each other for thirty turns.

---

## What it does

- Spins up two named agents (`Iris`, an analytic philosopher; `Marcus`, a
  phenomenologist) with separate, private conversation histories
- Alternates turns between them on a topic you supply
- Optionally runs a low-temperature *moderator* pass every 6 turns that names the
  live disagreement and the assumption both agents share, then injects that as a
  steering note
- Writes a readable `transcript.md` at the end
- Runs entirely against your local Ollama server — nothing leaves the machine

---

## Requirements

| Thing | Notes |
|---|---|
| Python | 3.9 or newer |
| Ollama | Installed and running (the tray/desktop app is fine — you do **not** need `ollama serve`) |
| A model | Defaults to `hermes3:8b`. Any chat model works. |
| `requests` | The only non-stdlib dependency |

**Model sizing, roughly:** `hermes3:8b` at Q4 runs on a consumer GPU and is the
practical default. `hermes3:70b` gives noticeably better philosophical reasoning
if you have the VRAM. Hermes 4 (14B / 36B) is also a good pick.

---

## Install

```bash
pip install requests
ollama pull hermes3:8b
```

Confirm both are actually there before going further:

```bash
python -c "import requests; print('requests ok')"
ollama list
```

If `ollama list` doesn't show `hermes3:8b`, the pull didn't complete and the
script will fail on its first request.

---

## Quick start

```bash
cd path/to/script
python two_agents.py --topic "Is personal identity a fiction?" --turns 16
```

The debate streams to your terminal and lands in `transcript.md` in the current
directory when it finishes or hits the turn limit.

Add the moderator once you've watched a raw run:

```bash
python two_agents.py --topic "Is personal identity a fiction?" --turns 20 \
  --moderator hermes3:8b
```

---

## Usage

```
python two_agents.py --topic "..." [options]
```

| Flag | Default | What it does |
|---|---|---|
| `--topic` | *required* | The question they argue about. Be specific — see below. |
| `--turns` | `16` | Maximum exchange count, then stop. |
| `--model` | `hermes3:8b` | Model for both agents. |
| `--moderator` | *off* | Model for the steering pass. Point it at a cheap model. |
| `--out` | `transcript.md` | Output path, relative to your current directory. |

### Pick a specific topic

A broad subject makes them restate the question forever. A sharp one gives them
something to actually collide over.

- Weak: `--topic "consciousness"`
- Strong: `--topic "Does the Mary's Room thought experiment prove qualia are non-physical?"`

You can also paste a real passage into the topic and tell them to argue about it.
This is the local equivalent of RAG and it noticeably raises the philosophical
density — otherwise the models riff on vibes.

### Stopping early

If an agent emits the literal token `[[CONCLUDE]]` anywhere in its reply, the
loop halts immediately. Mention it in the persona prompts if you want the agents
to decide when they're done.

---

## Customising the agents

The personas live in the `PERSONAS` dict at the top of the file. This is where
the real work is — the loop is the easy 20%.

What makes a persona work:

1. **Give them incompatible methods, not just different conclusions.** Iris does
   counterexamples; Marcus attacks presuppositions. They can't resolve that by
   trading facts, so the debate survives many turns.
2. **Ban agreement openers.** Left alone, both models start every turn with "You
   make a compelling point" and the whole thing collapses into mutual
   affirmation. Explicitly forbidding the phrase is the highest-leverage fix.
3. **Cap length and force a closing question.** 120–180 words with one mandatory
   question per turn keeps the loop tight and guarantees the other agent has
   something to bite on.
4. **Tell them to steelman, not strawman.** Otherwise they argue past each other.

Useful axes to split on: analytic vs. continental, compatibilist vs. hard
determinist, realist vs. anti-realist, utilitarian vs. virtue ethicist, ancient
vs. modern.

---

## Tuning

Parameters live in the `Agent` dataclass and in the `options` block of
`Agent.speak()`. The ones that matter:

| Parameter | Default | Effect |
|---|---|---|
| `temperature` | `0.85` / `0.9` | Higher = more divergent. Keep the two agents slightly asymmetric so they don't converge on identical phrasing. |
| `repeat_penalty` | `1.15` | Raise to 1.2 if they start repeating sentences. |
| `num_ctx` | `16384` | Context window per request. **Raise this if they forget the early turns.** Ollama's default is far lower than you'd expect and will silently truncate. |
| `num_predict` | `320` | Hard cap on reply length in tokens. |
| `seed` | time-based | Reseeded every call. Fix it if you want reproducible runs. |

Set explicitly in the request rather than relying on env vars — a per-request
`num_ctx` overrides the server default, which sidesteps a