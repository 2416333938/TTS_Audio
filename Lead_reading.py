# TTS大模型语音合成 - 用于教师生成录音的软件
# Copyright (C) 2026 李天月
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
import base64
import hashlib
import io
import math
import os
import re
import time
import wave
from concurrent.futures import ThreadPoolExecutor
import tkinter as tk
from tkinter import messagebox, scrolledtext

import pygame
from dotenv import load_dotenv
from openai import OpenAI


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(BASE_DIR, "Audio")


def read_api_key() -> str:
    load_dotenv()
    api_key = os.getenv("MIMO_API_KEY")
    if not api_key:
        raise ValueError("未在 .env 文件中找到 MIMO_API_KEY")
    return api_key


client = OpenAI(
    api_key=read_api_key(),
    base_url="https://api.xiaomimimo.com/v1",
)


def 合成音频(text):
    cache_key = hashlib.sha256(text.encode("utf-8")).hexdigest()
    cache_path = os.path.join(AUDIO_DIR, f"{cache_key}.wav")
    if os.path.isfile(cache_path):
        try:
            with open(cache_path, "rb") as audio_file:
                cached_audio = audio_file.read()
            with wave.open(io.BytesIO(cached_audio), "rb") as wav:
                wav.readframes(wav.getnframes())
        except (wave.Error, EOFError, OSError):
            print(f"缓存音频无效，重新合成：{text}")
        else:
            print(f"使用缓存：{text}")
            return cached_audio

    print(f"正在合成：{text} ...")
    resp = client.chat.completions.create(
        model="mimo-v2.5-tts",
        modalities=["text", "audio"],
        audio={"voice": "mimo_default", "format": "wav"},
        messages=[
            {"role": "user", "content": "<style>开心</style>"},
            {"role": "assistant", "content": text},
        ],
    )
    audio_data = base64.b64decode(resp.choices[0].message.audio.data)
    with wave.open(io.BytesIO(audio_data), "rb") as wav:
        wav.readframes(wav.getnframes())
    os.makedirs(AUDIO_DIR, exist_ok=True)
    with open(cache_path, "wb") as cache_file:
        cache_file.write(audio_data)
    return audio_data


class LeadReadingGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("跟读播放")
        self.root.geometry("760x520")
        self.root.minsize(560, 420)

        self.segments = []
        self.futures = []
        self.executor = None
        self.channel = None
        self.current_sound = None
        self.current_index = 0
        self.interval_seconds = 0.0
        self.wait_until = 0.0
        self.active = False
        self.paused = False

        self._create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self._close)

    def _create_widgets(self):
        tk.Label(self.root, text="输入文本（用两个空格分隔要逐段朗读的内容）：").pack(
            anchor="w", padx=16, pady=(14, 4)
        )
        self.text_input = scrolledtext.ScrolledText(
            self.root, height=6, wrap=tk.WORD, font=("Microsoft YaHei UI", 11)
        )
        self.text_input.pack(fill="x", padx=16)

        settings = tk.Frame(self.root)
        settings.pack(anchor="w", padx=16, pady=10)
        tk.Label(settings, text="段落间隔（秒）：").pack(side="left")
        self.interval_input = tk.Entry(settings, width=8)
        self.interval_input.insert(0, "2")
        self.interval_input.pack(side="left")
        self.start_button = tk.Button(settings, text="开始朗读", command=self._start)
        self.start_button.pack(side="left", padx=(12, 0))

        self.current_text = tk.Label(
            self.root,
            text="准备就绪",
            font=("Microsoft YaHei UI", 24, "bold"),
            wraplength=700,
            justify="center",
            height=4,
            relief="groove",
        )
        self.current_text.pack(fill="both", expand=True, padx=16, pady=12)

        controls = tk.Frame(self.root)
        controls.pack(pady=(0, 8))
        self.previous_button = tk.Button(
            controls, text="上一个", width=12, command=self._previous, state="disabled"
        )
        self.previous_button.pack(side="left", padx=5)
        self.pause_button = tk.Button(
            controls, text="暂停", width=12, command=self._pause, state="disabled"
        )
        self.pause_button.pack(side="left", padx=5)
        self.resume_button = tk.Button(
            controls, text="继续", width=12, command=self._resume, state="disabled"
        )
        self.resume_button.pack(side="left", padx=5)
        self.next_button = tk.Button(
            controls, text="下一个", width=12, command=self._next, state="disabled"
        )
        self.next_button.pack(side="left", padx=5)

        self.status_text = tk.StringVar(value="输入文本后点击“开始朗读”")
        tk.Label(self.root, textvariable=self.status_text, anchor="w").pack(
            fill="x", padx=16, pady=(0, 12)
        )

    def _start(self):
        if self.active:
            return

        text = self.text_input.get("1.0", "end").strip()
        self.segments = [
            segment.strip()
            for segment in re.split(r" {2}", text)
            if segment.strip()
        ]
        if not self.segments:
            messagebox.showerror("输入错误", "请输入要朗读的文本。", parent=self.root)
            return

        try:
            interval_seconds = float(self.interval_input.get())
        except ValueError:
            messagebox.showerror("输入错误", "段落间隔必须是数字。", parent=self.root)
            return
        if not math.isfinite(interval_seconds) or interval_seconds < 0:
            messagebox.showerror(
                "输入错误",
                "段落间隔必须是大于或等于 0 的有限数字。",
                parent=self.root,
            )
            return

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except pygame.error as error:
            messagebox.showerror("播放失败", str(error), parent=self.root)
            return

        self.interval_seconds = interval_seconds
        self.current_index = 0
        self.wait_until = 0.0
        self.active = True
        self.paused = False
        self.channel = None
        self.executor = ThreadPoolExecutor(max_workers=2)
        futures_by_segment = {
            segment: self.executor.submit(合成音频, segment)
            for segment in dict.fromkeys(self.segments)
        }
        self.futures = [futures_by_segment[segment] for segment in self.segments]
        self.start_button.configure(state="disabled")
        self._set_control_states(active=True, paused=False)
        self._show_current("等待音频…")
        self.status_text.set("正在准备朗读")
        self.root.after(100, self._poll)

    def _poll(self):
        if not self.active or self.paused:
            return

        if self.channel is not None and not self.channel.get_busy():
            self.channel = None
            self.current_sound = None
            self.current_index += 1
            self.wait_until = time.monotonic() + self.interval_seconds
            if self.current_index >= len(self.segments):
                self._finish()
                return

        if self.channel is None and time.monotonic() >= self.wait_until:
            self._play_current_when_ready()

        if self.active:
            self.root.after(100, self._poll)

    def _play_current_when_ready(self):
        future = self.futures[self.current_index]
        if not future.done():
            self._show_current("正在合成…")
            self.status_text.set(
                f"正在合成第 {self.current_index + 1}/{len(self.segments)} 段"
            )
            return

        try:
            audio_data = future.result()
            sound = pygame.mixer.Sound(file=io.BytesIO(audio_data))
            channel = pygame.mixer.Channel(0)
            channel.play(sound)
        except Exception as error:
            self._fail(error)
            return

        self.channel = channel
        self.current_sound = sound
        self._show_current()
        self.status_text.set(
            f"正在朗读第 {self.current_index + 1}/{len(self.segments)} 段"
        )

    def _show_current(self, prefix=""):
        text = self.segments[self.current_index]
        self.current_text.configure(text=f"{prefix}\n{text}" if prefix else text)

    def _pause(self):
        if not self.active or self.paused:
            return
        self.paused = True
        if self.channel is not None:
            self.channel.pause()
        self.status_text.set("已暂停")
        self._set_control_states(active=True, paused=True)

    def _resume(self):
        if not self.active or not self.paused:
            return
        self.paused = False
        if self.channel is not None:
            self.channel.unpause()
        self.status_text.set("继续朗读")
        self._set_control_states(active=True, paused=False)
        self.root.after(0, self._poll)

    def _previous(self):
        if not self.active:
            return
        self.current_index = max(0, self.current_index - 1)
        self._select_current()

    def _next(self):
        if not self.active:
            return
        self.current_index = min(len(self.segments) - 1, self.current_index + 1)
        self._select_current()

    def _select_current(self):
        if self.channel is not None:
            self.channel.stop()
        self.channel = None
        self.current_sound = None
        self.wait_until = 0.0
        self._show_current("等待音频…")
        if not self.paused:
            self.root.after(0, self._poll)

    def _set_control_states(self, active, paused):
        enabled = "normal" if active else "disabled"
        self.previous_button.configure(state=enabled)
        self.next_button.configure(state=enabled)
        self.pause_button.configure(
            state="normal" if active and not paused else "disabled"
        )
        self.resume_button.configure(
            state="normal" if active and paused else "disabled"
        )

    def _finish(self):
        self.active = False
        self._shutdown_executor()
        self.start_button.configure(state="normal")
        self._set_control_states(active=False, paused=False)
        self.current_text.configure(text="朗读完成")
        self.status_text.set("播放已完成")

    def _fail(self, error):
        self.active = False
        if self.channel is not None:
            self.channel.stop()
            self.channel = None
        self._shutdown_executor()
        self.start_button.configure(state="normal")
        self._set_control_states(active=False, paused=False)
        self.status_text.set("播放失败")
        messagebox.showerror("合成或播放失败", str(error), parent=self.root)

    def _shutdown_executor(self):
        if self.executor is not None:
            self.executor.shutdown(wait=False, cancel_futures=True)
            self.executor = None

    def _close(self):
        self.active = False
        if self.channel is not None:
            self.channel.stop()
        self._shutdown_executor()
        pygame.mixer.quit()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


def main():
    LeadReadingGUI().run()


if __name__ == "__main__":
    main()