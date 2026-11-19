import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

p = r"C:\Users\Christian\.gemini\antigravity\brain\50bac36d-2c54-4ce9-814b-3973c2e8c86b\.system_generated\logs\transcript.jsonl"
if os.path.exists(p):
    with open(p, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            data = json.loads(line)
            content = str(data.get("content", ""))
            thinking = str(data.get("thinking", ""))
            text = content + " " + thinking
            for term in ["ratio", "1 sur 3", "brise", "calisser", "sonder"]:
                if term in text.lower():
                    print(f"Line {idx} [{data.get('type')}]: {content[:300]}\n")
                    break
