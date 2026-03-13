import os
import re
import sys

def main():
    with os.popen("flake8 app --max-line-length=120 --exclude=__pycache__") as f:
        lines = f.readlines()

    for line in lines:
        parts = line.strip().split(":")
        if len(parts) >= 4:
            file_path = parts[0]
            line_num = int(parts[1]) - 1
            error_code = parts[3].strip().split(" ")[0]

            with open(file_path, "r") as src:
                content = src.readlines()

            if "E722" in error_code:
                content[line_num] = content[line_num].replace("except:", "except Exception:")
            elif "F401" in error_code:
                # Naive fix: just comment out the line or delete it if it's unused imports
                # Better to just use autoflake for F401
                pass
            elif "F811" in error_code:
                pass
            elif "E712" in error_code:
                content[line_num] = content[line_num].replace("== True", "is True").replace("== False", "is False")
            elif "F541" in error_code:
                content[line_num] = content[line_num].replace("f\"", "\"").replace("f'", "'")

            with open(file_path, "w") as dst:
                dst.writelines(content)

if __name__ == "__main__":
    main()
