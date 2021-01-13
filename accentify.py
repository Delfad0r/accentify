#! /usr/bin/env python3

import argparse
from pynput import keyboard
import pyperclip
import sys


ACUTE_ACCENTS = 'áéíóú'
GRAVE_ACCENTS = 'àèìòù'

class MultipleHotKeys(keyboard.Listener):
    def __init__(self, hotkeys, *args, **kwargs):
        self._hotkeys = [(set(keyboard.HotKey.parse(s)), f) for s, f in hotkeys.items()]
        self._default = (lambda: None)
        self._state = set()
        super(MultipleHotKeys, self).__init__(
            on_press = self._on_press,
            on_release = self._on_release,
            *args, **kwargs)
    def _on_press(self, key):
        self._state.add(key)
        for h, f in self._hotkeys:
            if h == self._state:
                C = keyboard.Controller()
                print(C.shift_pressed)
                for k in h:
                    C.release(k)
                f()
                break
    def _on_release(self, key):
        self._state = set()

def press_combo(C, s):
    keys = keyboard.HotKey.parse(s)
    for k in keys:
        C.press(k)
    for k in reversed(keys):
        C.release(k)

def replace_last_char(f):
    C = keyboard.Controller()
    press_combo(C, '<shift>+<left>')
    old = pyperclip.paste()
    press_combo(C, '<ctrl>+c')
    a = pyperclip.paste()[-1]
    pyperclip.copy(old)
    b = f(a.lower())
    if a.isupper():
        b = b.upper()
    C.type(b)


def run(shortcut1, shortcut2):
    def replace(c, acute):
        for i, a, g, n in zip(range(5), ACUTE_ACCENTS, GRAVE_ACCENTS, 'aeiou'):
            if c == a or c == g:
                return 'aeiou'[i]
            if c == n:
                return a if acute else g
        return c
    repl1 = lambda: replace_last_char(lambda c: replace(c, False))
    repl2 = lambda: replace_last_char(lambda c: replace(c, True))
    try:
        with MultipleHotKeys({ shortcut1 : repl1, shortcut2 : repl2 }) as ghk:
            ghk.join()
    except Exception as E:
        print(str(E))
        C = keyboard.Controller()
        for k in [keyboard.Key.shift, keyboard.Key.ctrl, keyboard.Key.alt]:
            C.release(k)

def run_test():
    def print_key(k):
        try:
            print(f'<{k.name}>')
        except AttributeError:
            print(k)
    with keyboard.Listener(on_press = lambda k: print_key(k)) as listener:
        listener.join()

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('shortcuts', nargs = '*', type = str)
    parser.add_argument('--test', '-t', action = 'store_true')
    args = parser.parse_args()
    if args.shortcuts:
        if args.test:
            parser.error('shortcuts and --test are mutually exclusive')
        if len(args.shortcuts) != 2:
            parser.error('neex exactly two shortcuts')
    else:
        if not args.test:
            parser.error('no shortcuts provided')
    return args

if __name__ == '__main__':
    args = parse_args()
    if args.shortcuts:
        run(*args.shortcuts)
    elif args.test:
        run_test()
