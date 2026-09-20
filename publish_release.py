# -*- coding: utf-8 -*-
"""创建 / 更新 GitHub Release，并上传单文件 exe 作为可下载附件。

凭证来源：本机 Git Credential Manager（不会打印任何密钥）。

用法：
    python publish_release.py                 # 使用下方默认版本号与资产名
    python publish_release.py v1.0.1          # 指定新版本号（标签）
    python publish_release.py v1.0.1 MyTool.exe

脚本可重复执行：同标签的 Release 会被更新，同名资产会先删除再重传。
"""
import hashlib
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

# ------------------------- 可按需修改的配置 -------------------------
OWNER = "Sword6988"
REPO = "windows-font-tool"
TARGET_BRANCH = "main"
ASSET_BASENAME = "FontNameExtractor"   # 资产名 = {BASENAME}-{TAG}.exe
# -------------------------------------------------------------------

HERE = os.path.dirname(os.path.abspath(__file__))
EXE_CANDIDATES = [
    os.path.join(HERE, "dist", "字体名称提取工具.exe"),
    os.path.join(HERE, "dist", "FontNameExtractor.exe"),
]
GCM_PATHS = [
    r"C:\Program Files\Git\mingw64\bin\git-credential-manager.exe",
    r"C:\Program Files\Git\mingw64\libexec\git-core\git-credential-manager.exe",
    "git-credential-manager",
]
API = "https://api.github.com"
UPLOADS = "https://uploads.github.com"


def find_exe():
    for p in EXE_CANDIDATES:
        if os.path.isfile(p):
            return p
    sys.exit("未找到 exe，请先运行「重新打包exe.bat」。已查找：\n  " + "\n  ".join(EXE_CANDIDATES))


def get_token():
    for gcm in GCM_PATHS:
        if os.sep in gcm and not os.path.isfile(gcm):
            continue
        try:
            p = subprocess.run([gcm, "get"], input="protocol=https\nhost=github.com\n\n",
                               capture_output=True, text=True, timeout=180)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
        if p.returncode != 0:
            continue
        for line in p.stdout.splitlines():
            if line.startswith("password="):
                return line.split("=", 1)[1].strip()
    sys.exit("未能从 Git Credential Manager 取得 GitHub 凭证")


def req(method, url, token, data=None, ctype="application/json", timeout=300):
    headers = {
        "Authorization": "token " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "font-tool-release-script",
        "Content-Type": ctype,
    }
    body = None
    if data is not None:
        body = bytes(data) if isinstance(data, (bytes, bytearray)) else json.dumps(data).encode("utf-8")
        headers["Content-Length"] = str(len(body))
    r = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", "replace")
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = raw[:500]
        return e.code, parsed


def build_body(tag, asset_name, size, sha):
    return """## 字体名称提取工具 {tag}

一键提取系统中已安装字体的**真实名称**（即软件外观设置里需要填写的“详细字体名”），
解决 `C:\\Windows\\Fonts` 目录下字体名称无法直接复制的问题。

### 功能亮点
- **准确枚举**：调用 Windows GDI `EnumFontFamiliesExW` 获取系统注册的字体家族名，去重并过滤 `@` 竖排别名
- **搜索筛选**：输入关键字即时过滤列表，底部实时显示「显示 X / 共 N 种」
- **一键复制**：单击选中 → 点「复制选中」或直接双击 → 写入剪贴板，弹出绿色「✓ 已复制」提示
- **实时预览**：右侧卡片用所选字体渲染示例文字，示例文本可自定义
- **批量能力**：复制全部（当前筛选结果）、导出为 TXT 文件
- **现代界面**：深色扁平主题，悬停/选中高亮，自定义细滚动条
- **高分屏适配**：Per-Monitor DPI Aware，缩放不模糊
- **零依赖**：单文件 exe，目标机无需安装 Python

### 下载说明
| 项目 | 值 |
|---|---|
| 文件 | `{asset}` |
| 大小 | {size:,} 字节（约 {mb:.2f} MB） |
| SHA-256 | `{sha}` |
| 运行环境 | Windows 7 及以上 |

下载后双击即可启动，无需安装。

### 使用方法
1. 启动程序，自动枚举并列出系统全部字体
2. 顶部输入框输入关键字筛选（如 `雅黑`、`Harmony`）
3. 单击选中字体，右侧查看预览效果
4. 点「复制选中」或双击条目，字体名即写入剪贴板
5. 到目标软件的外观设置里粘贴即可
""".format(tag=tag, asset=asset_name, size=size, mb=size / 1048576.0, sha=sha)


def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else "v1.0.0"
    if not tag.startswith("v"):
        tag = "v" + tag
    asset_name = sys.argv[2] if len(sys.argv) > 2 else "%s-%s.exe" % (ASSET_BASENAME, tag)

    exe = find_exe()
    size = os.path.getsize(exe)
    h = hashlib.sha256()
    with open(exe, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    sha = h.hexdigest()
    print("[info] exe = %s" % exe)
    print("[info] size = %d bytes  sha256 = %s" % (size, sha))

    token = get_token()
    st, me = req("GET", API + "/user", token, timeout=120)
    print("[1] GET /user -> %s (login=%s)" % (st, (me or {}).get("login")))

    rel_url = "%s/repos/%s/%s/releases" % (API, OWNER, REPO)
    st, releases = req("GET", rel_url + "?per_page=100", token, timeout=120)
    if st != 200:
        sys.exit("列出 Release 失败：%s %s" % (st, releases))
    existing = next((r for r in (releases or []) if r.get("tag_name") == tag), None)
    print("[2] 已存在同标签 Release: %s" % ("是" if existing else "否"))

    payload = {
        "tag_name": tag,
        "target_commitish": TARGET_BRANCH,
        "name": "%s — 字体名称提取工具（Windows 单文件版）" % tag,
        "body": build_body(tag, asset_name, size, sha),
        "draft": False,
        "prerelease": False,
    }
    if existing:
        st, rel = req("PATCH", "%s/%d" % (rel_url, existing["id"]), token, payload)
        action = "更新"
    else:
        st, rel = req("POST", rel_url, token, payload)
        action = "创建"
    if st not in (200, 201):
        sys.exit("Release %s失败：%s %s" % (action, st, rel))
    print("[3] Release %s成功 -> id=%s tag=%s" % (action, rel["id"], rel["tag_name"]))

    st, assets = req("GET", "%s/%d/assets?per_page=100" % (rel_url, rel["id"]), token, timeout=120)
    for a in assets or []:
        print("    已有资产：%s (%d bytes)" % (a["name"], a["size"]))
        if a["name"] == asset_name:
            d, _ = req("DELETE", "%s/repos/%s/%s/releases/assets/%d" % (API, OWNER, REPO, a["id"]), token, timeout=120)
            print("[4] 删除同名旧资产 -> %s" % d)

    q = urllib.parse.urlencode({"name": asset_name})
    up = "%s/repos/%s/%s/releases/%d/assets?%s" % (UPLOADS, OWNER, REPO, rel["id"], q)
    with open(exe, "rb") as f:
        st, asset = req("POST", up, token, data=f.read(), ctype="application/octet-stream", timeout=1800)
    if st not in (200, 201):
        sys.exit("资产上传失败：%s %s" % (st, asset))
    print("[5] 资产上传成功 -> %s | %d bytes | %s" % (asset["name"], asset["size"], asset.get("state")))
    print("RELEASE_URL=%s" % rel["html_url"])
    print("ASSET_URL=%s" % asset["browser_download_url"])
    print("TAG=%s" % rel["tag_name"])
    print("DONE")


if __name__ == "__main__":
    main()
