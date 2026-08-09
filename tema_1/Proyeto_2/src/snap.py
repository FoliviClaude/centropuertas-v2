"""Lógica core de Snap: generación de códigos cortos y gestión de URLs."""
import random
import string

from src.database import code_exists, get_url, list_urls, save_url

CODE_LENGTH = 6
ALPHABET = string.ascii_letters + string.digits


def generate_short_code(length: int = CODE_LENGTH) -> str:
    return "".join(random.choices(ALPHABET, k=length))


def shorten_url(long_url: str) -> str:
    if not long_url or not long_url.strip():
        raise ValueError("La URL no puede estar vacía")
    if not long_url.startswith(("http://", "https://")):
        raise ValueError("La URL debe comenzar con http:// o https://")

    short_code = generate_short_code()
    while code_exists(short_code):
        short_code = generate_short_code()

    save_url(short_code, long_url)
    return short_code


def resolve_short_code(short_code: str) -> str:
    long_url = get_url(short_code)
    if long_url is None:
        raise ValueError(f"El código '{short_code}' no existe")
    return long_url


def get_all_urls() -> list:
    return list_urls()
