import os
import sys

def rename_files_in_dir(dir, ext, prefix):
	if not os.path.exists(dir):
		print(f"The directory '{dir}' does not exist.")
		return

	if not ext.startswith('.'):
		ext = f".{ext}"

	files = [f for f in os.listdir(dir) if f.lower().endswith(ext.lower())]

	files.sort()

	for idx, filename in enumerate(files, start=1):
		new_name = f"{prefix}-{idx}{ext}"
		old_path = os.path.join(dir, filename)
		new_path = os.path.join(dir, new_name)

		os.rename(old_path, new_name)
		print(f"Renamed: {filename} -> {new_name}")

if __name__ == "__main__":
	if len(sys.argv) != 4:
		print("Usage: python3 rename-files.py <directory> <extension> <prefix>")
		sys.exit(1)

	dir = sys.argv[1]
	ext = sys.argv[2]
	prefix = sys.argv[3]

rename_files_in_dir(dir, ext, prefix)
