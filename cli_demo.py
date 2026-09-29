"""Scripted 'learning over time' demo on a fresh, empty memory bank.   python run.py demo"""
import os, tempfile, time
import laksh_ops  # loads .env
os.environ["HINDSIGHT_BANK"] = f"laksh-demo-{int(time.time())}"      # fresh bank => starts cold
os.environ["LAKSH_LOCAL_STORE"] = os.path.join(tempfile.mkdtemp(), "demo.json")
from laksh_ops.memory import make_memory
from laksh_ops.brain import OpsBrain
from laksh_ops.render import format_result

mem = make_memory()
brain = OpsBrain(mem)
ALERT = "payments-api p99 latency > 2s, DB connection errors after today's deploy"


def step(title, text):
    print(f"\n=== {title} ===\n> {text}")
    print(format_result(brain.handle(text, "Asha")))


print(f"Memory backend: {mem.name}")
step("WEEK 1 - first alert, empty memory", ALERT)
step("Engineer resolves it", "resolved payments-api pool exhaustion, restart the pods did not help, fixed by rolling back the deploy took 47 min")
step("WEEK 3 - similar alert (memory now used)", ALERT)
step("Engineer teaches a preference", "remember that I like exact kubectl commands")
step("Pattern insight (Hindsight reflect)", "what patterns keep recurring")
