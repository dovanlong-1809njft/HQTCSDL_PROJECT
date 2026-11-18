"""Validate local video content and create browser-compatible MP4, without metadata."""
import json
import math
import shutil
import subprocess
import tempfile
from threading import BoundedSemaphore
from pathlib import Path

from fastapi import HTTPException

MAX_VIDEO_BYTES = 50 * 1024 * 1024
VIDEO_SLOTS = BoundedSemaphore(2)


def normalize_video(data):
    if not VIDEO_SLOTS.acquire(timeout=1):
        raise HTTPException(503,"Máy chủ đang xử lý video khác, vui lòng thử lại sau.")
    try:
        return _normalize_video(data)
    finally:
        VIDEO_SLOTS.release()


def _normalize_video(data):
    if not shutil.which("ffprobe") or not shutil.which("ffmpeg"):
        raise HTTPException(503, "Máy chủ chưa có bộ xử lý video. Cần build lại backend.")
    with tempfile.TemporaryDirectory(prefix="familyconnect-video-") as folder:
        source, target = Path(folder)/"input", Path(folder)/"output.mp4"
        source.write_bytes(data)
        try:
            probe = subprocess.run(["ffprobe","-v","error","-protocol_whitelist","file,pipe",
                "-format_whitelist","mov,matroska,webm","-show_entries",
                "format=format_name,duration:stream=codec_type,codec_name,width,height","-of","json",str(source)],
                capture_output=True,timeout=20,check=True)
            info=json.loads(probe.stdout)
            duration=float(info.get("format",{}).get("duration",0))
            videos=[s for s in info.get("streams",[]) if s.get("codec_type")=="video"]
            if not videos or not math.isfinite(duration) or not 0<duration<=300:
                raise HTTPException(415,"Video phải có hình ảnh, thời lượng tối đa 5 phút.")
            if len(videos)!=1 or not 0<videos[0].get("width",0)<=4096 or not 0<videos[0].get("height",0)<=4096:
                raise HTTPException(415,"Video chỉ được có một luồng hình, độ phân giải tối đa 4096px mỗi chiều.")
            subprocess.run(["ffmpeg","-nostdin","-v","error","-xerror","-protocol_whitelist","file,pipe",
                "-format_whitelist","mov,matroska,webm","-i",str(source),"-map","0:v:0","-map","0:a:0?",
                "-map_metadata","-1","-map_chapters","-1","-vf","scale='min(1280,iw)':'min(1280,ih)':force_original_aspect_ratio=decrease:force_divisible_by=2,setsar=1",
                "-c:v","libx264","-preset","veryfast","-crf","24","-threads","2","-pix_fmt","yuv420p",
                "-r","30","-c:a","aac","-b:a","128k","-t","300","-fs",str(MAX_VIDEO_BYTES),
                "-movflags","+faststart",str(target)],capture_output=True,timeout=180,check=True)
            if not target.is_file() or target.stat().st_size>=MAX_VIDEO_BYTES:
                raise HTTPException(413,"Video sau xử lý vượt quá 50 MB.")
            return target.read_bytes(),"mp4"
        except (subprocess.CalledProcessError,ValueError,KeyError):
            raise HTTPException(415,"Tệp không phải video MP4/WebM hợp lệ hoặc video bị hỏng.") from None
        except subprocess.TimeoutExpired:
            raise HTTPException(422,"Video xử lý quá lâu; hãy chọn video ngắn hoặc độ phân giải thấp hơn.") from None
