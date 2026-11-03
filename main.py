import os
import sys

# Ensure src/ is on sys.path when running main.py directly
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from personalstt.cli import main

if __name__ == "__main__":
    main()

