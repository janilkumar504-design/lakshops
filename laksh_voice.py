"""Windows voice mode: your original Laksh + Hindsight incident memory.   python run.py voice
Ops phrases (alert / resolved / that didn't work / remember / patterns) -> OpsBrain + Hindsight.
Everything else -> Laksh's original PC control. PC actions taken during an incident are
attached to that incident's timeline when you say "resolved"."""
import os, sys
import laksh_ops  # loads .env
from laksh_ops.memory import make_memory
from laksh_ops.brain import OpsBrain
from laksh_ops.llm import complete

try:
    import laksh                       # your original file, unchanged
except Exception as e:
    sys.exit(f"Could not load laksh.py ({type(e).__name__}: {e}).\n"
             "Voice mode needs Windows + the Laksh packages:  python run.py setup\n"
             "No microphone/Windows?  Use the text console:  python run.py text")

ENGINEER = os.getenv("LAKSH_ENGINEER", "Asha")
laksh.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or laksh.GEMINI_API_KEY
_orig_ask = laksh.AIBrain.ask


def _ask(self, q):  # original used the retired 'gemini-pro' model; use the configured one first
    return complete(q, system="You are LAKSH, a friendly AI voice assistant. Answer in 1-2 short sentences, no bullets.") or _orig_ask(self, q)


laksh.AIBrain.ask = _ask


class OpsProcessor(laksh.CommandProcessor):
    def __init__(self, pc, brain):
        super().__init__(pc)
        self.brain = brain

    def process(self, cmd):
        r = self.brain.handle_ops(cmd, ENGINEER)
        if r:
            print("\n  LAKSH:", r["reply"])
            return r["reply"]
        out = super().process(cmd)
        self.brain.note_action(ENGINEER, cmd)
        return out


class OpsLaksh(laksh.LakshAssistant):
    def __init__(self):
        laksh.is_startup_installed = lambda: True   # don't auto-register the plain, memory-less script
        super().__init__()
        mem = make_memory()
        print(f"  [Memory backend: {mem.name}]  [Engineer: {ENGINEER}]\n")
        self.processor = OpsProcessor(self.pc, OpsBrain(mem))


if __name__ == "__main__":
    if "--install-startup" in sys.argv:
        laksh.__file__ = os.path.abspath(__file__)   # register THIS script (with memory) at boot
        laksh.install_startup(); sys.exit()
    if "--remove-startup" in sys.argv:
        laksh.remove_startup(); sys.exit()
    try:
        import pyaudio  # noqa: F401
    except ImportError:
        sys.exit("PyAudio (microphone support) is not installed. Use Python 3.11 and run:  python run.py setup\n"
                 "Meanwhile the text console works without it:  python run.py text")
    OpsLaksh().start()
