# video2exe

Restore original files from 1:1 color lossless video.

---

## Quick start (EXE)

1. Download `video2exe.exe` from [Releases](https://github.com/Jestions-dev/video2exe/releases)
2. Open a terminal in the folder containing your video file
3. Run:

```
video2exe -i video.mp4 -o restored.exe
```

No Python or FFmpeg installation needed — everything is bundled.

With MD5 verification:

```
video2exe -i video.mp4 -o restored.exe --md5 abc123...
```

---

## From source

Requirements: Python 3.8+, [FFmpeg](https://ffmpeg.org/download.html) in PATH or at `C:\ffmpeg\bin\`.

```bash
pip install -r requirements.txt
python video2exe.py -i video.mp4 -o restored.exe
```

---

## Note

This tool only restores files from videos created by the companion converter.
Regular video files do not contain the embedded data structure needed for restoration.
