import os
import base64
import io
import math
import re
import wave
import on
import hashlib
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

    for segment in segments:
        with wave.open(io.BytesIO(合成音频(segment)), "rb") as wav:
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


# 获取间隔时间
time_input = on.ask_input(
    title="间隔时间",
    prompt="请输入间隔时间（秒）：",
    default="5",
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