import json
import os
import sys

def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tag = sys.argv[1] if len(sys.argv) > 1 else "latest"
    version_file = os.path.join(root, "version.json")
    out_file = os.path.join(root, "release_body.txt")

    lines = []
    if os.path.isfile(version_file):
        try:
            with open(version_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            cl = data.get("changelog", [])
            if isinstance(cl, list):
                for item in cl:
                    item_str = str(item).strip()
                    if not item_str.startswith("•"):
                        item_str = f"• {item_str}"
                    lines.append(item_str)
            elif cl:
                for item in str(cl).strip().splitlines():
                    item_str = item.strip()
                    if item_str and not item_str.startswith("•"):
                        item_str = f"• {item_str}"
                    if item_str:
                        lines.append(item_str)
        except Exception as e:
            print("Error reading version.json:", e)

    if not lines:
        lines = [f"• อัปเดต CookieRun Bot เวอร์ชัน {tag}", "• ปรับปรุงประสิทธิภาพและความเสถียรของระบบ"]

    output_text = "\n".join(lines)
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(output_text)

    print("=== Generated release_body.txt ===")

if __name__ == "__main__":
    main()
