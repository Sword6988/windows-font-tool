# 字体名称提取工具

一键提取 Windows 系统中已安装字体的名称（即软件外观设置里需要填写的字体“详细名称”），
解决 `C:\Windows\Fonts` 下字体名无法直接复制的问题。

## 下载

最新版本：**v1.0.0** — [前往 Releases 下载](https://github.com/Sword6988/windows-font-tool/releases/tag/v1.0.0)

| 文件 | 大小 | SHA-256 |
|---|---|---|
| `FontNameExtractor-v1.0.0.exe` | 13,645,511 字节（约 13.01 MB） | `1ca1592dd35740abc8929df3b61063499f09cbe0a156f8a04a1c1731b46c873d` |

直链：<https://github.com/Sword6988/windows-font-tool/releases/download/v1.0.0/FontNameExtractor-v1.0.0.exe>

## 功能

- 列表展示系统全部字体名称（实测约 300+ 种，已过滤 `@` 竖排别名）
- 关键字实时筛选；鼠标悬停 / 选中行高亮
- 单击选中即用该字体实时预览效果
- 一键复制选中名称到剪贴板（双击亦可），并弹出成功提示
- 复制全部（当前筛选结果）、导出为 TXT
- 现代扁平深色界面，Per-Monitor DPI Aware，高分屏不模糊

## 直接运行

下载 Releases 中的 exe 双击即可运行（Windows 7+，无需安装 Python）。

从源码运行（需 Python 3.9+ 且包含 tkinter）：

```bash
python 字体名称提取工具.py
```

命令行模式：

```bash
python 字体名称提取工具.py --list             # 打印全部字体名
python 字体名称提取工具.py --export fonts.txt  # 导出到文件
python 字体名称提取工具.py --count             # 仅显示数量
```

## 自定义图标 / 重新打包

```bash
python make_icon.py    # 生成 app.ico（可替换为你自己的图标后重跑）
重新打包exe.bat         # 自动打包到 dist/
```

## 技术实现

- 字体名来源：Windows GDI `EnumFontFamiliesExW`（读取字体家族名，非注册表）
- GUI：Python 标准库 tkinter（零第三方运行时依赖）
- 打包：PyInstaller `--onefile --windowed`

## 许可

MIT
