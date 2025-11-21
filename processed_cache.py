import sqlite3
from pathlib import Path
from typing import Dict, Set, Optional
from datetime import datetime
import hashlib

from config import Config


class ProcessedCache:
    """Manages cache of processed PDF files using SQLite database"""
    
    def __init__(self, db_file: str = None):
        """
        Initialize cache manager with SQLite
        
        Args:
            db_file: Path to SQLite database file (default: from Config.CACHE_DB_FILE)
        """
        if db_file is None:
            db_file = Config.CACHE_DB_FILE
        self.db_file = Path(db_file)
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database and create table if not exists"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Create table with index on file_hash for fast lookup
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processed_files (
                file_hash TEXT PRIMARY KEY,
                file_path TEXT NOT NULL,
                file_name TEXT NOT NULL,
                processed_at TEXT NOT NULL,
                status TEXT,
                comparison TEXT,
                filename_gcn TEXT,
                predicted_gcn TEXT,
                error TEXT
            )
        """)
        
        # Create index on file_name for quick filename lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_file_name 
            ON processed_files(file_name)
        """)
        
        conn.commit()
        conn.close()
    
    def _get_file_hash(self, file_path: Path) -> str:
        """
        Get unique hash for a file based on path and size
        
        Args:
            file_path: Path to file
            
        Returns:
            File hash string
        """
        try:
            # Use absolute path and file size for hash
            file_info = f"{file_path.absolute()}_{file_path.stat().st_size}"
            return hashlib.md5(file_info.encode()).hexdigest()
        except:
            # Fallback to just path if stat fails
            return hashlib.md5(str(file_path.absolute()).encode()).hexdigest()
    
    def is_processed(self, file_path: Path) -> bool:
        """
        Check if a file has been processed
        
        Args:
            file_path: Path to file
            
        Returns:
            True if file was already processed
        """
        file_hash = self._get_file_hash(file_path)
        
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM processed_files WHERE file_hash = ?", (file_hash,))
        result = cursor.fetchone()
        conn.close()
        
        return result is not None
    
    def get_processed_result(self, file_path: Path) -> Optional[Dict]:
        """
        Get cached result for a file
        
        Args:
            file_path: Path to file
            
        Returns:
            Cached result dict or None if not found
        """
        file_hash = self._get_file_hash(file_path)
        
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT file_path, file_name, processed_at, status, comparison,
                   filename_gcn, predicted_gcn, error
            FROM processed_files 
            WHERE file_hash = ?
        """, (file_hash,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "file_path": row[0],
                "file_name": row[1],
                "processed_at": row[2],
                "status": row[3],
                "comparison": row[4],
                "filename_gcn": row[5],
                "predicted_gcn": row[6],
                "error": row[7]
            }
        return None
    
    def add_processed(self, file_path: Path, result: Dict):
        """
        Add a processed file to cache (with REPLACE for updates)
        
        Args:
            file_path: Path to file
            result: Processing result dict
        """
        file_hash = self._get_file_hash(file_path)
        
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Use REPLACE to update if exists, insert if not
        cursor.execute("""
            REPLACE INTO processed_files 
            (file_hash, file_path, file_name, processed_at, status, 
             comparison, filename_gcn, predicted_gcn, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            file_hash,
            str(file_path.absolute()),
            file_path.name,
            datetime.now().isoformat(),
            result.get("status"),
            result.get("comparison"),
            result.get("filename_gcn"),
            result.get("predicted_gcn"),
            result.get("error")
        ))
        
        conn.commit()
        conn.close()
    
    def remove_processed(self, file_path: Path):
        """
        Remove a file from cache
        
        Args:
            file_path: Path to file
        """
        file_hash = self._get_file_hash(file_path)
        
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM processed_files WHERE file_hash = ?", (file_hash,))
        conn.commit()
        conn.close()
    
    def clear_cache(self):
        """Clear all cache"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM processed_files")
        conn.commit()
        conn.close()
    
    def get_all_processed_files(self) -> Set[str]:
        """
        Get set of all processed file names
        
        Returns:
            Set of file names
        """
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT file_name FROM processed_files")
        file_names = {row[0] for row in cursor.fetchall()}
        conn.close()
        return file_names
    
    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics
        
        Returns:
            Dict with cache stats
        """
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM processed_files")
        total = cursor.fetchone()[0]
        
        # Get counts by status
        cursor.execute("SELECT status, COUNT(*) FROM processed_files GROUP BY status")
        status_counts = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            "total": total,
            "success": status_counts.get("success", 0),
            "skip": status_counts.get("skip", 0),
            "error": status_counts.get("error", 0)
        }

