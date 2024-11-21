import sys
import os
import asyncio
import aiohttp
import mimetypes
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class DocumentUploader:
    def __init__(self):
        self.api_url = "https://api.snowjass.ru/v1/documents/"
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

            # Читаем содержимое файла перед формированием FormData
            with open(file_path, 'rb') as f:
                file_content = f.read()

            # Создаем FormData с уже прочитанным содержимым
            data = aiohttp.FormData()
            data.add_field('file',
                           file_content,
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


class FileEventHandler(FileSystemEventHandler):
    def __init__(self, loop, uploader):
        self.loop = loop
        self.uploader = uploader
        super().__init__()

    def on_created(self, event):
        if not event.is_directory:
            self._handle_file_event(event.src_path, "created")

    def on_modified(self, event):
        if not event.is_directory:
            self._handle_file_event(event.src_path, "modified")

    def on_moved(self, event):
        if not event.is_directory:
            self._handle_file_event(event.dest_path, "moved")

    def _handle_file_event(self, file_path, event_type):
        if any(file_path.lower().endswith(ext) for ext in self.uploader.supported_extensions):
            print(f"File {event_type}: {file_path}")
            asyncio.run_coroutine_threadsafe(
                self.delayed_upload(file_path),
                self.loop
            )

    async def delayed_upload(self, file_path, delay=0.5):
        """Загрузка файла с небольшой задержкой"""
        await asyncio.sleep(delay)
        await self.uploader.upload_file(file_path)


class FileMonitor:
    def __init__(self, path, loop):
        self.path = path
        self.loop = loop
        self.uploader = DocumentUploader()
        self.observer = Observer()
        self.event_handler = FileEventHandler(loop, self.uploader)

    async def start(self):
        """Запуск мониторинга файловой системы"""
        await self.uploader.init_session()

        self.observer.schedule(self.event_handler, self.path, recursive=True)
        self.observer.start()

        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await self.stop()

    async def stop(self):
        """Остановка мониторинга"""
        print("\nStopping monitoring...")
        self.observer.stop()
        await self.uploader.close_session()
        self.observer.join()


async def main(path):
    if not os.path.exists(path):
        print(f"Directory {path} does not exist!")
        return

    loop = asyncio.get_event_loop()
    monitor = FileMonitor(path, loop)

    print(f"Starting monitoring directory: {path}")
    print(f"Watching for files with extensions: {', '.join(monitor.uploader.supported_extensions)}")
    print("Press Ctrl+C to stop")

    await monitor.start()


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "./monitored"

    try:
        asyncio.run(main(path))
    except KeyboardInterrupt:
        pass
