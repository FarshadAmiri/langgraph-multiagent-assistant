"""Simple memory store for agent interactions"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class MemoryStore:
    """Lightweight memory mechanism for storing and retrieving interactions"""
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_dir = Path(__file__).parent / "logs"
            db_dir.mkdir(exist_ok=True)
            db_path = str(db_dir / "memory.db")
        
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create interactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                query TEXT NOT NULL,
                agent TEXT NOT NULL,
                output TEXT,
                sources TEXT,
                metadata TEXT
            )
        """)
        
        # Create index on timestamp for faster retrieval
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON interactions(timestamp DESC)
        """)
        
        conn.commit()
        conn.close()
    
    def store_interaction(
        self,
        query: str,
        agent: str,
        output: str,
        sources: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> int:
        """Store an interaction in memory"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        sources_json = json.dumps(sources or [])
        metadata_json = json.dumps(metadata or {})
        
        cursor.execute("""
            INSERT INTO interactions (timestamp, query, agent, output, sources, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (timestamp, query, agent, output, sources_json, metadata_json))
        
        interaction_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return interaction_id
    
    def get_recent_interactions(self, limit: int = 10) -> List[Dict]:
        """Retrieve recent interactions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT timestamp, query, agent, output, sources, metadata
            FROM interactions
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        interactions = []
        for row in rows:
            interactions.append({
                "timestamp": row[0],
                "query": row[1],
                "agent": row[2],
                "output": row[3],
                "sources": json.loads(row[4]),
                "metadata": json.loads(row[5])
            })
        
        return interactions
    
    def search_interactions(self, query: str, limit: int = 5) -> List[Dict]:
        """Search for similar past interactions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Simple search using LIKE
        cursor.execute("""
            SELECT timestamp, query, agent, output, sources, metadata
            FROM interactions
            WHERE query LIKE ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (f"%{query}%", limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        interactions = []
        for row in rows:
            interactions.append({
                "timestamp": row[0],
                "query": row[1],
                "agent": row[2],
                "output": row[3],
                "sources": json.loads(row[4]),
                "metadata": json.loads(row[5])
            })
        
        return interactions
    
    def clear_old_interactions(self, days: int = 30):
        """Clear interactions older than specified days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        cutoff_iso = datetime.fromtimestamp(cutoff_date).isoformat()
        
        cursor.execute("""
            DELETE FROM interactions
            WHERE timestamp < ?
        """, (cutoff_iso,))
        
        conn.commit()
        conn.close()
