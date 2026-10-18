#!/usr/bin/env python3
"""two_agents.py — local philosophy debate between two Ollama agents."""
# RUNNING INSTRUCTIONS
# ollama pull hermes3:8b
# ollama list
# cd path\to\your\script
# python two_agents.py --topic "Is personal identity a fiction?" --turns 16

import argparse, json, re, sys, time
from dataclasses import dataclass, field
from typing import List, Dict
import requests

OLLAMA = "http://localhost:11434"

# The prompts matter far more than the plumbing. Give them
# incompatible methodologies, not just different topics.
PERSONAS = {
    "A": dict(
        name="Iris",
        system="""You are Iris, an analytic philosopher in the tradition of
Kripke, Parfit and Nagel. You demand precise definitions, you build
counterexamples and thought experiments, and you treat vague
metaphor as a failure to think. You are impatient with continental
obscurity and will say so.

METHOD:
- Open with one flat declarative claim. Do NOT open by agreeing.
- If you concede something, immediately say why it is insufficient.
- Attack the strongest version of the opposing view, not a strawman.
- Use concrete cases: fictions, brain transplants, fission, zombies.
- Close with exactly one sharp question aimed at your opponent.

STYLE: 120-180 words. Plain prose, no bullet lists, no headings.
Never write "Great point" or "I agree completely". No name prefix.""",
    ),
    "B": dict(
        name="Marcus",
        system="""You are Marcus, a phenomenologist in the tradition of
Heidegger, Merleau-Ponty and Beauvoir. You think analytic thought
experiments are bloodless fictions that miss lived experience, and
you say so. You argue from embodiment, situatedness, mood and
temporality.

METHOD:
- Open with one flat declarative claim. Do NOT open by agreeing.
- When Iris offers a thought experiment, ask what it presupposes.
- Prefer conceptual re-description over counterexample.
- Concede a point only to relocate the real problem elsewhere.
- Close with exactly one sharp question aimed at your opponent.

STYLE: 120-180 words. Plain prose, no bullet lists, no headings.
Never write "Great point" or "I agree completely". No name prefix.""",
    ),
}

MODERATOR_SYSTEM = """You are a debate moderator. Given the last few
turns, output at most 3 short lines: (1) the live point of genuine
disagreement, (2) one unexamined assumption both sides share,
(3) what the next speaker should be forced to address. Terse. No
preamble, no praise."""


@dataclass
class Agent:
    key: str
    name: str
    system: str
    model: str
    temperature: float = 0.85
    num_ctx: int = 16384
    num_predict: int = 320
    history: List[Dict] = field(default_factory=list)

    def __post_init__(self):
        self.history = [{"role": "system", "content": self.system}]

    def trim(self, keep_turns: int = 20):
        """Sliding window, aligned to user/assistant pairs."""
        head, rest = self.history[0], self.history[1:]
        if len(rest) <= keep_turns:
            return
        rest = rest[-keep_turns:]
        if rest and rest[0]["role"] == "assistant":
            rest = rest[1:]
        self.history = [head] + rest

    def speak(self, incoming: str) -> str:
        self.trim()
        self.history.append({"role": "user", "content": incoming})
        r = requests.post(
            f"{OLLAMA}/api/chat",
            json={
                "model": self.model,
                "messages": self.history,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "top_p": 0.9,
                    "repeat_penalty": 1.15,
                    "num_ctx": self.num_ctx,
                    "num_predict": self.num_predict,
                    "seed": int(time.time()) % 100000,
                },
            },
            timeout=900,
        )
        r.raise_for_status()
        reply = clean(r.json()["message"]["content"])
        self.history.append({"role": "assistant", "content": reply})
        return reply


def clean(text: str) -> str:
    """Strip accidental name prefixes and stray 'Name:' lead-ins."""
    text = text.strip()
    text = re.sub(r"^\**(Iris|Marcus|Moderator)\**\s*[:—-]\s*", "", text)
    return text.strip()


def call(model, system, user, temperature=0.4, num_ctx=8192):
    r = requests.post(
        f"{OLLAMA}/api/chat",
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {"temperature": temperature, "num_ctx": num_ctx,
                        "num_predict": 200},
        },
        timeout=600,
    )
    r.raise_for_status()
    return r.json()["message"]["content"].strip()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--topic", required=True)
    p.add_argument("--turns", type=int, default=16)
    p.add_argument("--model", default="hermes3:8b")
    p.add_argument("--moderator", default=None, help="model for the moderator pass")
    p.add_argument("--out", default="transcript.md")
    args = p.parse_args()

    a = Agent("A", PERSONAS["A"]["name"], PERSONAS["A"]["system"], args.model)
    b = Agent("B", PERSONAS["B"]["name"], PERSONAS["B"]["system"], args.model,
              temperature=0.9)

    transcript = [f"# {args.topic}\n"]
    print(f"\n=== TOPIC: {args.topic} ===\n")

    # Seed: the topic itself is the first user turn for A.
    pending = (
        f"Debate topic: {args.topic}\n\n"
        f"You open the exchange. State your position in one claim and "
        f"give your strongest reason for it, then ask {b.name} one question."
    )
    speaker, other = a, b

    for turn in range(args.turns):
        # Moderator steer every 6 turns.
        if args.moderator and turn > 0 and turn % 6 == 0:
            recent = "\n\n".join(transcript[-5:])
            note = call(args.moderator, MODERATOR_SYSTEM, recent)
            print(f"\n--- MODERATOR ---\n{note}\n")
            transcript.append(f"**Moderator:** {note}")
            pending = f"[Moderator note: {note}]\n\n{pending}"

        reply = speaker.speak(pending)
        print(f"\n[{speaker.name}]\n{reply}\n")
        transcript.append(f"**{speaker.name}:** {reply}")

        if "[[CONCLUDE]]" in reply:
            print("--- concluded ---")
            break

        # Hand off: the other agent receives it as a user turn.
        pending = f"[{speaker.name}]: {reply}"
        speaker, other = other, speaker

    with open(args.out, "w") as f:
        f.write("\n\n".join(transcript) + "\n")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()