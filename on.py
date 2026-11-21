import tkinter as tk


def ask_input(title="请输入", prompt="", default=""):
    """
    弹出一个输入框，点击"确定"后返回输入内容。

    参数:
        title:   窗口标题
        prompt:  输入框上方的提示文字
        default: 输入框的默认内容

    返回:
        字符串（用户输入的内容）；如果用户关闭窗口或点击取消，返回 None
    """
    result = {"value": None}

    root = tk.Tk()
    root.title(title)
    root.resizable(False, False)

    # 居中显示
    root.update_idletasks()
    w, h = 320, 140
    x = (root.winfo_screenwidth() - w) // 2
    y = (root.winfo_screenheight() - h) // 2
    root.geometry(f"{w}x{h}+{x}+{y}")

    # 提示文字
    if prompt:
        tk.Label(root, text=prompt, anchor="w").pack(
            fill="x", padx=12, pady=(12, 4)
        )

    # 输入框
    entry = tk.Entry(root, width=40)
    entry.pack(padx=12, pady=4, fill="x")
    entry.insert(0, default)
    entry.focus_set()
    entry.select_range(0, "end")

    def on_ok(event=None):
        result["value"] = entry.get()
        root.destroy()

    def on_cancel(event=None):
        result["value"] = None
        root.destroy()

    # 按钮
    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=8)
    tk.Button(btn_frame, text="确定", width=10, command=on_ok).pack(
        side="left", padx=6
    )
    tk.Button(btn_frame, text="取消", width=10, command=on_cancel).pack(
        side="left", padx=6
    )

    # 回车 = 确定，Esc = 取消
    root.bind("<Return>", on_ok)
    root.bind("<Escape>", on_cancel)
    root.protocol("WM_DELETE_WINDOW", on_cancel)  # 点 X 视为取消

    root.mainloop()
    return result["value"]


# ============ 使用示例 ============
if __name__ == "__main__":
    text = ask_input(title="输入框", prompt="请输入你的名字：")
    if text is None:
        print("用户取消了输入")
    else:
        print("你输入的是：", text)