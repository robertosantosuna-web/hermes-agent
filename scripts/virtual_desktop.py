#!/usr/bin/python3
"""
VIRTUAL KEYBOARD & MOUSE CONTROLLER
====================================
Controle total do desktop para operação remota/autônoma.
Suporta Wayland + XWayland com múltiplos backends.

Uso:
  python3 virtual_desktop.py type "texto para digitar"
  python3 virtual_desktop.py move 500 300
  python3 virtual_desktop.py click [left|right|middle]
  python3 virtual_desktop.py drag x1 y1 x2 y2
  python3 virtual_desktop.py key enter
  python3 virtual_desktop.py screenshot [path]
  python3 virtual_desktop.py screen_info
  python3 virtual_desktop.py hotkey ctrl+c
  python3 virtual_desktop.py scroll 3 [up|down]
  python3 virtual_desktop.py position
  python3 virtual_desktop.py click_at_text "Search"

Backends (auto-detected):
  - pynput: keyboard + mouse (XWayland)
  - pyautogui: mouse + keyboard + screenshot fallback
  - ydotool: kernel-level uinput (Wayland safe)
  - wtype: Wayland-native text input
  - xdotool: X11 window control
"""

import sys
import os
import time
import subprocess
import argparse


class DesktopController:
    """Controlador unificado de desktop com fallback automático."""

    def __init__(self):
        self.display = os.environ.get('DISPLAY', ':0')
        self.wayland = 'WAYLAND_DISPLAY' in os.environ
        self._init_backends()
        print(f"[virtual_desktop] Display: {'Wayland' if self.wayland else 'X11'} | Screen: {self.screen_size()}", file=sys.stderr)

    def _init_backends(self):
        """Verifica backends disponíveis."""
        self.has_pynput = False
        self.has_pyautogui = False
        self.has_ydotool = False
        self.has_xdotool = False
        self.has_wtype = False

        try:
            from pynput.keyboard import Controller as KbCtrl
            from pynput.mouse import Controller as MsCtrl
            self.kb = KbCtrl()
            self.ms = MsCtrl()
            self.has_pynput = True
        except:
            pass

        try:
            import pyautogui
            pyautogui.FAILSAFE = False
            self.pyautogui = pyautogui
            self.has_pyautogui = True
        except:
            pass

        self.has_ydotool = subprocess.run(['which', 'ydotool'],
                                          capture_output=True).returncode == 0
        self.has_xdotool = subprocess.run(['which', 'xdotool'],
                                          capture_output=True).returncode == 0
        self.has_wtype = subprocess.run(['which', 'wtype'],
                                        capture_output=True).returncode == 0

    # ═══════════════════════════════════════════
    # INFORMAÇÕES DA TELA
    # ═══════════════════════════════════════════

    def screen_size(self):
        try:
            return self.pyautogui.size()
        except:
            return (1920, 1080)

    def mouse_position(self):
        try:
            return self.pyautogui.position()
        except:
            try:
                return self.ms.position
            except:
                return (0, 0)

    def screen_info(self):
        size = self.screen_size()
        pos = self.mouse_position()
        print(f"Screen: {size.width}x{size.height}")
        print(f"Mouse:  x={pos.x}, y={pos.y}")
        print(f"Display: {'Wayland' if self.wayland else 'X11'} (DISPLAY={self.display})")
        print(f"Backends: pynput={'✅' if self.has_pynput else '❌'} "
              f"pyautogui={'✅' if self.has_pyautogui else '❌'} "
              f"ydotool={'✅' if self.has_ydotool else '❌'} "
              f"wtype={'✅' if self.has_wtype else '❌'}")

    # ═══════════════════════════════════════════
    # MOUSE
    # ═══════════════════════════════════════════

    def move_mouse(self, x, y, smooth=False):
        """Move o mouse para posição (x, y)."""
        try:
            if smooth and self.has_pyautogui:
                self.pyautogui.moveTo(x, y, duration=0.3)
            elif self.has_pyautogui:
                self.pyautogui.moveTo(x, y, duration=0.1)
            else:
                self.ms.position = (x, y)
            print(f"✅ Mouse → ({x}, {y})")
        except Exception as e:
            # Fallback: ydotool
            if self.has_ydotool:
                subprocess.run(['ydotool', 'mousemove', '--absolute',
                                str(x), str(y)], timeout=2)
                print(f"✅ ydotool mouse → ({x}, {y})")
            else:
                print(f"❌ Mouse move failed: {e}")

    def click(self, button='left', x=None, y=None):
        """Clique do mouse."""
        if x is not None and y is not None:
            self.move_mouse(x, y)
            time.sleep(0.1)

        try:
            if self.has_pynput:
                from pynput.mouse import Button
                btn_map = {'left': Button.left, 'right': Button.right,
                           'middle': Button.middle}
                self.ms.click(btn_map.get(button, Button.left))
            elif self.has_pyautogui:
                self.pyautogui.click(button=button)
            print(f"✅ Click {button} @ {self.mouse_position()}")
        except Exception as e:
            if self.has_ydotool:
                btn_map = {'left': '0x00', 'right': '0x01', 'middle': '0x02'}
                subprocess.run(['ydotool', 'click', btn_map.get(button, '0x00')],
                               timeout=2)
                print(f"✅ ydotool click {button}")
            else:
                print(f"❌ Click failed: {e}")

    def double_click(self, x=None, y=None):
        if x is not None and y is not None:
            self.move_mouse(x, y)
            time.sleep(0.1)
        try:
            if self.has_pyautogui:
                self.pyautogui.doubleClick()
            else:
                self.click(); time.sleep(0.05); self.click()
            print(f"✅ Double-click @ {self.mouse_position()}")
        except Exception as e:
            print(f"❌ Double-click failed: {e}")

    def drag(self, x1, y1, x2, y2):
        """Arrasta de (x1,y1) até (x2,y2)."""
        self.move_mouse(x1, y1)
        time.sleep(0.2)
        try:
            if self.has_pyautogui:
                self.pyautogui.mouseDown()
                self.pyautogui.moveTo(x2, y2, duration=1.0)
                self.pyautogui.mouseUp()
            elif self.has_pynput:
                from pynput.mouse import Button
                self.ms.press(Button.left)
                time.sleep(0.1)
                self.ms.position = (x2, y2)
                time.sleep(0.1)
                self.ms.release(Button.left)
            print(f"✅ Drag ({x1},{y1}) → ({x2},{y2})")
        except Exception as e:
            print(f"❌ Drag failed: {e}")

    def scroll(self, clicks, direction='down'):
        """Scroll do mouse."""
        amount = clicks if direction == 'up' else -clicks
        try:
            if self.has_pynput:
                self.ms.scroll(0, amount)
            elif self.has_pyautogui:
                self.pyautogui.scroll(amount)
            print(f"✅ Scroll {direction} ×{clicks}")
        except Exception as e:
            print(f"❌ Scroll failed: {e}")

    # ═══════════════════════════════════════════
    # TECLADO
    # ═══════════════════════════════════════════

    def type_text(self, text, interval=0.02):
        """Digita texto caractere por caractere."""
        try:
            if self.has_wtype and self.wayland:
                subprocess.run(['wtype', text], timeout=5)
            elif self.has_pynput:
                self.kb.type(text)
            elif self.has_pyautogui:
                self.pyautogui.typewrite(text, interval=interval)
            elif self.has_ydotool:
                subprocess.run(['ydotool', 'type', text], timeout=5)
            print(f"✅ Typed: '{text[:50]}{'...' if len(text)>50 else ''}'")
        except Exception as e:
            print(f"❌ Type failed: {e}")

    def press_key(self, key):
        """Pressiona uma tecla especial. Ex: enter, tab, escape, space, backspace, etc."""
        # Mapeamento de nomes comuns
        key_map = {
            'enter': 'Return',
            'return': 'Return',
            'tab': 'Tab',
            'escape': 'Escape',
            'esc': 'Escape',
            'space': 'space',
            'backspace': 'BackSpace',
            'delete': 'Delete',
            'up': 'Up',
            'down': 'Down',
            'left': 'Left',
            'right': 'Right',
            'home': 'Home',
            'end': 'End',
            'page_up': 'Page_Up',
            'page_down': 'Page_Down',
            'f1': 'F1', 'f2': 'F2', 'f3': 'F3', 'f4': 'F4',
            'f5': 'F5', 'f6': 'F6', 'f7': 'F7', 'f8': 'F8',
            'f9': 'F9', 'f10': 'F10', 'f11': 'F11', 'f12': 'F12',
        }
        mapped = key_map.get(key.lower(), key)

        try:
            if self.has_pynput:
                from pynput.keyboard import Key
                k = getattr(Key, mapped.lower(), mapped)
                self.kb.press(k)
                self.kb.release(k)
            elif self.has_pyautogui:
                self.pyautogui.press(key.lower())
            elif self.has_ydotool:
                subprocess.run(['ydotool', 'key', mapped], timeout=2)
            print(f"✅ Key: {key}")
        except Exception as e:
            print(f"❌ Key press failed: {e}")

    def hotkey(self, *keys):
        """Combinação de teclas. Ex: ctrl+c, alt+tab, ctrl+shift+t"""
        try:
            if self.has_pyautogui:
                self.pyautogui.hotkey(*keys)
            elif self.has_pynput:
                from pynput.keyboard import Key, Controller
                kb = Controller()
                modifiers = {'ctrl': Key.ctrl, 'alt': Key.alt,
                             'shift': Key.shift, 'cmd': Key.cmd,
                             'super': Key.cmd, 'win': Key.cmd}
                pressed = []
                for k in keys:
                    mod = modifiers.get(k.lower())
                    if mod:
                        kb.press(mod)
                        pressed.append(mod)
                    else:
                        kb.press(k)
                        kb.release(k)
                for mod in reversed(pressed):
                    kb.release(mod)
            print(f"✅ Hotkey: {'+'.join(keys)}")
        except Exception as e:
            print(f"❌ Hotkey failed: {e}")

    # ═══════════════════════════════════════════
    # SCREENSHOT
    # ═══════════════════════════════════════════

    def screenshot(self, path=None):
        """Tira screenshot da tela."""
        if path is None:
            path = os.path.expanduser(f'~/.hermes/forex/screenshot_{int(time.time())}.png')

        try:
            if self.has_pyautogui:
                img = self.pyautogui.screenshot()
                img.save(path)
                print(f"✅ Screenshot: {path} ({img.size})")
                return path
        except Exception as e:
            print(f"pyautogui screenshot: {e}")

        # Fallback: gnome-screenshot via D-Bus
        try:
            subprocess.run(['gnome-screenshot', '-f', path], timeout=5)
            if os.path.exists(path):
                print(f"✅ gnome-screenshot: {path}")
                return path
        except:
            pass

        # Fallback: grim (Wayland)
        try:
            subprocess.run(['grim', path], timeout=5)
            if os.path.exists(path):
                print(f"✅ grim: {path}")
                return path
        except:
            pass

        # Fallback: import (ImageMagick)
        try:
            subprocess.run(['import', '-window', 'root', path], timeout=5)
            if os.path.exists(path):
                print(f"✅ import: {path}")
                return path
        except:
            pass

        print(f"❌ Screenshot failed (all methods)")
        return None

    # ═══════════════════════════════════════════
    # UTILITÁRIOS
    # ═══════════════════════════════════════════

    def click_at_text(self, search_text):
        """
        Tenta encontrar e clicar em um elemento de texto na tela.
        Usa OCR (tesseract) se disponível, ou busca por accessibility tree.
        """
        # Por enquanto: tenta usar accessibility via dbus
        try:
            result = subprocess.run(
                ['gdbus', 'call', '--session',
                 '--dest', 'org.gnome.Shell',
                 '--object-path', '/org/gnome/Shell',
                 '--method', 'org.gnome.Shell.FocusSearch',
                 search_text],
                capture_output=True, timeout=5
            )
            print(f"Accessibility search: {result.stdout[:200]}")
        except:
            print(f"⚠️ Accessibility search not available for '{search_text}'")

    def run_app(self, app_name):
        """Abre um aplicativo pelo nome."""
        subprocess.Popen([app_name], stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
        print(f"✅ App launched: {app_name}")

    def open_url(self, url):
        """Abre URL no navegador padrão."""
        subprocess.Popen(['xdg-open', url], stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
        print(f"✅ URL opened: {url}")


# ═══════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Virtual Desktop Controller')
    sub = parser.add_subparsers(dest='command')

    sub.add_parser('screen_info', help='Mostra informações da tela')
    sub.add_parser('position', help='Mostra posição do mouse')

    p = sub.add_parser('move', help='Move o mouse')
    p.add_argument('x', type=int)
    p.add_argument('y', type=int)

    p = sub.add_parser('click', help='Clique do mouse')
    p.add_argument('button', nargs='?', default='left',
                   choices=['left', 'right', 'middle'])
    p.add_argument('--x', type=int, default=None)
    p.add_argument('--y', type=int, default=None)

    p = sub.add_parser('dblclick', help='Duplo clique')

    p = sub.add_parser('drag', help='Arrastar')
    p.add_argument('x1', type=int); p.add_argument('y1', type=int)
    p.add_argument('x2', type=int); p.add_argument('y2', type=int)

    p = sub.add_parser('scroll', help='Scroll')
    p.add_argument('clicks', type=int); p.add_argument('direction', nargs='?', default='down')

    p = sub.add_parser('type', help='Digitar texto')
    p.add_argument('text', type=str)

    p = sub.add_parser('key', help='Pressionar tecla')
    p.add_argument('key_name', type=str)

    p = sub.add_parser('hotkey', help='Combinação de teclas')
    p.add_argument('keys', nargs='+', type=str)

    p = sub.add_parser('screenshot', help='Screenshot')
    p.add_argument('path', nargs='?', default=None)

    p = sub.add_parser('run', help='Abrir app')
    p.add_argument('app', type=str)

    p = sub.add_parser('open_url', help='Abrir URL')
    p.add_argument('url', type=str)

    args = parser.parse_args()
    dc = DesktopController()

    if args.command == 'screen_info': dc.screen_info()
    elif args.command == 'position': print(f"Mouse: {dc.mouse_position()}")
    elif args.command == 'move': dc.move_mouse(args.x, args.y)
    elif args.command == 'click': dc.click(args.button, args.x, args.y)
    elif args.command == 'dblclick': dc.double_click()
    elif args.command == 'drag': dc.drag(args.x1, args.y1, args.x2, args.y2)
    elif args.command == 'scroll': dc.scroll(args.clicks, args.direction)
    elif args.command == 'type': dc.type_text(args.text)
    elif args.command == 'key': dc.press_key(args.key_name)
    elif args.command == 'hotkey': dc.hotkey(*args.keys)
    elif args.command == 'screenshot': dc.screenshot(args.path)
    elif args.command == 'run': dc.run_app(args.app)
    elif args.command == 'open_url': dc.open_url(args.url)
    else:
        parser.print_help()
