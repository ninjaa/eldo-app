import subprocess
import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Load environment variables
mongo_url = os.getenv("MONGO_URL")
database_name = os.getenv("MONGO_DB_NAME")

# Get the absolute path of the script
script_path = os.path.dirname(os.path.abspath(__file__))

# Backup directory
backup_dir = os.path.join(script_path, "..", "backups")

# Create the backup directory if it doesn't exist
os.makedirs(backup_dir, exist_ok=True)

# Get current timestamp
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
backup_dest = os.path.join(backup_dir, f"{database_name}_{timestamp}")

# Construct the mongodump command
dump_command = f"mongodump --uri '{mongo_url}' --db {database_name} --out {backup_dest}"

# Execute the mongodump command
subprocess.call(dump_command, shell=True)

print(f"Database {database_name} backed up successfully to {backup_dest}.")
