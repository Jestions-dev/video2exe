#!/usr/bin/env python3
"""
video2exe — 从 1:1 彩色视频中精确还原原始文件

是 exe2video 的逆向工具。使用 FFmpeg 解码视频，
根据文件末尾嵌入的大小信息精确截断，还原原始文件。
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
    """查找 ffmpeg，同时定位 ffprobe。"""
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
    """使用 ffprobe 获取视频的宽、高、帧数。"""
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
        print("[错误] 找不到 FFmpeg")
        sys.exit(1)
    ffprobe = ffmpeg.parent / 'ffprobe.exe'
    if not ffprobe.exists():
        ffprobe = Path(shutil.which('ffprobe') or '')
    if not ffprobe.exists():
        print("[错误] 找不到 ffprobe (通常与 ffmpeg 在同一目录)")
        sys.exit(1)

    print(f"  FFmpeg: {ffmpeg}")

    # ── 1. 读取原始文件大小 ──────────────────────────────
    try:
        with open(input_path, 'rb') as f:
            f.seek(-4, 2)
            size_bytes = f.read(4)
        original_size = struct.unpack('<I', size_bytes)[0]
    except (OSError, struct.error):
        print("\n[错误] 无法读取文件长度信息")
        print("  该视频可能不是由 exe2video 生成，或文件已损坏")
        sys.exit(1)

    if original_size == 0:
        print("[错误] 记录的文件大小为 0，视频可能无效")
        sys.exit(1)

    print(f"[1/3] 记录的文件大小: {original_size:,} 字节 ({original_size / 1024 / 1024:.2f} MB)")

    # ── 2. 获取视频参数并提取像素数据 ────────────────────
    width, height, total_frames = get_video_info(ffprobe, input_path)
    if width is None:
        print("\n[错误] 无法读取视频信息，文件可能不是有效视频")
        sys.exit(1)

    if width != height:
        print(f"[警告] 视频非正方形 ({width}x{height}), 但仍尝试提取...")

    print(f"[2/3] 视频信息: {width}x{height}, {total_frames} 帧")

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

    for _ in tqdm(range(total_frames), desc="提取进度", unit="帧"):
        raw = proc.stdout.read(frame_bytes_size)
        if len(raw) < frame_bytes_size:
            break
        all_bytes.extend(raw)

    proc.stdout.close()
    proc.wait()

    # ── 3. 截断 & 写出 ────────────────────────────────────
    print(f"[3/3] 还原文件...")
    if original_size > len(all_bytes):
        print(f"\n[错误] 视频数据不足")
        print(f"  需要: {original_size:,} 字节")
        print(f"  实际: {len(all_bytes):,} 字节")
        print(f"  差额: {original_size - len(all_bytes):,} 字节")
        print("  视频可能不完整或不是由 exe2video 生成")
        sys.exit(1)

    exe_data = bytes(all_bytes[:original_size])

    with open(output_path, 'wb') as f:
        f.write(exe_data)

    # ── 结果输出 ──────────────────────────────────────────
    actual_md5 = hashlib.md5(exe_data).hexdigest()

    print(f"\n{'=' * 55}")
    print(f"  还原完成!")
    print(f"  输入视频:    {input_path}")
    print(f"  输出文件:    {output_path}")
    print(f"  文件大小:    {len(exe_data):,} 字节")

    if md5_compare:
        if actual_md5 == md5_compare.lower():
            print(f"  MD5 校验:    [PASS] 一致")
        else:
            print(f"  MD5 校验:    [FAIL] 不一致!")
            print(f"    期望: {md5_compare.lower()}")
    print(f"  MD5:         {actual_md5}")
    print(f"{'=' * 55}")


def main():
    parser = argparse.ArgumentParser(
        description='从 1:1 视频中还原原始文件',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  video2exe -i output.mp4 -o restored.exe
  video2exe -i output.mp4 -o restored.exe --md5 abc123...
        """,
    )
    parser.add_argument('-i', required=True, type=Path,
                        help='输入视频文件路径')
    parser.add_argument('-o', required=True, type=Path,
                        help='输出还原文件路径')
    parser.add_argument('--md5', type=str, default=None,
                        help='原始文件 MD5, 用于校验还原结果')

    args = parser.parse_args()

    if not args.i.exists():
        print(f"[错误] 输入文件不存在: {args.i}")
        sys.exit(1)

    video_to_exe(args.i.resolve(), args.o.resolve(), args.md5)


if __name__ == '__main__':
    main()
