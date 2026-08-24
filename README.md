# DeskCat 🐈

A tiny animated cat that lives on your desktop — frameless, always-on-top,
and draggable anywhere on screen. No image assets required: the cat is
drawn live with Qt's `QPainter`, so it's a single lightweight Python file.

Inspired by the idea behind [yumiaura/myCat](https://github.com/yumiaura/myCat),
built from scratch as an original implementation.

## Features

- Frameless, transparent, always-on-top overlay window
- Idle animation: blinking eyes + a gently swaying tail
- Left-click and drag to move the cat anywhere
- Right-click for a menu: change color, quit
- Remembers its last position between runs (`~/.config/deskcat/config.ini`)

## Install & run

```bash
pip install -r requirements.txt
python main.py
```

### Options

```bash
python main.py --pos 800 400        # start at a specific screen position
python main.py --color "#d18a3f"    # start with a ginger cat
```

## Roadmap ideas

- [ ] Swap the procedural drawing for real sprite-sheet skins (like the
      original myCat's GIF-based skins)
- [ ] Add a reminder feature — cat carries a little banner across the screen
- [ ] Package as a standalone `.exe` / `.app` with PyInstaller
- [ ] Publish to PyPI so it installs with `pip install deskcat`
- [ ] Add a simple local-LLM chat mode via Ollama, like the original project

## License

MIT