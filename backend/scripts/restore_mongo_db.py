import subprocess
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Load environment variables
mongo_url = os.getenv("MONGO_URL")
database_name = os.getenv("MONGO_DB_NAME")

# Check if the database name is provided
if not database_name:
    print("Error: MONGO_DB_NAME environment variable is not set.")
    sys.exit(1)

# Check if the database name is 'aiacademy' as that is our PROD database
if database_name == 'aiacademy':
    # Check if the -f flag is passed
    if '-f' not in sys.argv:
        print("Error: Restoring the 'aiacademy' database requires the -f flag.")
        sys.exit(1)

# Get the absolute path of the script
script_path = os.path.dirname(os.path.abspath(__file__))

# Backup directory
backup_dir = os.path.join(script_path, "..", "backups")

# Check if a backup folder path is provided as an argument
if len(sys.argv) > 1:
    backup_folder = sys.argv[1]
    if not os.path.isabs(backup_folder):
        backup_folder = os.path.join(backup_dir, backup_folder)
else:
    # Find the latest backup folder
    backup_folders = sorted(os.listdir(backup_dir), reverse=True)
    if backup_folders:
        backup_folder = os.path.join(backup_dir, backup_folders[0])
        confirm = input(
            f"No backup folder specified. Restore the latest backup ({backup_folders[0]})? (y/n): ")
        if confirm.lower() != 'y':
            print("Restoration canceled.")
            sys.exit(0)
    else:
        print("No backup found.")
        sys.exit(1)

# Construct the mongorestore command with --drop option
restore_command = f"mongorestore --uri '{mongo_url}' --drop --dir {backup_folder}"

# Execute the mongorestore command
subprocess.call(restore_command, shell=True)

print(f"Database {database_name} restored successfully from {backup_folder}.")
