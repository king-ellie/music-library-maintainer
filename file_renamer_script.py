import os

def remove_numbers_from_file_name(directory):
    for root, _, files in os.walk(directory):
        for original_filename in files:
            if not original_filename.endswith(".mp3"):
                continue

            parts_of_filename = original_filename.split(" - ", 1)
            if len(parts_of_filename) != 2:
                print(f"Skipping: {original_filename}, could not split into parts")
                continue
            if not parts_of_filename[0].strip().isdigit():
                print(f"Skipping: {original_filename}, first section of song is not number")
                continue

            file_name_without_number = parts_of_filename[1]

            old_path = os.path.join(root, original_filename)
            new_path = os.path.join(root, file_name_without_number)

            try:
                os.rename(old_path, new_path)
                print(f"Renamed: {original_filename} -> {file_name_without_number}")
            except Exception as e:
                print(f"Error renaming {original_filename}: {e}")

DIRECTORY_PATH = "/Users/ellie/Music/Tracks To Download"

if __name__ == "__main__":
    remove_numbers_from_file_name(DIRECTORY_PATH)