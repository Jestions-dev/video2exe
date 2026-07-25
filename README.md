# video2exe

Restore original files from 1:1 color lossless video.

Uses FFmpeg to decode video pixel data and reconstruct the original binary file
with byte-level precision.

## Requirements

- Windows 10/11 64-bit
- [FFmpeg](https://ffmpeg.org/download.html) (includes ffprobe)

Make sure FFmpeg is in your PATH, or place it at `C:\ffmpeg\bin\`.

## Install

```bash
pip install -r requirements.txt
```

## Usage

```bash
python video2exe.py -i <video> -o <output>

# With MD5 verification
python video2exe.py -i video.mp4 -o restored.exe --md5 abc123...
```

## Build standalone EXE (optional)

A pre-built EXE is available on the [Releases](https://github.com/Jestions-dev/video2exe/releases) page.
If you prefer to build it yourself:

```bash
pip install pyinstaller
python -m PyInstaller --onefile --console --name video2exe video2exe.py
```

The EXE will be in the `dist/` folder.

## Note

This tool only restores files from videos created by the companion converter.
Regular video files do not contain the embedded data structure needed for restoration.
