"""Debug launcher to capture all console output."""
import sys
import subprocess

# Run the app and capture output
result = subprocess.run(
    [sys.executable, "-m", "app"],
    capture_output=True,
    text=True,
    cwd=r"C:\Users\LEGION\Documents\PROJECT_SAGEFRAME\sageframe_desktop"
)

# Write to file
with open("debug_output.txt", "w", encoding="utf-8") as f:
    f.write("=== STDOUT ===\n")
    f.write(result.stdout)
    f.write("\n\n=== STDERR ===\n")
    f.write(result.stderr)

print("Output written to debug_output.txt")
print("\n=== Last 30 lines ===")
all_lines = (result.stdout + "\n" + result.stderr).split("\n")
for line in all_lines[-30:]:
    print(line)
