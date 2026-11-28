[中文](README_CN.md)|English
# Overview

This project is based on the MIMO API. It synthesizes teacher-input text into audio paragraph by paragraph, supports setting the synthesis rate limit and paragraph interval, and outputs a WAV file.

# Environment Requirements

1. Windows is supported / others are unknown.

2. You need to additionally install `openai` and `python-dotenv` to run it. You can run
``
pip install -r requirements.txt
``
to install them.

1. This project requires a network connection.

2. Run `main.py` to run it.

3. The software UI uses `tkinter`. This library is included with Windows by default, but Linux may require `python3-tk`.

# Usage Example

1. Create a `.env` file in the root directory and write `MMIMO_API_KEY=your_MIMO_API_KEY` into it. <font color=red>The packaged software also requires this! It must be placed in the root directory.</font>

> `.env` is placed as an external file in the same directory as the `.exe` / `.py` file.

2. Start the software, and you will see something like:
![菜单
生成音频
跟读朗诵
退出](docs/images/菜单.png)

## Generate Recording
3. Click Generate Recording, and you will see something like:
![**合成限流**
请输入每秒最多合成多少个音频:
30
确定 取消](docs/images/合成限流.png)

interface, then you can modify the value in the box to change the maximum number of audios synthesized per second. <font color=white>*(Of course, this is to prevent synthesizing too many at once and burning tokens.)*</font>

4. After completion, you will see something like:
![**间隔时间**
请输入间隔时间(秒):
2
确定 取消](docs/images/间隔时间.png)

interface, then you can modify the value in the box to change the pause interval between each word. *(Fill it in as you see fit; I think 2S is fine.)* Then click OK.

5. This is the last step. After you click OK in the previous step, you will see something like:
![**输入框**
请输入要合成的文本(用两个空格分隔分段):
（空）
确定取消](docs/images/输入框.png)

interface, then copy the text you need to convert to audio into it. **(Use two spaces to separate paragraphs.)** For example, `first paragraph text  second paragraph text  third paragraph text`

6. The output file is a single file `test_output.wav` in the root directory.

## Follow-along Playback

3. Click Generate Recording, and you will see something like:
![**跟读播放**
输入文本(用两个空格分隔要逐段朗读的内容):
段落间隔(秒): 2 ***开始朗读***
准备就绪
上一个 暂停 继续 下一个](docs/images/跟读播放.png)

interface. You can enter content in the large box, then set the interval time, and finally click Start Reading.

4. You can click Pause, Play, Previous/Next to control the recitation.

# Project Details

1. When the project runs, an `Audio` folder will be generated. This folder is the project's cache folder, and cache files are stored here. If the folder takes up too much space, you can try deleting this folder, but if you delete it, generation may become slower.

> 1. It becomes slower because when reassembling `test_output.wav`, the word recordings need to be regenerated.
> 2. This folder can be safely deleted.
> 3. This folder is used to store the audio files used to concatenate `test_output.wav`.

2. The output file is the `test_output.wav` file in the root directory. After packaging, the output file is in the same directory as `main.exe`. <font color=red>The file will be overwritten when outputting repeatedly.</font>

# FAQ / Troubleshooting

## What should I do if it says the API Key is invalid?

Reapply for the API, check whether the format is correct, and check the `.env` file name, variable name case, path, spaces, balance, `base_url`, and network/proxy.

## What should I do if synthesis fails / is rate-limited?

Try running the software again.

## `test_output.wav` was not generated

Check whether you have file read/write permissions, check whether any paragraph was successfully synthesized, whether `Audio` is empty, whether the output file is in use, and whether the directory is writable.

## Chinese garbled characters / spaces in the path

Not tested.

## Regeneration is very slow after deleting Audio

Check the network and retry. TTS will be requested again, which may consume tokens again.

# Project Structure

```
.
├── main.py
├── on.py
├── requirements.txt
├── .env
├── Audio/ # cache directory
├── LICENSE
├── .gitignore
├── docs/images/
└── test_output.wav # output file
```

# License

This project is open source under the [GNU General Public License v3.0](LICENSE).
Copyright (C) 2026 李天月.

# Sponsorship

If this project is helpful to you, you are welcome to voluntarily sponsor to support maintenance.

> Sponsorship is a voluntary donation, does not represent the purchase of services, does not affect the project's continued open-source availability under GNU GPL v3.0, and does not constitute additional warranty or priority support commitment.

- WeChat tip: [![点击查看](docs/images/打赏.png)](https://cdn.luogu.com.cn/upload/image_hosting/58bf46x8.webp)
- WeChat transfer: [![点击查看](docs/images/收款.png)](https://cdn.luogu.com.cn/upload/image_hosting/j21fsygr.webp)

The payment QR code images are only for voluntary sponsorship. Please be aware of personal information disclosure risks.