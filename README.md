# video2exe

从 1:1 彩色视频中还原原始文件。使用 FFmpeg 解码视频像素数据，精确恢复原始二进制文件。

## 系统要求

- Windows 10/11 64-bit
- [FFmpeg](https://ffmpeg.org/download.html)（含 ffprobe）

## 安装

```bash
pip install -r requirements.txt
```

确保 FFmpeg 在 PATH 中，或放在 `C:\ffmpeg\bin\` 下。

## 使用

```bash
python video2exe.py -i <视频文件> -o <输出文件>

# 带 MD5 校验
python video2exe.py -i video.mp4 -o restored.exe --md5 abc123...
```

## 打包为独立 EXE

```bash
pip install pyinstaller
python -m PyInstaller --onefile --console --name video2exe video2exe.py
```

打包后的 EXE 在 `dist/` 目录，无需 Python 即可运行。

## 注意

本工具仅用于还原由配套转换工具生成的视频。普通视频文件不包含还原所需的数据结构。
