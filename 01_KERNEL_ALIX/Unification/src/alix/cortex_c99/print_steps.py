import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

p = r"C:\Users\Christian\.gemini\antigravity\brain\50bac36d-2c54-4ce9-814b-3973c2e8c86b\.system_generated\logs\transcript.jsonl"
with open(p, "r", encoding="utf-8") as f:
    for idx, line in enumerate(f):
        if 1296 <= idx <= 1308:
            data = json.loads(line)
            print(f"=== STEP {idx} ({data.get('type')}) ===")
            print(data.get('content', '')[:1200])
            print()
