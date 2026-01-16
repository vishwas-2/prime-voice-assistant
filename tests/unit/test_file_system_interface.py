"""
Unit tests for File System Interface.

Tests all file operations including create, read, update, delete, search,
move, copy, and metadata retrieval.
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from prime.models.data_models import FileMetadata
from prime.system.file_system_interface import FileSystemInterface


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def fs_interface(temp_dir):
    """Create a FileSystemInterface instance with a temporary directory."""
    return FileSystemInterface(default_directory=temp_dir)


class TestFileCreation:
    """Tests for file creation operations."""
    
    def test_create_file_with_content(self, fs_interface, temp_dir):
        """Test creating a file with initial content."""
        content = "Hello, PRIME!"
        fs_interface.create_file("test.txt", content)
        
        file_path = Path(temp_dir) / "test.txt"
        assert file_path.exists()
        assert file_path.read_text() == content
    
    def test_create_file_empty(self, fs_interface, temp_dir):
        """Test creating an empty file."""
        fs_interface.create_file("empty.txt")
        
        file_path = Path(temp_dir) / "empty.txt"
        assert file_path.exists()
        assert file_path.read_text() == ""
    
    def test_create_file_with_subdirectories(self, fs_interface, temp_dir):
        """Test creating a file in a subdirectory that doesn't exist yet."""
        content = "Nested file"
        fs_interface.create_file("subdir/nested/test.txt", content)
        
        file_path = Path(temp_dir) / "subdir" / "nested" / "test.txt"
        assert file_path.exists()
        assert file_path.read_text() == content
    
    def test_create_file_absolute_path(self, fs_interface, temp_dir):
        """Test creating a file with an absolute path."""
        file_path = Path(temp_dir) / "absolute.txt"
        content = "Absolute path file"
        fs_interface.create_file(str(file_path), content)
        
        assert file_path.exists()
        assert file_path.read_text() == content
    
    def test_create_file_already_exists(self, fs_interface, temp_dir):
        """Test that creating an existing file raises FileExistsError."""
        fs_interface.create_file("existing.txt", "content")
        
        with pytest.raises(FileExistsError, match="File already exists"):
            fs_interface.create_file("existing.txt", "new content")


class TestFileReading:
    """Tests for file reading operations."""
    
    def test_read_file_success(self, fs_interface, temp_dir):
        """Test reading a file successfully."""
        content = "Test content for reading"
        file_path = Path(temp_dir) / "read_test.txt"
        file_path.write_text(content)
        
        result = fs_interface.read_file("read_test.txt")
        assert result == content
    
    def test_read_file_absolute_path(self, fs_interface, temp_dir):
        """Test reading a file with an absolute path."""
        content = "Absolute path content"
        file_path = Path(temp_dir) / "absolute_read.txt"
        file_path.write_text(content)
        
        result = fs_interface.read_file(str(file_path))
        assert result == content
    
    def test_read_file_not_found(self, fs_interface):
        """Test that reading a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="File not found"):
            fs_interface.read_file("nonexistent.txt")
    
    def test_read_directory_raises_error(self, fs_interface, temp_dir):
        """Test that reading a directory raises IsADirectoryError."""
        subdir = Path(temp_dir) / "subdir"
        subdir.mkdir()
        
        with pytest.raises(IsADirectoryError, match="Path is a directory"):
            fs_interface.read_file("subdir")
    
    def test_read_file_with_unicode(self, fs_interface, temp_dir):
        """Test reading a file with Unicode content."""
        content = "Hello 世界! 🌍"
        file_path = Path(temp_dir) / "unicode.txt"
        file_path.write_text(content, encoding='utf-8')
        
        result = fs_interface.read_file("unicode.txt")
        assert result == content


class TestFileUpdate:
    """Tests for file update operations."""
    
    def test_update_file_success(self, fs_interface, temp_dir):
        """Test updating a file successfully."""
        file_path = Path(temp_dir) / "update_test.txt"
        file_path.write_text("Original content")
        
        new_content = "Updated content"
        fs_interface.update_file("update_test.txt", new_content)
        
        assert file_path.read_text() == new_content
    
    def test_update_file_not_found(self, fs_interface):
        """Test that updating a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="File not found"):
            fs_interface.update_file("nonexistent.txt", "content")
    
    def test_update_directory_raises_error(self, fs_interface, temp_dir):
        """Test that updating a directory raises IsADirectoryError."""
        subdir = Path(temp_dir) / "subdir"
        subdir.mkdir()
        
        with pytest.raises(IsADirectoryError, match="Path is a directory"):
            fs_interface.update_file("subdir", "content")
    
    def test_update_file_replaces_content(self, fs_interface, temp_dir):
        """Test that update completely replaces file content."""
        file_path = Path(temp_dir) / "replace_test.txt"
        file_path.write_text("Line 1\nLine 2\nLine 3")
        
        new_content = "Single line"
        fs_interface.update_file("replace_test.txt", new_content)
        
        assert file_path.read_text() == new_content


class TestFileDeletion:
    """Tests for file deletion operations."""
    
    def test_delete_file_success(self, fs_interface, temp_dir):
        """Test deleting a file successfully."""
        file_path = Path(temp_dir) / "delete_test.txt"
        file_path.write_text("To be deleted")
        
        fs_interface.delete_file("delete_test.txt")
        assert not file_path.exists()
    
    def test_delete_file_not_found(self, fs_interface):
        """Test that deleting a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="File not found"):
            fs_interface.delete_file("nonexistent.txt")
    
    def test_delete_directory_raises_error(self, fs_interface, temp_dir):
        """Test that deleting a directory raises IsADirectoryError."""
        subdir = Path(temp_dir) / "subdir"
        subdir.mkdir()
        
        with pytest.raises(IsADirectoryError, match="Path is a directory"):
            fs_interface.delete_file("subdir")
    
    def test_delete_file_absolute_path(self, fs_interface, temp_dir):
        """Test deleting a file with an absolute path."""
        file_path = Path(temp_dir) / "absolute_delete.txt"
        file_path.write_text("Delete me")
        
        fs_interface.delete_file(str(file_path))
        assert not file_path.exists()


class TestFileSearch:
    """Tests for file search operations."""
    
    def test_search_files_by_name(self, fs_interface, temp_dir):
        """Test searching files by name."""
        # Create test files
        (Path(temp_dir) / "test1.txt").write_text("content")
        (Path(temp_dir) / "test2.txt").write_text("content")
        (Path(temp_dir) / "other.txt").write_text("content")
        
        results = fs_interface.search_files("test", search_content=False)
        
        assert len(results) == 2
        assert any("test1.txt" in r for r in results)
        assert any("test2.txt" in r for r in results)
        assert not any("other.txt" in r for r in results)
    
    def test_search_files_by_content(self, fs_interface, temp_dir):
        """Test searching files by content."""
        (Path(temp_dir) / "file1.txt").write_text("Hello world")
        (Path(temp_dir) / "file2.txt").write_text("Goodbye world")
        (Path(temp_dir) / "file3.txt").write_text("Something else")
        
        results = fs_interface.search_files("world", search_content=True)
        
        assert len(results) == 2
        assert any("file1.txt" in r for r in results)
        assert any("file2.txt" in r for r in results)
        assert not any("file3.txt" in r for r in results)
    
    def test_search_files_with_type_filter(self, fs_interface, temp_dir):
        """Test searching files with file type filter."""
        (Path(temp_dir) / "test.txt").write_text("content")
        (Path(temp_dir) / "test.py").write_text("content")
        (Path(temp_dir) / "test.md").write_text("content")
        
        results = fs_interface.search_files("test", file_type=".py", search_content=False)
        
        assert len(results) == 1
        assert results[0].endswith("test.py")
    
    def test_search_files_in_subdirectories(self, fs_interface, temp_dir):
        """Test that search includes subdirectories."""
        subdir = Path(temp_dir) / "subdir"
        subdir.mkdir()
        (subdir / "nested.txt").write_text("content")
        (Path(temp_dir) / "root.txt").write_text("content")
        
        results = fs_interface.search_files(".txt", search_content=False)
        
        assert len(results) == 2
        assert any("nested.txt" in r for r in results)
        assert any("root.txt" in r for r in results)
    
    def test_search_files_case_insensitive(self, fs_interface, temp_dir):
        """Test that search is case-insensitive."""
        (Path(temp_dir) / "TEST.txt").write_text("CONTENT")
        
        results = fs_interface.search_files("test", search_content=False)
        assert len(results) == 1
        
        results = fs_interface.search_files("content", search_content=True)
        assert len(results) == 1
    
    def test_search_files_custom_path(self, fs_interface, temp_dir):
        """Test searching in a custom path."""
        subdir = Path(temp_dir) / "custom"
        subdir.mkdir()
        (subdir / "file.txt").write_text("content")
        (Path(temp_dir) / "file.txt").write_text("content")
        
        results = fs_interface.search_files("file", search_path="custom", search_content=False)
        
        assert len(results) == 1
        assert "custom" in results[0]
    
    def test_search_files_path_not_found(self, fs_interface):
        """Test that searching in a non-existent path raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Search path not found"):
            fs_interface.search_files("test", search_path="nonexistent")
    
    def test_search_files_empty_results(self, fs_interface, temp_dir):
        """Test that search returns empty list when no matches found."""
        (Path(temp_dir) / "file.txt").write_text("content")
        
        results = fs_interface.search_files("nonexistent", search_content=False)
        assert results == []


class TestFileMove:
    """Tests for file move operations."""
    
    def test_move_file_success(self, fs_interface, temp_dir):
        """Test moving a file successfully."""
        source = Path(temp_dir) / "source.txt"
        source.write_text("Move me")
        
        fs_interface.move_file("source.txt", "destination.txt")
        
        dest = Path(temp_dir) / "destination.txt"
        assert not source.exists()
        assert dest.exists()
        assert dest.read_text() == "Move me"
    
    def test_move_file_to_directory(self, fs_interface, temp_dir):
        """Test moving a file into a directory."""
        source = Path(temp_dir) / "file.txt"
        source.write_text("content")
        
        dest_dir = Path(temp_dir) / "subdir"
        dest_dir.mkdir()
        
        fs_interface.move_file("file.txt", "subdir")
        
        assert not source.exists()
        assert (dest_dir / "file.txt").exists()
        assert (dest_dir / "file.txt").read_text() == "content"
    
    def test_move_file_with_subdirectories(self, fs_interface, temp_dir):
        """Test moving a file to a path with subdirectories."""
        source = Path(temp_dir) / "file.txt"
        source.write_text("content")
        
        fs_interface.move_file("file.txt", "new/nested/path/file.txt")
        
        dest = Path(temp_dir) / "new" / "nested" / "path" / "file.txt"
        assert not source.exists()
        assert dest.exists()
    
    def test_move_file_source_not_found(self, fs_interface):
        """Test that moving a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Source file not found"):
            fs_interface.move_file("nonexistent.txt", "destination.txt")
    
    def test_move_file_destination_exists(self, fs_interface, temp_dir):
        """Test that moving to an existing file raises FileExistsError."""
        source = Path(temp_dir) / "source.txt"
        source.write_text("source")
        
        dest = Path(temp_dir) / "dest.txt"
        dest.write_text("dest")
        
        with pytest.raises(FileExistsError, match="Destination file already exists"):
            fs_interface.move_file("source.txt", "dest.txt")
    
    def test_move_directory_raises_error(self, fs_interface, temp_dir):
        """Test that moving a directory raises IsADirectoryError."""
        subdir = Path(temp_dir) / "subdir"
        subdir.mkdir()
        
        with pytest.raises(IsADirectoryError, match="Source is a directory"):
            fs_interface.move_file("subdir", "newdir")


class TestFileCopy:
    """Tests for file copy operations."""
    
    def test_copy_file_success(self, fs_interface, temp_dir):
        """Test copying a file successfully."""
        source = Path(temp_dir) / "source.txt"
        source.write_text("Copy me")
        
        fs_interface.copy_file("source.txt", "destination.txt")
        
        dest = Path(temp_dir) / "destination.txt"
        assert source.exists()  # Source should still exist
        assert dest.exists()
        assert dest.read_text() == "Copy me"
    
    def test_copy_file_to_directory(self, fs_interface, temp_dir):
        """Test copying a file into a directory."""
        source = Path(temp_dir) / "file.txt"
        source.write_text("content")
        
        dest_dir = Path(temp_dir) / "subdir"
        dest_dir.mkdir()
        
        fs_interface.copy_file("file.txt", "subdir")
        
        assert source.exists()  # Source should still exist
        assert (dest_dir / "file.txt").exists()
        assert (dest_dir / "file.txt").read_text() == "content"
    
    def test_copy_file_with_subdirectories(self, fs_interface, temp_dir):
        """Test copying a file to a path with subdirectories."""
        source = Path(temp_dir) / "file.txt"
        source.write_text("content")
        
        fs_interface.copy_file("file.txt", "new/nested/path/file.txt")
        
        dest = Path(temp_dir) / "new" / "nested" / "path" / "file.txt"
        assert source.exists()  # Source should still exist
        assert dest.exists()
    
    def test_copy_file_source_not_found(self, fs_interface):
        """Test that copying a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Source file not found"):
            fs_interface.copy_file("nonexistent.txt", "destination.txt")
    
    def test_copy_file_destination_exists(self, fs_interface, temp_dir):
        """Test that copying to an existing file raises FileExistsError."""
        source = Path(temp_dir) / "source.txt"
        source.write_text("source")
        
        dest = Path(temp_dir) / "dest.txt"
        dest.write_text("dest")
        
        with pytest.raises(FileExistsError, match="Destination file already exists"):
            fs_interface.copy_file("source.txt", "dest.txt")
    
    def test_copy_directory_raises_error(self, fs_interface, temp_dir):
        """Test that copying a directory raises IsADirectoryError."""
        subdir = Path(temp_dir) / "subdir"
        subdir.mkdir()
        
        with pytest.raises(IsADirectoryError, match="Source is a directory"):
            fs_interface.copy_file("subdir", "newdir")
    
    def test_copy_preserves_content(self, fs_interface, temp_dir):
        """Test that copying preserves file content exactly."""
        source = Path(temp_dir) / "source.txt"
        content = "Line 1\nLine 2\nLine 3\n"
        source.write_text(content)
        
        fs_interface.copy_file("source.txt", "dest.txt")
        
        dest = Path(temp_dir) / "dest.txt"
        assert dest.read_text() == content


class TestFileMetadata:
    """Tests for file metadata retrieval."""
    
    def test_get_file_metadata_success(self, fs_interface, temp_dir):
        """Test getting file metadata successfully."""
        file_path = Path(temp_dir) / "metadata_test.txt"
        content = "Test content"
        file_path.write_text(content)
        
        metadata = fs_interface.get_file_metadata("metadata_test.txt")
        
        assert isinstance(metadata, FileMetadata)
        assert metadata.name == "metadata_test.txt"
        assert metadata.size_bytes == len(content.encode('utf-8'))
        assert metadata.is_directory is False
        assert metadata.extension == ".txt"
        assert isinstance(metadata.created_at, datetime)
        assert isinstance(metadata.modified_at, datetime)
        assert metadata.permissions.startswith("0o")
    
    def test_get_file_metadata_no_extension(self, fs_interface, temp_dir):
        """Test getting metadata for a file without extension."""
        file_path = Path(temp_dir) / "noextension"
        file_path.write_text("content")
        
        metadata = fs_interface.get_file_metadata("noextension")
        
        assert metadata.extension is None
    
    def test_get_file_metadata_directory(self, fs_interface, temp_dir):
        """Test getting metadata for a directory."""
        subdir = Path(temp_dir) / "subdir"
        subdir.mkdir()
        
        metadata = fs_interface.get_file_metadata("subdir")
        
        assert metadata.is_directory is True
        assert metadata.name == "subdir"
    
    def test_get_file_metadata_not_found(self, fs_interface):
        """Test that getting metadata for non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="File not found"):
            fs_interface.get_file_metadata("nonexistent.txt")
    
    def test_get_file_metadata_absolute_path(self, fs_interface, temp_dir):
        """Test getting metadata with an absolute path."""
        file_path = Path(temp_dir) / "absolute.txt"
        file_path.write_text("content")
        
        metadata = fs_interface.get_file_metadata(str(file_path))
        
        assert metadata.name == "absolute.txt"
        assert str(file_path) in metadata.path


class TestPathResolution:
    """Tests for path resolution behavior."""
    
    def test_relative_path_uses_default_directory(self, fs_interface, temp_dir):
        """Test that relative paths are resolved relative to default directory."""
        fs_interface.create_file("relative.txt", "content")
        
        file_path = Path(temp_dir) / "relative.txt"
        assert file_path.exists()
    
    def test_absolute_path_used_directly(self, temp_dir):
        """Test that absolute paths are used directly."""
        # Create interface with different default directory
        other_dir = Path(temp_dir) / "other"
        other_dir.mkdir()
        fs_interface = FileSystemInterface(default_directory=str(other_dir))
        
        # Create file with absolute path in temp_dir
        abs_path = Path(temp_dir) / "absolute.txt"
        fs_interface.create_file(str(abs_path), "content")
        
        # File should be in temp_dir, not other_dir
        assert abs_path.exists()
        assert not (other_dir / "absolute.txt").exists()
    
    def test_home_directory_expansion(self, temp_dir):
        """Test that ~ is expanded to home directory."""
        fs_interface = FileSystemInterface(default_directory="~/test_prime")
        
        # The default directory should be expanded
        assert "~" not in str(fs_interface.default_directory)
        assert fs_interface.default_directory.is_absolute()
    
    def test_default_directory_created(self):
        """Test that default directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = Path(tmpdir) / "new" / "nested" / "dir"
            fs_interface = FileSystemInterface(default_directory=str(new_dir))
            
            assert new_dir.exists()
            assert new_dir.is_dir()
