

import argparse
import configparser
import math
import random
import sys
import time
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QTimer, QPoint, QObject, Signal
from PySide6.QtGui import QPainter, QColor, QBrush, QPainterPath, QAction
from PySide6.QtWidgets import QApplication, QWidget, QMenu

try:
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False

CONFIG_DIR = Path.home() / ".config" / "deskpenguin"
CONFIG_FILE = CONFIG_DIR / "config.ini"

WIDTH, HEIGHT = 120, 145
FRAME_MS = 40  # ~25 fps

BODY = QColor("#2e2e33")
BELLY = QColor("#fbfaf6")
BEAK = QColor("#f0a244")
BLUSH = QColor("#f3a6a6")
KEY_BG = QColor("#4a4a52")
KEY_TOP = QColor("#e9e9ee")

WALK_SPEED = 1.1          
TYPING_HOLD_SECONDS = 1.2  


class KeyBridge(QObject):
    """Relays keystrokes from the background listener thread to the Qt main thread."""
    pressed = Signal()


class PenguinWidget(QWidget):
    def __init__(self, start_pos: Optional[QPoint]):
        super().__init__()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(WIDTH, HEIGHT)

        self._drag_offset = None
        self._tick = 0
        self._blink_at = random.randint(90, 150)
        self._blinking = 0

        # walking state
        self._state = "idle"          # "idle" or "walking"
        self._facing = 1              # 1 = right, -1 = left
        self._target_x = None
        self._state_until = time.time() + random.uniform(2, 4)

        # typing state
        self._last_keypress = 0.0
        self._key_bridge = KeyBridge()
        self._key_bridge.pressed.connect(self._on_keypress)
        self._listener = None
        if PYNPUT_AVAILABLE:
            self._listener = keyboard.Listener(on_press=self._on_raw_keypress)
            self._listener.daemon = True
            self._listener.start()

        if start_pos is not None:
            self.move(start_pos)
        else:
            self._restore_position()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_tick)
        self.timer.start(FRAME_MS)

    # ---------- typing detection ----------

    def _on_raw_keypress(self, key):
        # runs on the pynput background thread — just hand off to Qt safely
        self._key_bridge.pressed.emit()

    def _on_keypress(self):
        self._last_keypress = time.time()

    def _is_typing(self):
        return (time.time() - self._last_keypress) < TYPING_HOLD_SECONDS

    # ---------- animation / movement ----------

    def _on_tick(self):
        self._tick += 1
        now = time.time()

        # gentle occasional blink
        if self._blinking > 0:
            self._blinking -= 1
        elif self._tick % self._blink_at == 0:
            self._blinking = 5

        # don't wander while the user is typing or dragging — sit and watch the keyboard
        if self._is_typing() or self._drag_offset is not None:
            self._state = "idle"
        else:
            self._update_walk_state(now)
            if self._state == "walking":
                self._step_towards_target()

        self.update()

    def _update_walk_state(self, now):
        if now < self._state_until:
            return

        screen = QApplication.primaryScreen().availableGeometry()
        if self._state == "idle":
            self._state = "walking"
            margin = 20
            self._target_x = random.randint(screen.left() + margin, screen.right() - WIDTH - margin)
            self._facing = 1 if self._target_x > self.x() else -1
            self._state_until = now + random.uniform(3, 7)
        else:
            self._state = "idle"
            self._state_until = now + random.uniform(2, 5)

    def _step_towards_target(self):
        if self._target_x is None:
            return
        x = self.x()
        if abs(x - self._target_x) <= WALK_SPEED:
            self.move(self._target_x, self.y())
            self._state = "idle"
            self._state_until = time.time() + random.uniform(2, 5)
            return
        step = WALK_SPEED if self._target_x > x else -WALK_SPEED
        self.move(int(x + step), self.y())

    # ---------- drawing ----------

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        walking = self._state == "walking" and self._drag_offset is None
        typing = self._is_typing()

        # gentle waddle bob — small and calm, not exaggerated
        bob = math.sin(self._tick * 0.35) * (2.2 if walking else 0.6)

        p.save()
        p.translate(WIDTH / 2, HEIGHT / 2 + bob)
        if self._facing < 0:
            p.scale(-1, 1)
        p.translate(-WIDTH / 2, -HEIGHT / 2)

        cx = WIDTH / 2
        body_top = 42
        body_w, body_h = 62, 74
        head_r = 24
        head_cy = body_top - 6

        # feet — small alternating step while walking, still while idle
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(BEAK))
        foot_lift = 3 if (walking and (self._tick // 6) % 2 == 0) else 0
        foot_y = body_top + body_h - 6
        p.drawEllipse(int(cx - 22), int(foot_y - foot_lift), 16, 8)
        p.drawEllipse(int(cx + 6), int(foot_y - (0 if foot_lift else 3)), 16, 8)

        # body
        p.setBrush(QBrush(BODY))
        p.drawRoundedRect(int(cx - body_w / 2), int(body_top), int(body_w), int(body_h), 30, 30)

        # belly
        p.setBrush(QBrush(BELLY))
        belly_w, belly_h = body_w * 0.6, body_h * 0.75
        p.drawEllipse(int(cx - belly_w / 2), int(body_top + body_h * 0.15), int(belly_w), int(belly_h))

        # wings — small, resting against the body, only a very slight sway
        wing_sway = math.sin(self._tick * 0.12) * 3
        p.setBrush(QBrush(BODY))
        left_wing = QPainterPath()
        lw_x, lw_y = cx - body_w / 2 + 4, body_top + 18
        left_wing.moveTo(lw_x, lw_y)
        left_wing.quadTo(lw_x - 14 + wing_sway, lw_y + 20, lw_x - 2, lw_y + 36)
        left_wing.quadTo(lw_x + 8, lw_y + 20, lw_x, lw_y)
        left_wing.closeSubpath()
        p.drawPath(left_wing)

        right_wing = QPainterPath()
        rw_x, rw_y = cx + body_w / 2 - 4, body_top + 18
        right_wing.moveTo(rw_x, rw_y)
        right_wing.quadTo(rw_x + 14 - wing_sway, rw_y + 20, rw_x + 2, rw_y + 36)
        right_wing.quadTo(rw_x - 8, rw_y + 20, rw_x, rw_y)
        right_wing.closeSubpath()
        p.drawPath(right_wing)

        # head
        p.setBrush(QBrush(BODY))
        p.drawEllipse(int(cx - head_r), int(head_cy - head_r), int(head_r * 2), int(head_r * 2))

        # face patch
        p.setBrush(QBrush(BELLY))
        face_w, face_h = head_r * 1.25, head_r * 1.4
        p.drawEllipse(int(cx - face_w / 2), int(head_cy - face_h / 2 + 3), int(face_w), int(face_h))

        # blush — this is what makes it read as "cute"
        p.setBrush(QBrush(BLUSH))
        p.setOpacity(0.55)
        p.drawEllipse(int(cx - head_r * 0.85), int(head_cy + 3), 9, 6)
        p.drawEllipse(int(cx + head_r * 0.35), int(head_cy + 3), 9, 6)
        p.setOpacity(1.0)

        # big soft eyes
        eye_y = head_cy - 2
        eye_dx = 7
        eye_w = 6
        eye_h = 6 if self._blinking == 0 else 1
        p.setBrush(QBrush(QColor("#1a1a1a")))
        p.drawEllipse(int(cx - eye_dx - eye_w / 2), int(eye_y - eye_h / 2), eye_w, eye_h)
        p.drawEllipse(int(cx + eye_dx - eye_w / 2), int(eye_y - eye_h / 2), eye_w, eye_h)
        if self._blinking == 0:
            p.setBrush(QBrush(QColor("#ffffff")))
            p.drawEllipse(int(cx - eye_dx - 1), int(eye_y - 2), 2, 2)
            p.drawEllipse(int(cx + eye_dx - 1), int(eye_y - 2), 2, 2)

        # beak
        p.setBrush(QBrush(BEAK))
        beak = QPainterPath()
        beak.moveTo(cx - 6, head_cy + 6)
        beak.lineTo(cx + 6, head_cy + 6)
        beak.lineTo(cx, head_cy + 13)
        beak.closeSubpath()
        p.drawPath(beak)

        p.restore()

        # tiny keyboard prop — drawn in screen space (not mirrored) so it always reads upright
        if typing:
            self._draw_keyboard_prop(p)

        p.end()

    def _draw_keyboard_prop(self, p: QPainter):
        kb_w, kb_h = 46, 20
        kb_x = WIDTH / 2 - kb_w / 2
        kb_y = HEIGHT - 30

        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(KEY_BG))
        p.drawRoundedRect(int(kb_x), int(kb_y), kb_w, kb_h, 4, 4)

        # a few little keys, with a "pressed" one that cycles to look like typing
        cols, rows = 6, 2
        pad = 3
        key_w = (kb_w - pad * (cols + 1)) / cols
        key_h = (kb_h - pad * (rows + 1)) / rows
        active_index = (self._tick // 3) % (cols * rows)

        idx = 0
        for r in range(rows):
            for c in range(cols):
                kx = kb_x + pad + c * (key_w + pad)
                ky = kb_y + pad + r * (key_h + pad)
                pressed = idx == active_index
                p.setBrush(QBrush(KEY_TOP if not pressed else BEAK))
                p.drawRoundedRect(int(kx), int(ky + (1 if pressed else 0)), int(key_w), int(key_h), 2, 2)
                idx += 1

    # ---------- dragging ----------

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None:
            self.move(event.globalPosition().toPoint() - self._drag_offset)

    def mouseReleaseEvent(self, event):
        self._drag_offset = None
        self._state_until = time.time() + random.uniform(2, 4)

    # ---------- context menu ----------

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)
        menu.exec(event.globalPos())

    def _quit(self):
        self._save_position()
        if self._listener is not None:
            self._listener.stop()
        QApplication.instance().quit()

    def closeEvent(self, event):
        self._save_position()
        if self._listener is not None:
            self._listener.stop()
        super().closeEvent(event)

    # ---------- persistence ----------

    def _save_position(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        cfg = configparser.ConfigParser()
        cfg["position"] = {"x": str(self.x()), "y": str(self.y())}
        with open(CONFIG_FILE, "w") as f:
            cfg.write(f)

    def _restore_position(self):
        if CONFIG_FILE.exists():
            cfg = configparser.ConfigParser()
            cfg.read(CONFIG_FILE)
            if "position" in cfg:
                x = cfg["position"].getint("x", fallback=None)
                y = cfg["position"].getint("y", fallback=None)
                if x is not None and y is not None:
                    self.move(x, y)
                    return

        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.right() - WIDTH - 40, screen.bottom() - HEIGHT - 40)


def main():
    parser = argparse.ArgumentParser(description="A cute, walking, typing-aware desktop penguin.")
    parser.add_argument("--pos", nargs=2, type=int, metavar=("X", "Y"), help="starting screen position")
    args = parser.parse_args()

    if not PYNPUT_AVAILABLE:
        print("Note: 'pynput' isn't installed, so the penguin won't react to typing.")
        print("Install it with: pip install pynput")

    app = QApplication(sys.argv)
    start_pos = QPoint(*args.pos) if args.pos else None
    penguin = PenguinWidget(start_pos=start_pos)
    penguin.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()