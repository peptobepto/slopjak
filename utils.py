# File: utils.py
import os
import shutil


def delete_files_in_folders(base_dir="."):
    """Delete files in intermediate folders (old function, kept for compatibility)."""
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


def cleanup_intermediate_files(base_dir=".", keep_originals=True, keep_final_output=True):
    """Clean up all intermediate files and folders, optionally keeping original video files.
    
    Args:
        base_dir: Base directory to clean (default: current directory)
        keep_originals: If True, keep podcast.mp4 and fart.mp4 (default: True)
        keep_final_output: If True, keep final_with_subs folder (default: True)
    """
    print("\n=== Cleaning up intermediate files ===")
    
    # Files to delete
    files_to_delete = [
        "full_podcast.srt",
        "clip_ratings.json",
    ]
    
    # Folders to delete entirely
    folders_to_delete = [
        "subtitles",
        "podcast_output",
        "gameplay",
        "combined",
    ]
    
    # Optionally delete final output folder
    if not keep_final_output:
        folders_to_delete.append("final_with_subs")
    
    deleted_count = 0
    failed_count = 0
    
    # Delete individual files
    for filename in files_to_delete:
        file_path = os.path.join(base_dir, filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"✓ Deleted: {filename}")
                deleted_count += 1
            except Exception as e:
                print(f"✗ Failed to delete {filename}: {e}")
                failed_count += 1
    
    # Delete folders
    for folder_name in folders_to_delete:
        folder_path = os.path.join(base_dir, folder_name)
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            try:
                shutil.rmtree(folder_path)
                print(f"✓ Deleted folder: {folder_name}/")
                deleted_count += 1
            except Exception as e:
                print(f"✗ Failed to delete folder {folder_name}/: {e}")
                failed_count += 1
    
    # Optionally delete original video files
    if not keep_originals:
        original_files = ["podcast.mp4", "fart.mp4"]
        for filename in original_files:
            file_path = os.path.join(base_dir, filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"✓ Deleted original: {filename}")
                    deleted_count += 1
                except Exception as e:
                    print(f"✗ Failed to delete {filename}: {e}")
                    failed_count += 1
    
    print(f"\nCleanup complete: {deleted_count} items deleted, {failed_count} failures")
    return deleted_count, failed_count

