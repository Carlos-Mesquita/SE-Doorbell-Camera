import asyncio
import os
import tempfile
from logging import getLogger
from typing import Any, AsyncGenerator

import aiofiles
from ...dtos import CaptureDTO, SettingsDTO
from ...models import Capture, Settings
from ...services import ICaptureService, ISettingsService
from ...repositories import (
    ICaptureRepository, ISettingsRepository
)
from dependency_injector.wiring import inject, Provide

from ...mappers import IMapper
from .base import BaseService


class CaptureService(BaseService[CaptureDTO, Capture], ICaptureService):

    @inject
    def __init__(
        self,
        mapper: IMapper[CaptureDTO, Capture] = Provide['capture_mapper'],
        repo: ICaptureRepository = Provide['capture_repo'],
        config: dict[str, Any] = Provide['config'],
    ):
        super().__init__(mapper, repo)
        self._repo = repo
        self._capture_dir = config['capture_dir']
        self._logger = getLogger()

    async def generate_video(self, paths: list[str]) -> AsyncGenerator[bytes, None]:
        """
            Generate stop motion video from capture paths using ffmpeg
            Returns an async generator that yields video bytes
        """
        if not paths:
            raise ValueError("No paths provided")

        temp_dir = None
        try:
            temp_dir = tempfile.mkdtemp(prefix="stop_motion_")

            image_paths = []
            for i, path in enumerate(paths):
                try:
                    full_path = os.path.join(self._capture_dir, path) if not os.path.isabs(path) else path

                    if not os.path.exists(full_path):
                        print(f"File not found: {full_path}")
                        continue

                    filename = f"frame_{i:04d}.png"
                    dest_path = os.path.join(temp_dir, filename)

                    import shutil
                    shutil.copy2(full_path, dest_path)

                    image_paths.append(dest_path)

                except Exception as e:
                    self._logger.error(f"Failed to process capture {path}: {e}")
                    continue

            if not image_paths:
                raise ValueError("Failed to process any images")

            self._logger.info(f"Processing {len(image_paths)} images for stop motion video")

            output_path = os.path.join(temp_dir, "stop_motion_output.mp4")
            input_pattern = os.path.join(temp_dir, "frame_%04d.png")

            ffmpeg_cmd = [
                'ffmpeg',
                '-r', '8',
                '-i', input_pattern,
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-crf', '18',
                '-preset', 'medium',
                '-movflags', '+faststart',
                '-y',
                output_path
            ]

            process = await asyncio.create_subprocess_exec(
                *ffmpeg_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=temp_dir
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                raise RuntimeError(f"FFmpeg failed: {stderr.decode()}")

            if not os.path.exists(output_path):
                raise RuntimeError("FFmpeg completed but no output file was created")

            async with aiofiles.open(output_path, 'rb') as video_file:
                while True:
                    chunk = await video_file.read(8192)
                    if not chunk:
                        break
                    yield chunk

        except Exception as e:
            self._logger.error(f"Error in generate_video: {e}")
            raise
        finally:
            if temp_dir and os.path.exists(temp_dir):
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                except Exception as cleanup_error:
                    self._logger.error(f"Failed to cleanup temp directory: {cleanup_error}")


class SettingsService(BaseService[SettingsDTO, Settings], ISettingsService):

    @inject
    def __init__(
        self,
        mapper: IMapper[SettingsDTO, Settings] = Provide['settings_mapper'],
        repo: ISettingsRepository = Provide['settings_repo']
    ):
        super().__init__(mapper, repo)
        self._repo = repo
