import asyncio
import subprocess
import os
import requests
from pathlib import Path

__all__ = [
    "download",
    "download_video",
    "download_and_decrypt_video",
    "decrypt_and_merge_video",
    "send_vid",
    "get_mps_and_keys",
    "download_and_decrypt_pdf",
    "pdf_download",
    "decrypt_file_txt",
    "watermark_pdf",
]

async def _run_cmd(cmd: str) -> int:
    """Run a shell command in a thread and return the exit code."""
    def _run():
        return subprocess.call(cmd, shell=True)
    return await asyncio.to_thread(_run)

async def download(url: str, name: str) -> str:
    """Download a file from a URL. Returns the local filename.

    This is a best-effort implementation: for many media links yt-dlp is more
    robust, but we try a simple requests stream first and fall back to yt-dlp.
    """
    out = f"{name}"
    # Try streaming with requests
    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(out, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        return out
    except Exception:
        # Fallback to yt-dlp
        cmd = f'yt-dlp -o "{out}" "{url}"'
        code = await _run_cmd(cmd)
        if code == 0 and os.path.exists(out):
            return out
        raise RuntimeError(f"Failed to download {url}")

async def download_video(url: str, cmd: str, name: str) -> str:
    """Run the provided yt-dlp command (or similar) and return the created filename.

    main.py expects this to return the path to the downloaded file (e.g. "name.mp4").
    """
    # If a command is provided, run it; otherwise build a default one
    if cmd:
        run_cmd = cmd
    else:
        run_cmd = f'yt-dlp -o "{name}.mp4" "{url}"'
    code = await _run_cmd(run_cmd)
    expected = f"{name}.mp4"
    if code == 0 and os.path.exists(expected):
        return expected
    # If yt-dlp produced a differently named file, try to find a recent file matching name
    candidates = list(Path('.').glob(f"{name}*"))
    if candidates:
        return str(candidates[0])
    raise RuntimeError(f"Video download failed for {url}")

async def download_and_decrypt_video(url: str, cmd: str, name: str, appxkey: str) -> str:
    """Placeholder: download then (optionally) decrypt.

    For now we attempt a normal download and return the filename. If you need
    actual DRM decryption, replace this with the proper implementation.
    """
    return await download_video(url, cmd, name)

async def decrypt_and_merge_video(mpd: str, keys_string: str, path: str, name: str, raw_text2: str) -> str:
    """Placeholder for decrypt+merge workflow used by DRM flows.

    This implementation simply downloads the MPD URL (if reachable) or
    returns a reasonable filename. Replace with the real logic if required.
    """
    # Try to download the mpd (yt-dlp can handle many MPD manifests)
    cmd = f'yt-dlp -o "{name}.mp4" "{mpd}"'
    code = await _run_cmd(cmd)
    expected = f"{name}.mp4"
    if code == 0 and os.path.exists(expected):
        return expected
    # fallback: return name with .mp4 extension and let the caller handle errors
    return expected

async def send_vid(bot, m, cc, filename: str, thumb, name: str, prog=None):
    """Send a video/file using the provided bot and message object.

    This tries send_video first and falls back to send_document if that fails.
    After sending the file the local copy is removed when possible.
    """
    try:
        # Prefer send_video for mp4 files
        if filename and os.path.exists(filename):
            await bot.send_video(chat_id=m.chat.id, video=filename, caption=cc)
        else:
            # If file does not exist, raise to let caller handle it
            raise FileNotFoundError(filename)
    except Exception:
        try:
            if filename and os.path.exists(filename):
                await bot.send_document(chat_id=m.chat.id, document=filename, caption=cc)
        except Exception as e:
            # If sending fails, re-raise so the caller can report the error
            raise
    finally:
        try:
            if filename and os.path.exists(filename):
                os.remove(filename)
        except Exception:
            pass

def get_mps_and_keys(url: str):
    """Return (mpd, keys) tuple expected by main.py.

    Real implementation would parse an API response. Here we return the
    provided URL as the mpd and an empty keys list.
    """
    return url, []

async def download_and_decrypt_pdf(url: str, name: str, pdf_key: str) -> str:
    out = f"{name}.pdf"
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        with open(out, "wb") as f:
            f.write(r.content)
        return out
    except Exception:
        # fallback to yt-dlp
        cmd = f'yt-dlp -o "{out}" "{url}"'
        code = await _run_cmd(cmd)
        if code == 0 and os.path.exists(out):
            return out
        raise

async def pdf_download(url: str, output: str) -> None:
    # simple download to the output path
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        with open(output, "wb") as f:
            f.write(r.content)
    except Exception as e:
        raise

def decrypt_file_txt(path: str) -> str:
    """Placeholder decryption for text files.

    If your project had a custom encrypted text format, implement it here.
    For now we return the same path (no-op).
    """
    return path

async def watermark_pdf(file_path: str, watermark_text: str) -> str:
    # no-op for now
    return file_path
