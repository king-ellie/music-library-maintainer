import os

def remove_numbers_from_file_name(directory):
    for root, _, files in os.walk(directory):
        for original_file_name in files:
            if not original_file_name.endswith(".mp3"):
                continue

            parts_of_file_name = original_file_name.split(" - ", 1)
            if len(parts_of_file_name) != 2:
                print(f"Skipping: {original_file_name}, could not split into parts")
                continue
            if not parts_of_file_name[0].strip().isdigit():
                print(f"Skipping: {original_file_name}, first section of song is not number")
                continue

            file_name_without_number = parts_of_file_name[1]

            old_path = os.path.join(root, original_file_name)
            new_path = os.path.join(root, file_name_without_number)

            try:
                os.rename(old_path, new_path)
                print(f"Renamed: {original_file_name} -> {file_name_without_number}")
            except Exception as e:
                print(f"Error renaming {original_file_name}: {e}")

DIRECTORY_PATH = "/Users/ellie/Music/Tracks To Download"

if __name__ == "__main__":
    remove_numbers_from_file_name(DIRECTORY_PATH)