#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""系统字体名称提取工具

通过 Windows GDI 枚举系统中真正注册的字体家族名称（即软件外观设置里
需要填写的字体“详细名称”），并提供 GUI 进行搜索、复制与预览。

界面：现代扁平 + 深色主题，Per-Monitor DPI Aware，随窗口自适应。

用法：
    直接运行（需要 Python 含 tkinter）：
        python 字体名称提取工具.py
    命令行模式：
        python 字体名称提取工具.py --list
        python 字体名称提取工具.py --export fonts.txt
        python 字体名称提取工具.py --count
"""
import os
import sys
import ctypes
from ctypes import (wintypes, POINTER, WINFUNCTYPE, c_void_p, c_uint,
                    c_int, c_long, c_byte, c_wchar)

# ==========================================================================
# 主题（现代扁平 · 深色）
# ==========================================================================
BG = "#1B1B26"          # 窗口背景
CARD = "#23232F"        # 卡片背景
CARD2 = "#2A2A38"       # 卡片次级 / 次按钮
BORDER = "#33334A"      # 描边
FG = "#E8E8F0"          # 主文字
FG_DIM = "#9A9AB0"      # 次文字
FG_MUTED = "#6B6B80"    # 弱化文字 / 占位
ACCENT = "#5B8CFF"      # 主色
ACCENT_HOVER = "#7AA2FF"
ACCENT_ACTIVE = "#4A7AF0"
SUCCESS = "#34C759"     # 成功反馈
SEL_BG = "#33436E"      # 列表选中行
HOVER_BG = "#2A2A3A"    # 列表悬停行

INDENT = "   "          # 列表项左缩进（视觉内边距）


# ==========================================================================
# 字体枚举（Windows GDI）
# ==========================================================================
gdi32 = ctypes.WinDLL('gdi32', use_last_error=True)


class LOGFONT(ctypes.Structure):
    _fields_ = [
        ("lfHeight", c_long),
        ("lfWidth", c_long),
        ("lfEscapement", c_long),
        ("lfOrientation", c_long),
        ("lfWeight", c_long),
        ("lfItalic", c_byte),
        ("lfUnderline", c_byte),
        ("lfStrikeOut", c_byte),
        ("lfCharSet", c_byte),
        ("lfOutPrecision", c_byte),
        ("lfClipPrecision", c_byte),
        ("lfQuality", c_byte),
        ("lfPitchAndFamily", c_byte),
        ("lfFaceName", c_wchar * 32),
    ]


FONTENUMPROC = WINFUNCTYPE(c_int, POINTER(LOGFONT), c_void_p, c_uint, c_void_p)

gdi32.EnumFontFamiliesExW.argtypes = [
    wintypes.HDC, POINTER(LOGFONT), FONTENUMPROC, c_void_p, c_uint]
gdi32.EnumFontFamiliesExW.restype = c_int
gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
gdi32.CreateCompatibleDC.restype = wintypes.HDC
gdi32.DeleteDC.argtypes = [wintypes.HDC]
gdi32.DeleteDC.restype = c_int


def enum_fonts():
    """返回排序去重后的系统字体家族名称列表。"""
    names = []
    seen = set()
    lf = LOGFONT()
    lf.lfCharSet = 0  # DEFAULT_CHARSET：枚举所有字符集

    @FONTENUMPROC
    def callback(plf, lpntme, fonttype, lparam):
        name = plf.contents.lfFaceName
        if name:
            name = name.strip()
        # 跳过以 '@' 开头的竖排别名（非软件设置所需的真实字体名）
        if name and not name.startswith('@') and name not in seen:
            seen.add(name)
            names.append(name)
        return 1  # 继续枚举

    hdc = gdi32.CreateCompatibleDC(None)
    try:
        gdi32.EnumFontFamiliesExW(hdc, ctypes.byref(lf), callback, None, 0)
    finally:
        gdi32.DeleteDC(hdc)

    # 英文名（ASCII 开头）在前，非 ASCII（中文等）在后，组内按名称排序
    names.sort(key=lambda s: (0 if ord(s[0]) < 128 else 1, s))
    return names


# ==========================================================================
# 环境适配
# ==========================================================================
def resource_path(name):
    """兼容 PyInstaller onefile 的资源路径。"""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


def enable_dpi_awareness():
    """声明 DPI 感知，避免高分屏模糊。"""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PER_MONITOR
        return
    except Exception:
        pass
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def pick_fonts(root):
    """挑选界面字体（优先 HarmonyOS Sans SC，缺失则逐级回退）。"""
    from tkinter import font as tkfont
    fams = set(tkfont.families(root))

    def pick(cands, default):
        for c in cands:
            if c in fams:
                return c
        return default

    ui = pick(["HarmonyOS Sans SC", "Microsoft YaHei UI", "Microsoft YaHei",
               "Segoe UI"], "Segoe UI")
    mono = pick(["Cascadia Mono", "Consolas", "Courier New"], "Courier New")
    return ui, mono


# ==========================================================================
# GUI（tkinter · 深色扁平）
# ==========================================================================
def main():
    import tkinter as tk
    from tkinter import ttk, filedialog

    enable_dpi_awareness()
    fonts = enum_fonts()

    root = tk.Tk()
    ui, mono = pick_fonts(root)
    # DPI 缩放：以实际 DPI 校准 tk，使点值字号等比放大
    try:
        root.tk.call('tk', 'scaling', root.winfo_fpixels('1i') / 72.0)
    except Exception:
        pass
    root.title(f"字体名称提取工具 · 共 {len(fonts)} 种字体")
    root.geometry("860x650")
    root.minsize(720, 560)
    root.configure(bg=BG)

    # 窗口图标（打包后从 _MEIPASS 读取）
    try:
        ico = resource_path("app.ico")
        if os.path.exists(ico):
            root.iconbitmap(ico)
    except Exception:
        pass

    F_TITLE = (ui, 15, "bold")
    F_BODY = (ui, 11)
    F_SMALL = (ui, 9)
    F_LIST = (ui, 11)
    F_MONO = (mono, 10)

    query = tk.StringVar()
    preview_text = tk.StringVar(value="永和九年岁在癸丑 ABCdefg 0123456789 字体效果预览")
    preview_name = tk.StringVar(value="未选择")

    # ---------- 顶部标题栏 ----------
    frm_head = tk.Frame(root, bg=BG)
    frm_head.pack(fill="x", padx=16, pady=(14, 8))
    tk.Label(frm_head, text=" Aa ", bg=ACCENT, fg="#FFFFFF",
             font=(ui, 13, "bold")).pack(side="left")
    tk.Label(frm_head, text="  字体名称提取", bg=BG, fg=FG,
             font=F_TITLE).pack(side="left")
    tk.Label(frm_head, text=f"共 {len(fonts)} 种", bg=CARD2, fg=FG_DIM,
             font=F_SMALL, padx=10, pady=4).pack(side="right")

    # ---------- 搜索框 ----------
    frm_search = tk.Frame(root, bg=BG)
    frm_search.pack(fill="x", padx=16, pady=(0, 10))
    entry_search = tk.Entry(
        frm_search, textvariable=query, font=F_BODY,
        bg=CARD, fg=FG, insertbackground=ACCENT, relief="flat",
        highlightthickness=1, highlightbackground=BORDER,
        highlightcolor=ACCENT)
    entry_search.pack(fill="x", ipady=7)
    entry_search.focus()
    _ph = "输入关键字筛选字体名称（如 雅黑 / Sans / 楷体）"

    def show_ph():
        if not query.get():
            entry_search.insert(0, _ph)
            entry_search.config(fg=FG_MUTED)

    def clear_ph(_=None):
        if entry_search.get() == _ph:
            entry_search.delete(0, tk.END)
            entry_search.config(fg=FG)

    entry_search.bind("<FocusIn>", clear_ph)
    entry_search.bind("<FocusOut>", lambda e: show_ph())
    show_ph()

    # ---------- 主体：左列表 + 右预览 ----------
    frm_main = tk.Frame(root, bg=BG)
    frm_main.pack(fill="both", expand=True, padx=16, pady=0)

    # 左：列表卡片
    card_list = tk.Frame(frm_main, bg=CARD)
    card_list.pack(side="left", fill="both", expand=True)

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure("Dark.Vertical.TScrollbar", background=CARD2,
                    troughcolor=CARD, bordercolor=CARD, arrowcolor=FG_DIM,
                    relief="flat", arrowsize=12)
    style.map("Dark.Vertical.TScrollbar",
              background=[("active", BORDER), ("pressed", ACCENT)])

    lb = tk.Listbox(card_list, font=F_LIST, activestyle="none",
                    selectmode=tk.SINGLE, bg=CARD, fg=FG,
                    selectbackground=SEL_BG, selectforeground=FG,
                    relief="flat", bd=0, highlightthickness=0,
                    exportselection=False)
    sb = ttk.Scrollbar(card_list, orient="vertical", command=lb.yview,
                       style="Dark.Vertical.TScrollbar")
    lb.config(yscrollcommand=sb.set)
    lb.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
    sb.pack(side="left", fill="y", pady=8, padx=(0, 4))

    # 右：预览卡片
    card_prev = tk.Frame(frm_main, bg=CARD, width=320)
    card_prev.pack(side="left", fill="y", padx=(12, 0))
    card_prev.pack_propagate(False)

    tk.Label(card_prev, text="预览", bg=CARD, fg=FG_DIM,
             font=F_SMALL).pack(anchor="w", padx=14, pady=(12, 4))
    entry_preview = tk.Entry(card_prev, textvariable=preview_text, font=F_BODY,
                             bg=CARD2, fg=FG, insertbackground=ACCENT,
                             relief="flat", highlightthickness=1,
                             highlightbackground=BORDER, highlightcolor=ACCENT)
    entry_preview.pack(fill="x", padx=14, ipady=5)

    preview_label = tk.Label(card_prev, text="", bg=CARD2, fg=FG,
                             wraplength=270, justify="left", anchor="nw",
                             padx=14, pady=14, font=(ui, 24))
    preview_label.pack(fill="both", expand=True, padx=14, pady=(10, 6))

    tk.Label(card_prev, textvariable=preview_name, bg=CARD, fg=FG_MUTED,
             font=F_MONO, anchor="w").pack(fill="x", padx=14, pady=(0, 12))

    # ---------- 状态栏 ----------
    status = tk.StringVar(value="就绪")
    tk.Label(root, textvariable=status, bg=BG, fg=FG_DIM, anchor="w",
             font=F_SMALL).pack(fill="x", padx=18, pady=(6, 0))

    # ---------- 按钮区 ----------
    frm_btn = tk.Frame(root, bg=BG)
    frm_btn.pack(fill="x", padx=16, pady=(8, 14))

    def bind_hover(w, normal, hover):
        w.bind("<Enter>", lambda e: w.config(bg=hover))
        w.bind("<Leave>", lambda e: w.config(bg=normal))

    def primary(parent, text, cmd, padx=20):
        b = tk.Button(parent, text=text, command=cmd, font=(ui, 11, "bold"),
                      bg=ACCENT, fg="#FFFFFF", activebackground=ACCENT_ACTIVE,
                      activeforeground="#FFFFFF", relief="flat", bd=0,
                      padx=padx, pady=8, cursor="hand2")
        bind_hover(b, ACCENT, ACCENT_HOVER)
        return b

    def secondary(parent, text, cmd, padx=16):
        b = tk.Button(parent, text=text, command=cmd, font=F_BODY,
                      bg=CARD2, fg=FG, activebackground=BORDER,
                      activeforeground=FG, relief="flat", bd=0,
                      padx=padx, pady=8, cursor="hand2")
        bind_hover(b, CARD2, BORDER)
        return b

    # ---------- 逻辑 ----------
    hover_idx = [None]

    def refresh():
        q = query.get().strip().lower()
        if q == _ph.lower():
            q = ""
        lb.delete(0, tk.END)
        cnt = 0
        for f in fonts:
            if not q or q in f.lower():
                lb.insert(tk.END, INDENT + f)
                cnt += 1
        hover_idx[0] = None
        status.set(f"显示 {cnt} / 共 {len(fonts)} 种")

    def current_name():
        sel = lb.curselection()
        if not sel:
            return None
        return lb.get(sel[0]).strip()

    def on_select(evt=None):
        name = current_name()
        if not name:
            return
        preview_name.set(name)
        try:
            preview_label.config(font=(name, 24), text=preview_text.get())
        except Exception:
            preview_label.config(font=(ui, 24), text=preview_text.get())

    def on_motion(e):
        idx = lb.nearest(e.y)
        sel = lb.curselection()
        if sel and sel[0] == idx:
            idx = None
        if idx == hover_idx[0]:
            return
        prev = hover_idx[0]
        if prev is not None and prev < lb.size():
            lb.itemconfig(prev, background=CARD)
        if idx is not None and 0 <= idx < lb.size():
            lb.itemconfig(idx, background=HOVER_BG)
        hover_idx[0] = idx

    def on_leave(_=None):
        prev = hover_idx[0]
        if prev is not None and prev < lb.size():
            lb.itemconfig(prev, background=CARD)
        hover_idx[0] = None

    def show_toast(text):
        tl = tk.Toplevel(root)
        tl.overrideredirect(True)
        tl.configure(bg=SUCCESS)
        try:
            tl.attributes("-topmost", True)
        except Exception:
            pass
        tk.Label(tl, text=text, bg=SUCCESS, fg="#FFFFFF",
                 font=(ui, 11, "bold"), padx=20, pady=12).pack()
        tl.update_idletasks()
        w, h = tl.winfo_width(), tl.winfo_height()
        x = root.winfo_rootx() + (root.winfo_width() - w) // 2
        y = root.winfo_rooty() + (root.winfo_height() - h) // 2
        tl.geometry(f"+{x}+{y}")
        tl.after(1300, tl.destroy)

    def copy_selected(event=None):
        name = current_name()
        if not name:
            status.set("请先在左侧选择一种字体")
            show_toast("请先选择一种字体")
            return
        root.clipboard_clear()
        root.clipboard_append(name)
        root.update()
        status.set(f"✓ 已复制：{name}（可直接粘贴到软件设置）")
        show_toast(f"✓ 已复制：{name}")

    def filtered_items():
        q = query.get().strip().lower()
        if q == _ph.lower():
            q = ""
        return [f for f in fonts if (not q or q in f.lower())]

    def copy_all():
        items = filtered_items()
        if not items:
            status.set("没有可复制的字体")
            show_toast("没有可复制的字体")
            return
        root.clipboard_clear()
        root.clipboard_append("\n".join(items))
        root.update()
        status.set(f"✓ 已复制 {len(items)} 个字体名称到剪贴板")
        show_toast(f"✓ 已复制 {len(items)} 个名称")

    def export_all():
        items = filtered_items()
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("CSV 文件", "*.csv")],
            title="导出字体名称")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as fp:
                fp.write("\n".join(items))
            status.set(f"✓ 已导出 {len(items)} 个字体名称 -> {path}")
            show_toast(f"✓ 已导出 {len(items)} 个名称")
        except Exception as e:
            status.set(f"导出失败：{e}")

    primary(frm_btn, "复制选中", copy_selected).pack(side="left")
    secondary(frm_btn, "复制全部（当前筛选）", copy_all).pack(side="left", padx=8)
    secondary(frm_btn, "导出到文件", export_all).pack(side="left")
    tk.Label(frm_btn, text="提示：单击选中可预览，双击直接复制",
             bg=BG, fg=FG_MUTED, font=F_SMALL).pack(side="right")

    lb.bind("<Double-Button-1>", copy_selected)
    lb.bind("<<ListboxSelect>>", on_select)
    lb.bind("<Motion>", on_motion)
    lb.bind("<Leave>", on_leave)
    entry_search.bind("<KeyRelease>", lambda e: refresh())
    entry_preview.bind("<KeyRelease>", lambda e: on_select())

    refresh()
    root.mainloop()


def main_cmd():
    import argparse
    p = argparse.ArgumentParser(description="系统已安装字体名称提取工具")
    p.add_argument("--list", action="store_true", help="列出所有字体名称后退出")
    p.add_argument("--export", metavar="FILE", help="导出全部字体名称到文件")
    p.add_argument("--count", action="store_true", help="仅显示字体数量")
    args = p.parse_args()

    fonts = enum_fonts()
    if args.count:
        print(len(fonts))
        return
    if args.export:
        with open(args.export, "w", encoding="utf-8") as fp:
            fp.write("\n".join(fonts))
        print(f"已导出 {len(fonts)} 个字体名称 -> {args.export}")
        return
    if args.list:
        for f in fonts:
            print(f)
        print(f"\n共 {len(fonts)} 种字体", file=sys.stderr)
        return
    try:
        main()
    except Exception as e:  # 避免 windowed 模式下静默崩溃
        import tkinter.messagebox as mb
        mb.showerror("启动失败", f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    main_cmd()
