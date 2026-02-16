import pytest
from unittest.mock import patch
from app.storage.file_manager import FileManager
from app.storage.atomic_write import atomic_write_bytes

import tempfile
import os
import asyncio

@pytest.mark.asyncio
async def test_atomic_write_bytes_failure(tmp_path):
    # Simulate atomic_write_bytes raising an exception
    test_path = tmp_path / "fail.txt"
    data = b"should not be written"

    with patch("app.storage.atomic_write.aiofiles.open", side_effect=IOError("disk full")):
        with pytest.raises(IOError):
            await atomic_write_bytes(test_path, data)
        # File should not exist after failure
        assert not test_path.exists()

@pytest.mark.asyncio
async def test_file_manager_save_upload_atomic(monkeypatch, tmp_path):
    # Patch atomic_write_bytes to simulate failure
    fm = FileManager()
    fm.sessions_dir = tmp_path  # redirect to temp
    class DummyFile:
        filename = "fail.png"
        async def read(self):
            return b"data"
    dummy_file = DummyFile()
    async def fail_write(*args, **kwargs):
        raise IOError("disk full")
    # Patch at the import location in file_manager
    monkeypatch.setattr("app.storage.file_manager.atomic_write_bytes", fail_write)
    with pytest.raises(IOError):
        await fm.save_upload("session1", dummy_file)
    # File should not exist
    session_dir = tmp_path / "session1"
    file_path = session_dir / f"original_{dummy_file.filename}"
    assert not file_path.exists()
    # No temp files should remain
    assert not list(session_dir.glob("*.tmp.*")), "Temp files were not cleaned up after atomic write failure"
