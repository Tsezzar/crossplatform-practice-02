"""Актуальные версии и даты релизов инструментов кросс-платформенной разработки.

Данные берутся только из первоисточников: страниц Releases на GitHub, официальных
API и каталогов загрузки разработчиков. Результат — data/tool_versions.json
с URL источника и датой обращения для каждой записи.

Запуск: python tools/fetch_versions.py
"""
import datetime
import hashlib
import http.client
import json
import os
import pathlib
import re
import urllib.error
import urllib.request

OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "tool_versions.json"
# Необязательный кэш ответов (FETCH_CACHE=<каталог>): повторный запуск не расходует
# лимит GitHub API (60 запросов в час без авторизации)
CACHE = pathlib.Path(os.environ["FETCH_CACHE"]) if os.environ.get("FETCH_CACHE") else None


def headers(url):
    h = {"User-Agent": "crossplatform-practice-02"}
    if url.startswith("https://api.github.com/"):
        h["Accept"] = "application/vnd.github+json"
    return h


def get(url, attempts=3):
    cached = CACHE / (hashlib.sha1(url.encode()).hexdigest() + ".txt") if CACHE else None
    if cached and cached.exists():
        return cached.read_text(encoding="utf-8")
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers(url)), timeout=60) as r:
                body = r.read().decode("utf-8")
            if cached:
                cached.parent.mkdir(parents=True, exist_ok=True)
                cached.write_text(body, encoding="utf-8")
            return body
        except (http.client.IncompleteRead, urllib.error.URLError, TimeoutError):
            if attempt == attempts:
                raise


def get_json(url):
    return json.loads(get(url))


def github_latest(repo, prefix=""):
    """Наибольшая стабильная версия (не draft, не prerelease) среди свежих релизов.

    Релизы отдаются от новых к старым; страницы небольшие, потому что описания
    релизов объёмны (у Electron — десятки килобайт на релиз)."""
    pattern = re.compile(re.escape(prefix) + r"v?(\d+)\.(\d+)\.(\d+)")
    best = None
    for page in (1, 2, 3):
        for rel in get_json(f"https://api.github.com/repos/{repo}/releases?per_page=15&page={page}"):
            if rel["draft"] or rel["prerelease"]:
                continue
            m = pattern.fullmatch(rel["tag_name"])
            if not m:
                continue
            ver = tuple(int(x) for x in m.groups())
            if best is None or ver > best[0]:
                best = (ver, rel)
        if best:
            break
    ver, rel = best
    return {
        "version": ".".join(map(str, ver)),
        "date": rel["published_at"][:10],
        "source": rel["html_url"],
    }


def github_license(repo):
    lic = get_json(f"https://api.github.com/repos/{repo}").get("license") or {}
    return lic.get("spdx_id")


def python_latest():
    rels = get_json("https://www.python.org/api/v2/downloads/release/?is_published=true&pre_release=false")
    rels = [r for r in rels if re.fullmatch(r"Python \d+\.\d+\.\d+", r["name"])]
    top = max(rels, key=lambda r: tuple(int(x) for x in r["name"].split()[1].split(".")))
    return {"version": top["name"].split()[1], "date": top["release_date"][:10],
            "source": "https://www.python.org/downloads/"}


def node_versions():
    idx = get_json("https://nodejs.org/dist/index.json")
    current, lts = idx[0], next(r for r in idx if r["lts"])
    return {
        "version": f"{lts['version'].lstrip('v')} LTS «{lts['lts']}»; {current['version'].lstrip('v')} Current",
        "date": f"{lts['date']}; {current['date']}",
        "source": "https://nodejs.org/dist/index.json",
    }


def dotnet_latest():
    idx = get_json("https://dotnetcli.blob.core.windows.net/dotnet/release-metadata/releases-index.json")
    active = [c for c in idx["releases-index"] if c["support-phase"] == "active"]
    top = max(active, key=lambda c: tuple(int(x) for x in c["channel-version"].split(".")))
    return {"version": f"{top['latest-release']} ({top['release-type'].upper()})",
            "date": top["latest-release-date"],
            "source": "https://dotnet.microsoft.com/download/dotnet"}


def flutter_latest():
    data = get_json("https://storage.googleapis.com/flutter_infra_release/releases/releases_windows.json")
    stable = next(r for r in data["releases"] if r["hash"] == data["current_release"]["stable"])
    return {"version": stable["version"], "date": stable["release_date"][:10],
            "source": "https://docs.flutter.dev/release/archive"}


def npm_latest(package):
    meta = get_json(f"https://registry.npmjs.org/{package}")
    ver = meta["dist-tags"]["latest"]
    return {"version": ver, "date": meta["time"][ver][:10],
            "source": f"https://www.npmjs.com/package/{package}"}


def qt_latest():
    base = "https://download.qt.io/official_releases/qt/"
    minors = re.findall(r'href="(\d+)\.(\d+)/"', get(base))
    major, minor = max(((int(a), int(b)) for a, b in minors), key=lambda v: v)
    listing = get(f"{base}{major}.{minor}/")
    rows = re.findall(r'href="(\d+\.\d+\.\d+)/".*?<td align="right">(\d{2}-\w{3}-\d{4})', listing)
    ver, day = max(rows, key=lambda r: tuple(int(x) for x in r[0].split(".")))
    date = datetime.datetime.strptime(day, "%d-%b-%Y").date().isoformat()
    return {"version": ver, "date": date, "source": f"{base}{major}.{minor}/"}


def main():
    today = datetime.date.today().isoformat()
    github = {
        # ключ: (репозиторий, префикс тега)
        "Electron": ("electron/electron", ""),
        "Tauri 2": ("tauri-apps/tauri", "tauri-"),
        "React Native": ("facebook/react-native", ""),
        "Kotlin (Multiplatform)": ("JetBrains/kotlin", ""),
        "Compose Multiplatform": ("JetBrains/compose-multiplatform", ""),
        ".NET MAUI": ("dotnet/maui", ""),
        "Ionic Framework": ("ionic-team/ionic-framework", ""),
        "Capacitor": ("ionic-team/capacitor", ""),
        "Avalonia UI": ("AvaloniaUI/Avalonia", ""),
        "CMake": ("Kitware/CMake", ""),
        "Docker Engine": ("moby/moby", "docker-"),
        "WSL 2": ("microsoft/WSL", ""),
        "Wasmtime (среда WebAssembly)": ("bytecodealliance/wasmtime", ""),
    }
    result = {}
    for name, (repo, prefix) in github.items():
        result[name] = {**github_latest(repo, prefix), "license": github_license(repo)}
    for name, fn, repo in [
        ("Python", python_latest, "python/cpython"),
        ("Node.js", node_versions, "nodejs/node"),
        (".NET", dotnet_latest, "dotnet/runtime"),
        ("Flutter", flutter_latest, "flutter/flutter"),
        ("Qt 6", qt_latest, "qt/qtbase"),
    ]:
        result[name] = {**fn(), "license": github_license(repo)}
    result["Expo SDK"] = {**npm_latest("expo"), "license": github_license("expo/expo")}
    for item in result.values():
        item["accessed"] = today
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    for name, item in result.items():
        print(f"{name:32} {item['version']:36} {item['date']:24} {item['license']}")


if __name__ == "__main__":
    main()
