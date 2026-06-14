#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path


EXPORTER_DIR = Path("/Users/jay/Documents/Lark/tools/wechat-article-exporter")
WXD_DIR = Path("/Users/jay/Documents/Lark/tools/wxdown-service")
CREDENTIALS = WXD_DIR / "resources/data/credentials.json"
LOG_DIR = Path("/tmp/qbit-wechat-review-logs")
PROXY_HOST = "127.0.0.1"
PROXY_PORT = "65000"
MIN_COOKIE_LENGTH = 500


def run(args, cwd=None, capture=True, check=False):
    return subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=capture,
        check=check,
    )


def is_listening(port):
    return run(["lsof", f"-iTCP:{port}", "-sTCP:LISTEN", "-nP"], capture=True).returncode == 0


def start_services():
    if not EXPORTER_DIR.exists():
        raise SystemExit(f"missing article exporter: {EXPORTER_DIR}")
    if not WXD_DIR.exists():
        raise SystemExit(f"missing credential service: {WXD_DIR}")
    if not (WXD_DIR / ".venv/bin/python").exists():
        raise SystemExit(f"missing credential service venv: {WXD_DIR / '.venv/bin/python'}")

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    if not is_listening("3000"):
        with open(LOG_DIR / "wechat-article-exporter.log", "ab") as log:
            subprocess.Popen(
                ["node", ".output/server/index.mjs"],
                cwd=str(EXPORTER_DIR),
                stdout=log,
                stderr=log,
                env={**os.environ, "PORT": "3000", "HOST": "127.0.0.1"},
            )
    if not (is_listening("65000") and is_listening("65001")):
        with open(LOG_DIR / "wxdown-service.log", "ab") as log:
            subprocess.Popen(
                [str(WXD_DIR / ".venv/bin/python"), "main.py", "-d"],
                cwd=str(WXD_DIR),
                stdout=log,
                stderr=log,
            )

    deadline = time.time() + 30
    while time.time() < deadline:
        if is_listening("3000") and is_listening("65000") and is_listening("65001"):
            return
        time.sleep(1)
    raise SystemExit("local WeChat services did not become ready")


def parse_proxy_output(text):
    info = {}
    for line in text.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            info[key.strip()] = value.strip()
    return info


def get_proxy(kind):
    cmd = ["networksetup", "-getwebproxy" if kind == "http" else "-getsecurewebproxy", "Wi-Fi"]
    result = run(cmd, capture=True, check=True)
    return parse_proxy_output(result.stdout)


def set_proxy(kind, host, port, enabled=True):
    set_cmd = "-setwebproxy" if kind == "http" else "-setsecurewebproxy"
    state_cmd = "-setwebproxystate" if kind == "http" else "-setsecurewebproxystate"
    run(["networksetup", set_cmd, "Wi-Fi", host, str(port)], capture=True, check=True)
    run(["networksetup", state_cmd, "Wi-Fi", "on" if enabled else "off"], capture=True, check=True)


def restore_proxy(saved):
    for kind in ("http", "https"):
        info = saved[kind]
        enabled = info.get("Enabled", "No").lower() == "yes"
        server = info.get("Server") or PROXY_HOST
        port = info.get("Port") or "0"
        set_proxy(kind, server, port, enabled)


def load_credentials():
    if not CREDENTIALS.exists() or not CREDENTIALS.stat().st_size:
        return []
    try:
        return json.loads(CREDENTIALS.read_text())
    except Exception:
        return []


def credential_status(account_name, started_ms):
    latest = None
    for item in load_credentials():
        name = item.get("name") or ""
        timestamp = int(item.get("timestamp") or 0)
        if name != account_name or timestamp < started_ms:
            continue
        if latest is None or timestamp > int(latest.get("timestamp") or 0):
            latest = item
    if not latest:
        return {"ready": False, "reason": "missing"}
    cookie_len = len(latest.get("set_cookie") or "")
    has_token = bool(latest.get("appmsg_token"))
    ready = cookie_len >= MIN_COOKIE_LENGTH and has_token
    reason = "ready" if ready else f"incomplete cookie_len={cookie_len} token={has_token}"
    return {"ready": ready, "reason": reason}


def credential_ready(account_name, started_ms):
    return credential_status(account_name, started_ms)["ready"]


def open_in_wechat(url):
    for app_name in ("WeChat", "微信"):
        result = run(["open", "-a", app_name, url], capture=True)
        if result.returncode == 0:
            return app_name
    run(["open", url], capture=True, check=True)
    return "default browser"


def parse_account(value):
    if "=" not in value:
        raise argparse.ArgumentTypeError("account must be NAME=URL")
    name, url = value.split("=", 1)
    name = name.strip()
    url = url.strip()
    if not name or not url:
        raise argparse.ArgumentTypeError("account must be NAME=URL")
    return name, url


def main():
    parser = argparse.ArgumentParser(description="Refresh WeChat article credentials by opening links.")
    parser.add_argument("--account", action="append", type=parse_account, required=True, help="NAME=URL")
    parser.add_argument("--timeout", type=int, default=90)
    args = parser.parse_args()

    start_services()
    started_ms = int(time.time() * 1000)
    saved = {"http": get_proxy("http"), "https": get_proxy("https")}
    opened = []
    try:
        set_proxy("http", PROXY_HOST, PROXY_PORT, True)
        set_proxy("https", PROXY_HOST, PROXY_PORT, True)
        for name, url in args.account:
            opener = open_in_wechat(url)
            opened.append((name, opener))
            time.sleep(2)

        wanted = [name for name, _ in args.account]
        deadline = time.time() + args.timeout
        while time.time() < deadline:
            statuses = {name: credential_status(name, started_ms) for name in wanted}
            ready = [name for name in wanted if statuses[name]["ready"]]
            missing = [name for name in wanted if name not in ready]
            print(
                json.dumps(
                    {
                        "ready": ready,
                        "missing": missing,
                        "status": statuses,
                        "opened": opened,
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )
            if not missing:
                return 0
            time.sleep(3)
        return 2
    finally:
        restore_proxy(saved)


if __name__ == "__main__":
    sys.exit(main())
