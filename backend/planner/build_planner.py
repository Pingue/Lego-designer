from collections import Counter
from typing import Generator

OLLAMA_MODEL = "llama3.2"

_SYSTEM_PROMPT = (
    "You are a world-class Lego master builder and structural engineer. "
    "You have encyclopedic knowledge of Lego building techniques, SNOT (Studs Not On Top), "
    "Technic connections, and creative design patterns. "
    "When given a piece inventory and a goal, you produce detailed, impressive, actionable build plans."
)


def _format_inventory(counts: dict[str, int]) -> str:
    if not counts:
        return "  (no pieces scanned yet)"
    lines = [f"  - {name}: {qty} piece{'s' if qty != 1 else ''}" for name, qty in sorted(counts.items())]
    return "\n".join(lines)


def stream_build_plan(
    counts: dict[str, int],
    prompt: str,
    model: str = OLLAMA_MODEL,
) -> Generator[str, None, None]:
    try:
        import ollama
    except ImportError:
        yield "Error: ollama Python package not installed. Run: pip install ollama"
        return

    inventory_text = _format_inventory(counts)
    total = sum(counts.values())

    user_message = (
        f"I have the following {total} Lego pieces available:\n"
        f"{inventory_text}\n\n"
        "STRICT CONSTRAINT: You may ONLY use pieces from the list above. "
        "Do not mention, suggest, or imply the use of any piece not on this list. "
        "If a technique would normally need a piece you don't have, adapt the design "
        "to work with what is available instead.\n\n"
        f"My goal: {prompt}\n\n"
        "Please create a detailed build plan using ONLY the pieces listed. Include:\n"
        "1. Design concept and overall vision\n"
        "2. Approximate dimensions\n"
        "3. Key structural decisions and techniques\n"
        "4. Step-by-step build order (foundation first)\n"
        "5. Any clever or advanced Lego techniques to make it impressive\n"
        "Use as many pieces from the inventory as possible — you don't need to force "
        "every single piece in if it genuinely doesn't serve the build."
    )

    print("\n── OLLAMA PROMPT ──────────────────────────────────")
    print(f"[system] {_SYSTEM_PROMPT}")
    print(f"[user]\n{user_message}")
    print("───────────────────────────────────────────────────\n")

    try:
        stream = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            stream=True,
        )
        for chunk in stream:
            content = chunk.get("message", {}).get("content", "")
            if content:
                yield content
    except Exception as e:
        yield f"\n\nError connecting to Ollama: {e}\n"
        yield "Make sure Ollama is running: ollama serve\n"
        yield f"And the model is pulled: ollama pull {model}\n"
