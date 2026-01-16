"""
File System Interface for PRIME Voice Assistant.

This module provides file management capabilities including creating, reading,
updating, deleting, searching, moving, and copying files. It also provides
file metadata retrieval.

Validates Requirements:
- 7.1: Open files with appropriate application
- 7.2: Create files in specified or default location
- 7.3: Move or copy files and confirm completion
- 7.4: Search for files by name, type, or content
- 7.5: Present options and ask for clarification when multiple files match
"""

import os
import shutil
import stat
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from prime.models.data_models import FileMetadata


class FileSystemInterface:
    """
    Provides file system operations for PRIME Voice Assistant.
    
    This class handles all file-related operations including CRUD operations,
    file search, and metadata retrieval. All operations validate paths and
    handle errors gracefully.
    """
    
    def __init__(self, default_directory: Optional[str] = None):
        """
        Initialize the File System Interface.
        
        Args:
            default_directory: Default directory for file operations.
                             If None, uses the user's home directory.
        """
        if default_directory:
            self.default_directory = Path(default_directory).expanduser().resolve()
        else:
            self.default_directory = Path.home()
        
        # Ensure default directory exists
        self.default_directory.mkdir(parents=True, exist_ok=True)
    
    def create_file(self, path: str, content: str = "") -> None:
        """
        Create a new file with the specified content.
        
        If the path is relative, it will be created in the default directory.
        Parent directories are created automatically if they don't exist.
        
        Args:
            path: Path to the file to create (absolute or relative)
            content: Initial content for the file (default: empty string)
        
        Raises:
            FileExistsError: If the file already exists
            PermissionError: If lacking permission to create the file
            OSError: For other file system errors
        
        Validates: Requirements 7.2
        """
        file_path = self._resolve_path(path)
        
        if file_path.exists():
            raise FileExistsError(f"File already exists: {file_path}")
        
        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create the file with content
        file_path.write_text(content, encoding='utf-8')
    
    def read_file(self, path: str) -> str:
        """
        Read and return the contents of a file.
        
        Args:
            path: Path to the file to read (absolute or relative)
        
        Returns:
            The contents of the file as a string
        
        Raises:
            FileNotFoundError: If the file doesn't exist
            PermissionError: If lacking permission to read the file
            IsADirectoryError: If the path points to a directory
            OSError: For other file system errors
        
        Validates: Requirements 7.1
        """
        file_path = self._resolve_path(path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if file_path.is_dir():
            raise IsADirectoryError(f"Path is a directory, not a file: {file_path}")
        
        return file_path.read_text(encoding='utf-8')
    
    def update_file(self, path: str, content: str) -> None:
        """
        Update an existing file with new content.
        
        This completely replaces the file's content. The file must already exist.
        
        Args:
            path: Path to the file to update (absolute or relative)
            content: New content for the file
        
        Raises:
            FileNotFoundError: If the file doesn't exist
            PermissionError: If lacking permission to write to the file
            IsADirectoryError: If the path points to a directory
            OSError: For other file system errors
        """
        file_path = self._resolve_path(path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if file_path.is_dir():
            raise IsADirectoryError(f"Path is a directory, not a file: {file_path}")
        
        file_path.write_text(content, encoding='utf-8')
    
    def delete_file(self, path: str) -> None:
        """
        Delete a file.
        
        This is a destructive operation and should be confirmed by the Safety Controller.
        
        Args:
            path: Path to the file to delete (absolute or relative)
        
        Raises:
            FileNotFoundError: If the file doesn't exist
            PermissionError: If lacking permission to delete the file
            IsADirectoryError: If the path points to a directory
            OSError: For other file system errors
        """
        file_path = self._resolve_path(path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if file_path.is_dir():
            raise IsADirectoryError(f"Path is a directory, not a file: {file_path}")
        
        file_path.unlink()
    
    def search_files(
        self,
        query: str,
        search_path: Optional[str] = None,
        search_content: bool = False,
        file_type: Optional[str] = None
    ) -> List[str]:
        """
        Search for files by name, type, or content.
        
        Args:
            query: Search query (filename pattern or content to search for)
            search_path: Directory to search in (default: default_directory)
            search_content: If True, search file contents; if False, search filenames
            file_type: Optional file extension filter (e.g., ".txt", ".py")
        
        Returns:
            List of absolute paths to matching files
        
        Raises:
            FileNotFoundError: If the search path doesn't exist
            PermissionError: If lacking permission to access the search path
        
        Validates: Requirements 7.4, 7.5
        """
        if search_path:
            base_path = self._resolve_path(search_path)
        else:
            base_path = self.default_directory
        
        if not base_path.exists():
            raise FileNotFoundError(f"Search path not found: {base_path}")
        
        if not base_path.is_dir():
            raise NotADirectoryError(f"Search path is not a directory: {base_path}")
        
        matches = []
        
        # Walk through directory tree
        for root, dirs, files in os.walk(base_path):
            for filename in files:
                file_path = Path(root) / filename
                
                # Apply file type filter if specified
                if file_type and not filename.endswith(file_type):
                    continue
                
                # Search by filename or content
                if search_content:
                    # Search file contents
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        if query.lower() in content.lower():
                            matches.append(str(file_path))
                    except (PermissionError, OSError):
                        # Skip files we can't read
                        continue
                else:
                    # Search by filename
                    if query.lower() in filename.lower():
                        matches.append(str(file_path))
        
        return matches
    
    def move_file(self, source: str, destination: str) -> None:
        """
        Move a file from source to destination.
        
        If destination is a directory, the file is moved into that directory
        with its original name. Otherwise, the file is moved and renamed.
        
        Args:
            source: Path to the source file (absolute or relative)
            destination: Path to the destination (absolute or relative)
        
        Raises:
            FileNotFoundError: If the source file doesn't exist
            FileExistsError: If the destination file already exists
            PermissionError: If lacking permission to move the file
            OSError: For other file system errors
        
        Validates: Requirements 7.3
        """
        source_path = self._resolve_path(source)
        dest_path = self._resolve_path(destination)
        
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        if source_path.is_dir():
            raise IsADirectoryError(f"Source is a directory, not a file: {source_path}")
        
        # If destination is a directory, move file into it
        if dest_path.is_dir():
            dest_path = dest_path / source_path.name
        
        # Check if destination already exists
        if dest_path.exists():
            raise FileExistsError(f"Destination file already exists: {dest_path}")
        
        # Create parent directories if needed
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Move the file
        shutil.move(str(source_path), str(dest_path))
    
    def copy_file(self, source: str, destination: str) -> None:
        """
        Copy a file from source to destination.
        
        If destination is a directory, the file is copied into that directory
        with its original name. Otherwise, the file is copied and renamed.
        
        Args:
            source: Path to the source file (absolute or relative)
            destination: Path to the destination (absolute or relative)
        
        Raises:
            FileNotFoundError: If the source file doesn't exist
            FileExistsError: If the destination file already exists
            PermissionError: If lacking permission to copy the file
            OSError: For other file system errors
        
        Validates: Requirements 7.3
        """
        source_path = self._resolve_path(source)
        dest_path = self._resolve_path(destination)
        
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        if source_path.is_dir():
            raise IsADirectoryError(f"Source is a directory, not a file: {source_path}")
        
        # If destination is a directory, copy file into it
        if dest_path.is_dir():
            dest_path = dest_path / source_path.name
        
        # Check if destination already exists
        if dest_path.exists():
            raise FileExistsError(f"Destination file already exists: {dest_path}")
        
        # Create parent directories if needed
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy the file
        shutil.copy2(str(source_path), str(dest_path))
    
    def get_file_metadata(self, path: str) -> FileMetadata:
        """
        Get metadata information about a file.
        
        Args:
            path: Path to the file (absolute or relative)
        
        Returns:
            FileMetadata object containing file information
        
        Raises:
            FileNotFoundError: If the file doesn't exist
            PermissionError: If lacking permission to access the file
            OSError: For other file system errors
        """
        file_path = self._resolve_path(path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Get file stats
        stats = file_path.stat()
        
        # Get file permissions in octal format
        permissions = oct(stat.S_IMODE(stats.st_mode))
        
        # Get file extension
        extension = file_path.suffix if file_path.suffix else None
        
        return FileMetadata(
            path=str(file_path),
            name=file_path.name,
            size_bytes=stats.st_size,
            created_at=datetime.fromtimestamp(stats.st_ctime),
            modified_at=datetime.fromtimestamp(stats.st_mtime),
            is_directory=file_path.is_dir(),
            extension=extension,
            permissions=permissions
        )
    
    def _resolve_path(self, path: str) -> Path:
        """
        Resolve a path to an absolute Path object.
        
        If the path is relative, it's resolved relative to the default directory.
        Expands user home directory (~) and resolves symbolic links.
        
        Args:
            path: Path to resolve (absolute or relative)
        
        Returns:
            Resolved absolute Path object
        """
        path_obj = Path(path).expanduser()
        
        if not path_obj.is_absolute():
            path_obj = self.default_directory / path_obj
        
        return path_obj.resolve()
