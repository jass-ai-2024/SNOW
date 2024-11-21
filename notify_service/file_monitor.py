import inotify.adapters
import sys
import os
import aiohttp
import asyncio
from pathlib import Path
import mimetypes


class DocumentUploader:
    def __init__(self):
        self.api_url = "https://api.snowjass.ru/v1/documents"
        self.supported_extensions = {'.txt', '.pdf'}
        self.session = None

    async def init_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def close_session(self):
        if self.session:
            await self.session.close()
            self.session = None

    async def upload_file(self, file_path: str):
        if not any(file_path.lower().endswith(ext) for ext in self.supported_extensions):
            return

        try:
            await self.init_session()

            mime_type = mimetypes.guess_type(file_path)[0]

            with open(file_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file',
                               f,
                               filename=os.path.basename(file_path),
                               content_type=mime_type)

            async with self.session.post(self.api_url, data=data) as response:
                if response.status == 200:
                    print(f"Successfully uploaded {file_path}")
                    response_data = await response.json()
                    print(f"API Response: {response_data}")
                else:
                    print(f"Failed to upload {file_path}. Status: {response.status}")
                    print(f"Response: {await response.text()}")

        except Exception as e:
            print(f"Error uploading {file_path}: {str(e)}")


class FileMonitor:
    def __init__(self, path):
        self.path = path
        self.uploader = DocumentUploader()
        self.inotify = inotify.adapters.InotifyTree(path)
        self.loop = asyncio.get_event_loop()

    def process_event(self, event):
        mask_types = event[1]
        file_path = os.path.join(event[2], event[3].decode('utf-8')) if event[3] else event[2]

        if ('IN_CLOSE_WRITE' in mask_types or
            'IN_MOVED_TO' in mask_types) and \
                any(file_path.lower().endswith(ext) for ext in self.uploader.supported_extensions):

            print(f"File event detected: {file_path}")
            if 'IN_CLOSE_WRITE' in mask_types:
                print(f"File modified/created: {file_path}")
            elif 'IN_MOVED_TO' in mask_types:
                print(f"File moved to watch directory: {file_path}")

            self.loop.create_task(self.uploader.upload_file(file_path))

    async def monitor(self):
        """Асинхронный мониторинг файловой системы"""
        await self.uploader.init_session()

        try:
            for event in self.inotify.event_gen(yield_nones=False):
                self.process_event(event)
                await asyncio.sleep(0)  # Даём шанс другим корутинам выполниться

        except KeyboardInterrupt:
            print("\nStopping monitoring...")
        finally:
            await self.uploader.close_session()


async def main(path):
    if not os.path.exists(path):
        print(f"Directory {path} does not exist!")
        return

    monitor = FileMonitor(path)
    print(f"Starting monitoring directory: {path}")
    print(f"Watching for files with extensions: {', '.join(monitor.uploader.supported_extensions)}")
    print("Press Ctrl+C to stop")

    await monitor.monitor()


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "/monitored"

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main(path))
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()