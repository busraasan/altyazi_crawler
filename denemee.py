import re

text = "{\1c&00FFFF&}{\3c&000000&}{\4c&000000&}Hey, �u ku�un gagas�na bak..."
print(text.replace("{\1c&00FFFF&}", "").replace("{\4c&000000&}","").replace("{\3c&000000&}", ""))