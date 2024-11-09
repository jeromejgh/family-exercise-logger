import shutil
import os
import json
import sqlite3
import pandas as pd
from datetime import datetime
import zipfile

class ExerciseLogBackup:
    def __init__(self):
        self.db_path = 'data/exercise_log.db'
        self.backup_dir = 'backups'
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create backup directory if it doesn't exist
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

    def create_sqlite_backup(self):
        """Create a full SQLite database backup"""
        backup_path = f"{self.backup_dir}/exercise_log_{self.timestamp}.db"
        shutil.copy2(self.db_path, backup_path)
        return backup_path

    def create_csv_backup(self):
        """Export all tables to CSV files"""
        conn = sqlite3.connect(self.db_path)
        
        # Get all table names
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        # Create a directory for this backup
        csv_dir = f"{self.backup_dir}/csv_backup_{self.timestamp}"
        os.makedirs(csv_dir)
        
        # Export each table to CSV
        csv_files = []
        for table in tables:
            table_name = table[0]
            csv_path = f"{csv_dir}/{table_name}.csv"
            
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            df.to_csv(csv_path, index=False)
            csv_files.append(csv_path)
        
        conn.close()
        
        # Create zip file containing all CSVs
        zip_path = f"{self.backup_dir}/exercise_log_{self.timestamp}_csv.zip"
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for csv_file in csv_files:
                zipf.write(csv_file, os.path.basename(csv_file))
        
        # Clean up individual CSV files
        shutil.rmtree(csv_dir)
        
        return zip_path

    def create_json_backup(self):
        """Export all data to a structured JSON file"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        # Create JSON structure
        backup_data = {
            'backup_date': self.timestamp,
            'tables': {}
        }
        
        # Export each table to JSON
        for table in tables:
            table_name = table[0]
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            
            # Convert DataFrame to JSON structure
            backup_data['tables'][table_name] = df.to_dict(orient='records')
        
        conn.close()
        
        # Save JSON file
        json_path = f"{self.backup_dir}/exercise_log_{self.timestamp}.json"
        with open(json_path, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        return json_path

    def create_full_backup(self):
        """Create backups in all formats and return their paths"""
        backup_paths = {
            'sqlite': self.create_sqlite_backup(),
            'csv': self.create_csv_backup(),
            'json': self.create_json_backup()
        }
        return backup_paths