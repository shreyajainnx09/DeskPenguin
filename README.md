# DeskPenguin 🐧

A cute, gently animated penguin that lives on your desktop. It waddles around your screen on its own, blinks softly, and pops out a tiny keyboard to tap along whenever you're typing — then settles back down when you're done. Drag it anywhere with your mouse, and it remembers where you left it next time you open it.

Built with **Python** and **PySide6**.

Inspired by the idea behind [yumiaura/myCat](https://github.com/yumiaura/myCat), built from scratch as an original implementation.

## Download

🔗 **[Download DeskPenguin on itch.io](https://shreyajainnx.itch.io/deskpenguin)**

macOS only for now (Apple Silicon recommended).

## Features

- Idle waddling and blinking animations
- Reacts to typing with a tiny animated keyboard
- Drag-and-drop repositioning — remembers where you left it
- Lightweight desktop companion, runs quietly in the background

## Installation (from download)

1. Download `DeskPenguin.app.zip` from the [itch.io page](https://shreyajainnx.itch.io/deskpenguin) and unzip it.
2. Move `DeskPenguin.app` to your Applications folder (or run it directly).
3. Right-click the app and choose **Open** to bypass the unidentified-developer warning (only needed once).
4. To enable the typing reaction, go to **System Settings → Privacy & Security → Accessibility** and enable DeskPenguin.

## Running from source

```bash
git clone https://github.com/shreyajainnx09/DeskPenguin.git
cd DeskPenguin
pip install -r requirements.txt
python penguin_main.py
```

## Requirements

- Python 3.9+
- PySide6
- pynput (optional — for typing detection)

## License

LGPLv3
