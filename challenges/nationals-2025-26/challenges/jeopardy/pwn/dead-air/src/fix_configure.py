#!/usr/bin/env python3
import re
import sys

path = sys.argv[1] if len(sys.argv) > 1 else 'configure'

with open(path) as f:
    text = f.read()

before = text.count('case "(($ac_try" in')
print(f"[fix_configure] Found {before} problematic case blocks")

pattern = r'case "\(\(\$ac_try" in\n  \*\\".*?\n  \*\) ac_try_echo=\$ac_try;;\nesac'
replacement = 'ac_try_echo=$ac_try'

text = re.sub(pattern, replacement, text)

after = text.count('case "(($ac_try" in')
print(f"[fix_configure] After fix: {after} remaining (replaced {before - after})")

if after > 0:
    print("[fix_configure] Trying alternate patterns...")
    text = re.sub(
        r'case "\(\(\$ac_try" in\n.*?\nesac',
        replacement, text, flags=re.DOTALL
    )
    after2 = text.count('case "(($ac_try" in')
    print(f"[fix_configure] After alternate fix: {after2} remaining")

with open(path, 'w') as f:
    f.write(text)

with open(path) as f:
    text = f.read()
werrors = text.count('-Werror')
text = text.replace('-Werror', '')
with open(path, 'w') as f:
    f.write(text)
print(f"[fix_configure] Removed {werrors} -Werror occurrences")
