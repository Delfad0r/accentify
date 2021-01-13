#! /usr/bin/env python3

import argparse
from collections import deque
import os
from pynput import keyboard
from pynput.keyboard import Key
import pyperclip
import subprocess
import sys
import time
import unicodedata


ACCENTS = ['aà', 'eèé', 'iì', 'oò', 'uù']

def normalize(w):
    return unicodedata.normalize('NFKD', w).encode('ascii', 'ignore').decode('ascii')


class MultipleHotKeys(keyboard.Listener):
    def __init__(self, hotkeys, *args, **kwargs):
        self._hotkeys = [(set(keyboard.HotKey.parse(s)), f) for s, f in hotkeys.items() if s != 'default']
        self._default = (lambda: None)
        if 'default' in hotkeys:
            self._default = hotkeys['default']
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
                for k in h:
                    C.release(k)
                f()
                break
        else:
            self._default()
    
    def _on_release(self, key):
        self._state = set()

def press_combo(C, s):
    keys = keyboard.HotKey.parse(s)
    for k in keys:
        C.press(k)
    for k in reversed(keys):
        C.release(k)

def get_last_word(C):
    press_combo(C, '<ctrl>+<shift>+<left>')
    old = pyperclip.paste()
    press_combo(C, '<ctrl>+c')
    C.tap(Key.right)
    w = pyperclip.paste()
    pyperclip.copy(old)
    return w

def do_stuff(delta, words = {}):
    do_stuff.clicks = [i for i in do_stuff.clicks if time.time() - i < 2]
    do_stuff.clicks.append(time.time())
    if len(do_stuff.clicks) >= 10:
        print('RESTART')
        os.execl(sys.executable, sys.executable, *sys.argv)
    C = keyboard.Controller()
    w = get_last_word(C)
    if w.lower() in words:
        press_combo(C, '<ctrl>+<shift>+<left>')
        C.type(''.join(i if j.islower() else i.upper() for i, j in zip(words[w.lower()], w)))
        return
    l = w[-1].lower()
    for acc in ACCENTS:
        if l in acc:
            l = acc[(acc.index(l) + delta) % len(acc)]
            break
    ret = (normalize(w).lower(), w[: -1].lower() + l)
    if w[-1].isupper():
        l = l.upper()
    C.tap(Key.backspace)
    C.type(l)
    if ret[0] != ret[1] and ret[0].isalpha():
        return ret
do_stuff.clicks = []

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('shortcuts', nargs = '*', type = str)
    mex = parser.add_mutually_exclusive_group()
    mex.add_argument('--addword', '-a', metavar = 'W', nargs = '*')
    mex.add_argument('--test', '-t', action = 'store_true')
    args = parser.parse_args()
    if args.shortcuts:
        if args.addword is not None:
            parser.error('shortcuts and --addword are mutually exclusive')
        if args.test:
            parser.error('shortcuts and --test are mutually exclusive')
        if len(args.shortcuts) > 2:
            parser.error('too many shortcuts (need two or less)')
    else:
        if args.addword is None and not args.test:
            parser.error('no shortcuts provided (need at least one)')
    return args


SPECIAL_WORDS_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'special_words.txt')

def load_special_words():
    try:
        return set(open(SPECIAL_WORDS_PATH, 'r').read().split())
    except FileNotFoundError:
        return set()
def save_special_words(words):
    with open(SPECIAL_WORDS_PATH, 'w') as fout:
        for w in sorted(words):
            fout.write(w)
            fout.write('\n')

def run(shortcut1, shortcut2 = None):
    special_words = [w.lower() for w in load_special_words()]
    special_words = { normalize(w) : w for w in special_words }
    special_words_buffer = deque()
    def dec(*args, **kwargs):
        def f():
            x = do_stuff(*args, **kwargs)
            if x is not None:
                special_words_buffer.append(x + (time.time(), ))
        return f
    def update_buffer():
        nonlocal special_words, special_words_buffer
        did_something = False
        while special_words_buffer and time.time() - special_words_buffer[0][2] > 10:
            i, j, k = special_words_buffer.popleft()
            special_words[i] = j
            did_something = True
            for acc in ACCENTS:
                if j[-1] in acc[0 : 2]:
                    del special_words[i]
                    break
        if did_something:
            save_special_words(special_words.values())
        print(special_words)
    hotkeys = { shortcut1 : dec(1, special_words), 'default' : update_buffer }
    if shortcut2:
        hotkeys[shortcut2] = dec(-1)
    try:
        with MultipleHotKeys(hotkeys) as ghk:
            ghk.join()
    except Exception:
        C = keyboard.Controller()
        for k in [Key.shift, Key.ctrl, Key.alt]:
            C.release(k)

def run_test():
    def print_key(k):
        try:
            print(f'<{k.name}>')
        except AttributeError:
            print(k)
    with keyboard.Listener(on_press = lambda k: print_key(k)) as listener:
        listener.join()

def run_add_words(ws):
    if not ws:
        subprocess.run(['xdg-open', SPECIAL_WORDS_PATH])
        return
    special_words = load_special_words()
    for w in ws:
        special_words.add(w)
    save_special_words(special_words)

if __name__ == '__main__':
    args = parse_args()
    if args.shortcuts:
        run(*args.shortcuts)
    elif args.test:
        run_test()
    elif args.addword is not None:
        run_add_words(args.addword)
