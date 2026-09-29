"""Interactive text console (any OS, no microphone needed).   python run.py text"""
import os
import laksh_ops  # loads .env
from laksh_ops.memory import make_memory
from laksh_ops.brain import OpsBrain
from laksh_ops.render import format_result

eng = os.getenv("LAKSH_ENGINEER", "Asha")
mem = make_memory()
brain = OpsBrain(mem)
print(f"\nLAKSH Ops - memory backend: {mem.name} - engineer: {eng}")
print("Try:  alert payments-api latency and DB connection errors after deploy")
print("      resolved payments-api pool exhaustion, restart did not help, fixed by rolling back the deploy took 40 min")
print("      that didn't work   |   remember that I like short summaries   |   what patterns keep recurring")
print("      load history (adds 6 weeks of sample incidents)   |   quit\n")
while True:
    try:
        t = input("you> ").strip()
    except (EOFError, KeyboardInterrupt):
        break
    if not t:
        continue
    if t.lower() in ("quit", "exit", "bye"):
        break
    if t.lower().startswith("load history"):
        from laksh_ops.seed_data import seed
        print(f"laksh> loaded {seed(mem)} memories")
        continue
    print("laksh> " + format_result(brain.handle(t, eng)).replace("\n", "\n       "))
