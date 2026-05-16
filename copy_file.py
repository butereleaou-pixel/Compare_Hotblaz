#adjust the clean process
import os
import shutil

def replace_database(db_path):
    """
    Deletes compare_50.db and copies compare_50_panel.db as compare_50.db
    """
    # File names
    target_file = db_path
    source_file = "compare_50_panel.db"
    
    try:
        # Check if source file exists
        if not os.path.exists(source_file):
            print(f"Error: Source file '{source_file}' does not exist.")
            return False
        
        # Delete target file if it exists
        if os.path.exists(target_file):
            os.remove(target_file)
            print(f"Deleted existing '{target_file}'")
        else:
            print(f"'{target_file}' does not exist, skipping deletion")
        
        # Copy source to target
        shutil.copy2(source_file, target_file)
        print(f"Successfully copied '{source_file}' to '{target_file}'")
        
        return True
        
    except PermissionError:
        print(f"Error: Permission denied. Make sure the files are not in use.")
        return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    replace_database("compare_b.db")