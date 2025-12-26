from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any

@dataclass(frozen=True)
class FileInfo:
    """Immutable value object for file metadata."""
    id: int
    folder_index: int
    path: str  # Relative path in the project
    name: str
    ext: str
    size: int
    modified_date: float
    md5: Optional[str] = None
    llm_embedding: Optional[bytes] = None
    last_seen: Optional[float] = None
    
    @property
    def full_path(self) -> str:
        """Construct display path."""
        return f"{self.path}/{self.name}" if self.path else self.name

    @classmethod
    def from_db_row(cls, row: tuple) -> 'FileInfo':
        """Helper to create FileInfo from database row."""
        # row: (id, folder_index, path, name, ext, last_seen, size, modified_date, md5, llm_embedding)
        return cls(
            id=row[0],
            folder_index=row[1],
            path=row[2],
            name=row[3],
            ext=row[4],
            last_seen=row[5],
            size=row[6],
            modified_date=row[7],
            md5=row[8],
            llm_embedding=row[9]
        )
