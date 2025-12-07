# File: utils.py
import os
import shutil


def delete_files_in_folders(base_dir="."):
    folders = ["subtitles", "podcast_output", "gameplay", "combined"]
    for folder in folders:
        folder_path = os.path.join(base_dir, folder)
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                    print(f"Deleted: {file_path}")
                except Exception as e:
                    print(f"Failed to delete {file_path}. Reason: {e}")
        else:
            print(f"Folder not found: {folder_path}")

