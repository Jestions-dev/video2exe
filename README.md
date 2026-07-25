# video2exe

Restore original files from 1:1 color lossless video.

Uses FFmpeg to decode video pixel data and reconstruct the original binary file
with byte-level precision.

## Requirements (source only)

- Windows 10/11 64-bit
- Python 3.8+
- [FFmpeg](https://ffmpeg.org/download.html) in PATH or at `C:\ffmpeg\bin\`

> The pre-built EXE on the [Releases](https://github.com/Jestions-dev/video2exe/releases) page
> bundles FFmpeg — download and run, no installation needed.

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

## Note

This tool only restores files from videos created by the companion converter.
Regular video files do not contain the embedded data structure needed for restoration.
