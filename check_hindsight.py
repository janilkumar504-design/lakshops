"""Verifies your Hindsight connection and that tags + metadata round-trip.   python run.py check"""
import os, sys, time
import laksh_ops  # loads .env
from laksh_ops.memory import normalize_url, CLOUD_API

try:
    from hindsight_client import Hindsight
except ImportError:
    sys.exit("hindsight-client is not installed. Run:  python run.py setup")

url = normalize_url(os.getenv("HINDSIGHT_URL")) or CLOUD_API
key = os.getenv("HINDSIGHT_API_KEY") or None
bank = f"laksh-check-{int(time.time())}"
print(f"URL: {url}\nAPI key set: {bool(key)}\nBank: {bank}\n")
c = Hindsight(base_url=url, api_key=key)
try:
    c.create_bank(bank_id=bank, name="LAKSH connectivity check")
    print("1. create_bank ........ OK")
    c.retain(bank_id=bank, content="On payments-api (pool-exhaustion), 'Roll back the latest deploy' resolved the incident in 40 min.",
             tags=["kind:fix", "service:payments-api", "outcome:worked_fix"], metadata={"fix": "Roll back the latest deploy", "ttr": "40"})
    print("2. retain ............. OK")
    r = c.recall(bank_id=bank, query="payments-api connection errors", tags=["service:payments-api"], tags_match="any_strict")
    print(f"3. recall ............. OK ({len(r.results)} result(s))")
    for x in r.results[:3]:
        print(f"     text: {x.text[:90]}\n     tags: {x.tags}\n     metadata: {x.metadata}")
    print("   tags round-trip:", "YES" if any(x.tags for x in r.results) else "NO  (planner falls back to parsing text)")
    print("   metadata round-trip:", "YES" if any(x.metadata for x in r.results) else "NO  (planner falls back to parsing text)")
    print("4. reflect ............ " + c.reflect(bank_id=bank, query="What fixed payments-api?").text[:160])
    print("\nAll good - Hindsight is working.")
except Exception as e:
    print(f"\nFAILED: {type(e).__name__}: {e}")
    print("Check: HINDSIGHT_URL must be https://api.hindsight.vectorize.io and HINDSIGHT_API_KEY must be a valid key (starts with hsk_).")
    sys.exit(1)
