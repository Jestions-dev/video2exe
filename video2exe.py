#!/usr/bin/env python3
"""
video2exe — Restore original files from 1:1 color video

Reverse tool for exe2video. Uses FFmpeg to decode video pixel data,
reads the embedded size trailer to truncate precisely, and restores
the original binary file intact.
"""

import argparse
import hashlib
import shutil
import struct
import subprocess
import sys
from pathlib import Path

from tqdm import tqdm


def find_ffmpeg():
    """Locate ffmpeg executable. Checks PATH first, then common locations."""
    path = shutil.which('ffmpeg')
    if path:
        return Path(path)
    candidates = [
        r'C:\ffmpeg\bin\ffmpeg.exe',
        r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',
    ]
    for p in candidates:
        if Path(p).exists():
            return Path(p)
    return None


def get_video_info(ffprobe: Path, video_path: Path):
    """Use ffprobe to get video width, height, and frame count."""
    cmd = [
        str(ffprobe), '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height,nb_frames',
        '-of', 'csv=p=0',
        str(video_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not result.stdout.strip():
        return None, None, None

    parts = result.stdout.strip().split(',')
    if len(parts) != 3:
        return None, None, None

    try:
        width = int(parts[0])
        height = int(parts[1])
        nb_frames = int(parts[2])
        return width, height, nb_frames
    except ValueError:
        return None, None, None


def video_to_exe(input_path: Path, output_path: Path, md5_compare: str | None = None):
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        print("[ERROR] FFmpeg not found. Please install FFmpeg and try again.")
        print("  Download: https://ffmpeg.org/download.html")
        print("  Or place it at C:\\ffmpeg\\bin\\ffmpeg.exe")
        sys.exit(1)

    ffprobe = ffmpeg.parent / 'ffprobe.exe'
    if not ffprobe.exists():
        ffprobe = Path(shutil.which('ffprobe') or '')
    if not ffprobe.exists():
        print("[ERROR] ffprobe not found (usually in the same directory as ffmpeg)")
        sys.exit(1)

    print(f"  FFmpeg: {ffmpeg}")

    # ── 1. Read original file size from trailer ──────────
    try:
        with open(input_path, 'rb') as f:
            f.seek(-4, 2)
            size_bytes = f.read(4)
        original_size = struct.unpack('<I', size_bytes)[0]
    except (OSError, struct.error):
        print("\n[ERROR] Cannot read file size trailer.")
        print("  The video may not have been created by exe2video, or the file is corrupted.")
        sys.exit(1)

    if original_size == 0:
        print("[ERROR] Recorded file size is 0. Video may be invalid.")
        sys.exit(1)

    print(f"[1/3] Original file size: {original_size:,} bytes "
          f"({original_size / 1024 / 1024:.2f} MB)")

    # ── 2. Get video info and extract pixel data ─────────
    width, height, total_frames = get_video_info(ffprobe, input_path)
    if width is None:
        print("\n[ERROR] Cannot read video info. The file may not be a valid video.")
        sys.exit(1)

    if width != height:
        print(f"[WARNING] Video is not square ({width}x{height}), "
              f"attempting extraction anyway...")

    print(f"[2/3] Video: {width}x{height}, {total_frames} frames")

    decode_cmd = [
        str(ffmpeg), '-i', str(input_path),
        '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-vcodec', 'rawvideo',
        '-',
    ]
    proc = subprocess.Popen(
        decode_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )

    frame_bytes_size = width * height * 3
    all_bytes = bytearray()

    for _ in tqdm(range(total_frames), desc="Extracting", unit="frame"):
        raw = proc.stdout.read(frame_bytes_size)
        if len(raw) < frame_bytes_size:
            break
        all_bytes.extend(raw)

    proc.stdout.close()
    proc.wait()

    # ── 3. Truncate and write ────────────────────────────
    print(f"[3/3] Writing output file...")
    if original_size > len(all_bytes):
        print(f"\n[ERROR] Insufficient video data")
        print(f"  Required: {original_size:,} bytes")
        print(f"  Available: {len(all_bytes):,} bytes")
        print(f"  Missing: {original_size - len(all_bytes):,} bytes")
        print("  The video may be incomplete or was not created by exe2video.")
        sys.exit(1)

    exe_data = bytes(all_bytes[:original_size])

    with open(output_path, 'wb') as f:
        f.write(exe_data)

    # ── Result ───────────────────────────────────────────
    actual_md5 = hashlib.md5(exe_data).hexdigest()

    print(f"\n{'=' * 55}")
    print(f"  Restore complete!")
    print(f"  Input video:  {input_path}")
    print(f"  Output file:  {output_path}")
    print(f"  File size:    {len(exe_data):,} bytes")

    if md5_compare:
        if actual_md5 == md5_compare.lower():
            print(f"  MD5 check:    [PASS]")
        else:
            print(f"  MD5 check:    [FAIL]")
            print(f"    Expected: {md5_compare.lower()}")
    print(f"  MD5:          {actual_md5}")
    print(f"{'=' * 55}")


def main():
    parser = argparse.ArgumentParser(
        description='Restore original files from 1:1 color lossless video',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  video2exe -i output.mp4 -o restored.exe
  video2exe -i output.mp4 -o restored.exe --md5 abc123...
        """,
    )
    parser.add_argument('-i', required=True, type=Path,
                        help='Input video file path')
    parser.add_argument('-o', required=True, type=Path,
                        help='Output restored file path')
    parser.add_argument('--md5', type=str, default=None,
                        help='Expected MD5 hash for verification')

    args = parser.parse_args()

    if not args.i.exists():
        print(f"[ERROR] Input file not found: {args.i}")
        sys.exit(1)

    video_to_exe(args.i.resolve(), args.o.resolve(), args.md5)


if __name__ == '__main__':
    main()
