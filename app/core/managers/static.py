from fastapi.staticfiles import StaticFiles
from app.core.config import config
from fastapi import FastAPI
from PIL import Image
from io import BytesIO
import hashlib
import os


class StaticFilesManager:

    @staticmethod
    def init_static_files(app: FastAPI) -> None:
        app.mount(
            config.static_url, StaticFiles(directory=config.static_dir), name="static"
        )

    @staticmethod
    def save_static_file(file_bytes: bytes) -> str:
        file_hash = hashlib.sha256(file_bytes).hexdigest()
        file_path = f"{config.static_dir}/{file_hash}"
        with open(file_path, "wb") as file:
            file.write(file_bytes)
        return f"{config.static_url}/{file_hash}"

    @staticmethod
    def remove_static_file(file_hash: str) -> None:
        file_path = f"{config.static_dir}/{file_hash}"
        try:
            os.remove(file_path)
        except FileNotFoundError:
            pass

    @staticmethod
    def save_avatar_file(file_bytes: bytes, size: tuple[int, int] = (128, 128)) -> str:
        with BytesIO(file_bytes) as file:
            image = Image.open(file)
            image.thumbnail(size)
            image_bytes = BytesIO()
            image.save(image_bytes, format="WEBP")
        file_hash = hashlib.sha256(image_bytes.getvalue()).hexdigest()
        file_path = f"{config.static_dir}/avatars/{file_hash}.webp"
        with open(file_path, "wb") as file:
            file.write(image_bytes.getvalue())
        return f"{config.static_url}/avatars/{file_hash}.webp"
