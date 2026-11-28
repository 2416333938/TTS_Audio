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
import os
import synthesized_recording
import tkinter as tk
import Lead_reading

root = tk.Tk()
root.title("菜单")

button1 = tk.Button(root, text="生成音频", command=lambda: synthesized_recording.main())
button2 = tk.Button(root, text="跟读朗诵", command=lambda: Lead_reading.main())
button3 = tk.Button(root, text="退出", command=root.quit)
button1.pack()
button2.pack()
button3.pack()
root.mainloop()