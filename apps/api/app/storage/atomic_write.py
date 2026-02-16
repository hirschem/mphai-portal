import os
import tempfile
from pathlib import Path
from typing import Union

import aiofiles

async def atomic_write_bytes(path: Union[str, Path], data: bytes, mode: str = 'wb'):
    """
    Atomically write bytes to a file. Writes to a temp file and moves it into place.
    """
    path = Path(path)
    dir_path = path.parent
    dir_path.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=dir_path, prefix=path.name + ".tmp.")
    os.close(fd)
    try:
        async with aiofiles.open(tmp_path, mode) as f:
            await f.write(data)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise

async def atomic_write_text(path: Union[str, Path], text: str, encoding: str = 'utf-8'):
    """
    Atomically write text to a file. Writes to a temp file and moves it into place.
    """
    await atomic_write_bytes(path, text.encode(encoding), mode='wb')
