import os
import base64
import io
import math
import re
import wave
import on
import hashlib
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(BASE_DIR, "Audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

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


class 音频合成限流器:
    def __init__(self, 每秒最大合成数):
        self.rate = 每秒最大合成数
        self.capacity = max(1.0, 每秒最大合成数)
        self.tokens = self.capacity
        self.updated_at = time.monotonic()
        self.lock = threading.Lock()

    def acquire(self):
        while True:
            with self.lock:
                now = time.monotonic()
                elapsed = now - self.updated_at
                self.tokens = min(
                    self.capacity,
                    self.tokens + elapsed * self.rate,
                )
                self.updated_at = now

                if self.tokens >= 1:
                    self.tokens -= 1
                    return

                wait_seconds = (1 - self.tokens) / self.rate

            time.sleep(max(wait_seconds, 0.01))


合成限流器 = None
MAX_WORKERS = 10


def 合成音频(text):
    cache_key = hashlib.sha256(text.encode("utf-8")).hexdigest()
    cache_path = os.path.join(AUDIO_DIR, f"{cache_key}.wav")

    if os.path.isfile(cache_path):
        try:
            with wave.open(cache_path, "rb") as wav:
                wav.readframes(wav.getnframes())
            print(f"使用缓存：{text}")
            with open(cache_path, "rb") as audio_file:
                return audio_file.read()
        except (wave.Error, EOFError, OSError):
            os.remove(cache_path)

    合成限流器.acquire()
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
    with open(cache_path, "wb") as cache_file:
        cache_file.write(audio_data)
    return audio_data


def 合成并保存音频(text, filename="test_output.wav", 间隔秒数=0):
    segments = [segment.strip() for segment in re.split(r" {2}", text) if segment.strip()]
    if not segments:
        raise ValueError("请输入要合成的文本")

    pcm_segments = []
    wav_format = None

    unique_segments = list(dict.fromkeys(segments))
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        audio_by_segment = dict(zip(unique_segments, executor.map(合成音频, unique_segments)))

    for segment in segments:
        with wave.open(io.BytesIO(audio_by_segment[segment]), "rb") as wav:
            format_info = (
                wav.getnchannels(),
                wav.getsampwidth(),
                wav.getframerate(),
            )
            if wav_format is None:
                wav_format = format_info
            elif format_info != wav_format:
                raise ValueError("分段音频的 WAV 格式不一致，无法合并")
            pcm_segments.append(wav.readframes(wav.getnframes()))

    channels, sampwidth, framerate = wav_format
    silence_frames = round(间隔秒数 * framerate)
    silence = bytes(silence_frames * channels * sampwidth)
    output_pcm = silence.join(pcm_segments)

    with wave.open(str(filename), "wb") as output:
        output.setnchannels(channels)
        output.setsampwidth(sampwidth)
        output.setframerate(framerate)
        output.writeframes(output_pcm)

    print(f" 已生成 {filename}")


# 获取限流
rate_input = on.ask_input(
    title="合成限流",
    prompt="请输入每秒最多合成多少个音频：",
    default="5",
)
if rate_input is None:
    raise SystemExit

try:
    每秒最大合成数 = float(rate_input)
except ValueError:
    raise ValueError("每秒合成数量必须是数字")

if not math.isfinite(每秒最大合成数) or 每秒最大合成数 <= 0:
    raise ValueError("每秒合成数量必须是大于 0 的有限数字")

合成限流器 = 音频合成限流器(每秒最大合成数)

# 获取间隔时间
time_input = on.ask_input(
    title="间隔时间",
    prompt="请输入间隔时间（秒）：",
    default="2",
)
if time_input is None:
    raise SystemExit

try:
    间隔秒数 = float(time_input)
except ValueError:
    raise ValueError("间隔时间必须是数字")

if not math.isfinite(间隔秒数) or 间隔秒数 < 0:
    raise ValueError("间隔时间必须是大于或等于 0 的有限数字")

# 调用函数
ask_input = on.ask_input(title="输入框", prompt="请输入要合成的文本（用两个空格分隔分段）：")
if ask_input is not None:
    合成并保存音频(ask_input, 间隔秒数=间隔秒数)