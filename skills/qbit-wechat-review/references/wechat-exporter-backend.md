# WeChat Exporter Backend

## Validated Local Components

- Article body/base JSON: `/Users/jay/Documents/Lark/tools/wechat-article-exporter`
- Credential capture: `/Users/jay/Documents/Lark/tools/wxdown-service`
- Frontend/API service: `http://127.0.0.1:3000`
- Credential proxy: `127.0.0.1:65000`
- Credential websocket: `wss://127.0.0.1:65001`

The current backend replaces browser-only public page extraction for `mp.weixin.qq.com/s/...` tasks. For 量子位 title-only inputs, resolve a WeChat URL with local `appmsgpublish` search first. Use qbitai.com only when `appmsgpublish` cannot resolve a reliable WeChat URL or the local backend cannot get a complete article body.

Local `wxdown-service/resources/credential.py` must capture `appmsg_token` from both `/mp/getappmsgext` and `/mp/jsmonitor`. Desktop WeChat often exposes the token through `/mp/jsmonitor` before any explicit `getappmsgext` request appears in logs.

## Qbit-Owned Article Entry Points

Use these two fixed entry points for 量子位自有文章:

- Link input: when the user provides `mp.weixin.qq.com/s/...`, use that link directly, fetch body/base JSON with the local download API, then fetch metrics with `getappmsgext`.
- Title input: when the user provides only article titles, use the local backend login session and `appmsgpublish` search to resolve each title to a WeChat URL. Then run the same link input path for body, metrics, author extraction, attachment upload, and review writing.
- qbitai.com fallback: use only when `appmsgpublish` cannot resolve a reliable WeChat URL or the local WeChat body fetch is incomplete.
- A title/link discovery pass is incomplete by itself. Do not stop after writing only title, date, link, read count, or publication position.

## First-Run Install And Credential Warmup

Run this section before the first review task on a new computer, or when either local backend is missing.

### Install Local Repositories

Create the tools directory:

```bash
mkdir -p /Users/jay/Documents/Lark/tools
```

Clone the article exporter:

```bash
git clone https://github.com/wechat-article/wechat-article-exporter.git \
  /Users/jay/Documents/Lark/tools/wechat-article-exporter
```

Clone the credential service:

```bash
git clone https://github.com/wechat-article/wxdown-service.git \
  /Users/jay/Documents/Lark/tools/wxdown-service
```

If either directory already exists, run `git pull` in that directory instead of cloning again.

Install and build `wechat-article-exporter`:

```bash
cd /Users/jay/Documents/Lark/tools/wechat-article-exporter
npx -y yarn@1.22.22 install --frozen-lockfile
NODE_OPTIONS=--max-old-space-size=4096 npx -y yarn@1.22.22 build
```

Install `wxdown-service`:

```bash
cd /Users/jay/Documents/Lark/tools/wxdown-service
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### Trust The mitmproxy Certificate

Start `wxdown-service` once to generate `~/.mitmproxy/mitmproxy-ca-cert.pem`:

```bash
cd /Users/jay/Documents/Lark/tools/wxdown-service
.venv/bin/python main.py -d
```

If the certificate is not trusted, add it to the macOS System Keychain:

```bash
sudo security add-trusted-cert -d -r trustRoot \
  -k /Library/Keychains/System.keychain \
  ~/.mitmproxy/mitmproxy-ca-cert.pem
```

Verify trust:

```bash
security verify-cert -c ~/.mitmproxy/mitmproxy-ca-cert.pem
```

Expected success text includes `certificate verification successful`.

If the user cannot enter the sudo password in the terminal, ask them to open Keychain Access, import `~/.mitmproxy/mitmproxy-ca-cert.pem` into the `System` keychain, then set the certificate trust to `Always Trust`.

### Start Services

Start `wechat-article-exporter`:

```bash
cd /Users/jay/Documents/Lark/tools/wechat-article-exporter
PORT=3000 HOST=127.0.0.1 node .output/server/index.mjs
```

Start `wxdown-service`:

```bash
cd /Users/jay/Documents/Lark/tools/wxdown-service
.venv/bin/python main.py -d
```

Verify listeners:

```bash
lsof -iTCP:3000 -sTCP:LISTEN -nP
lsof -iTCP:65000 -sTCP:LISTEN -nP
lsof -iTCP:65001 -sTCP:LISTEN -nP
```

### Warm Up The Three AI Media Credentials

Save the current proxy settings before changing them:

```bash
networksetup -getwebproxy Wi-Fi
networksetup -getsecurewebproxy Wi-Fi
```

Set Wi-Fi HTTP and HTTPS proxy to `127.0.0.1:65000`:

```bash
networksetup -setwebproxy Wi-Fi 127.0.0.1 65000
networksetup -setsecurewebproxy Wi-Fi 127.0.0.1 65000
networksetup -setwebproxystate Wi-Fi on
networksetup -setsecurewebproxystate Wi-Fi on
```

Use the auto-refresh helper to open these three articles and wait for credentials:

```bash
python3 scripts/auto_refresh_wechat_credentials.py \
  --account '量子位=https://mp.weixin.qq.com/s/xOm_f8iEmdHjiD9v3p3wFg' \
  --account '新智元=https://mp.weixin.qq.com/s/jqBsN_2UDie47GVQj8L5MQ' \
  --account '机器之心=https://mp.weixin.qq.com/s/BQbWcPzPKv7gn1sGbR3ixw'
```

The helper opens links with desktop WeChat when available, falls back to the default URL handler, listens for fresh `appmsg_token` values, and restores the previous macOS proxy settings in a `finally` block. If it times out, ask the user to confirm desktop WeChat is logged in and manually open the missing article links.

Monitor credentials manually only when debugging:

```bash
python3 - <<'PY'
import json
from pathlib import Path

p = Path('/Users/jay/Documents/Lark/tools/wxdown-service/resources/data/credentials.json')
if not p.exists() or not p.stat().st_size:
    print('no credentials')
    raise SystemExit

for item in json.loads(p.read_text()):
    print(item.get('name') or item.get('biz'), item.get('biz'))
PY
```

Do not print cookies, `key`, `pass_ticket`, `appmsg_token`, or raw credential URLs.

If manual proxy capture was used, restore the previous proxy settings immediately. In the validated local setup the normal proxy was:

```bash
networksetup -setwebproxy Wi-Fi 127.0.0.1 7897
networksetup -setsecurewebproxy Wi-Fi 127.0.0.1 7897
networksetup -setwebproxystate Wi-Fi on
networksetup -setsecurewebproxystate Wi-Fi on
```

Do not assume `127.0.0.1:7897` on other computers. Always restore the values saved before capture.

When warmup succeeds, tell the user:

```text
准备好了，可以开始使用。
```

## Start And Verify Services

From `wechat-article-exporter`:

```bash
PORT=3000 HOST=127.0.0.1 node .output/server/index.mjs
```

If rebuilding is needed:

```bash
NODE_OPTIONS=--max-old-space-size=4096 npx -y yarn@1.22.22 build
```

From `wxdown-service`:

```bash
DYLD_LIBRARY_PATH=/opt/homebrew/opt/expat/lib .venv/bin/python main.py -d
```

Verify listeners:

```bash
lsof -iTCP:3000 -sTCP:LISTEN -nP
lsof -iTCP:65000 -sTCP:LISTEN -nP
lsof -iTCP:65001 -sTCP:LISTEN -nP
```

## Fetch Article Body

Use the public download endpoint:

```bash
curl -sS --get 'http://127.0.0.1:3000/api/public/v1/download' \
  --data-urlencode 'url=<WECHAT_URL>' \
  --data-urlencode 'format=json' \
  -o article.json

curl -sS --get 'http://127.0.0.1:3000/api/public/v1/download' \
  --data-urlencode 'url=<WECHAT_URL>' \
  --data-urlencode 'format=text' \
  -o article.txt
```

In `article.json`, the article HTML body is normally `content_noencode`. Convert it to Markdown when a readable file is useful.

## Capture Credentials For Metrics

Credentials are scoped by公众号`__biz`. One valid credential can fetch metrics for multiple articles under the same公众号 during its validity window.

1. Check whether `/Users/jay/Documents/Lark/tools/wxdown-service/resources/data/credentials.json` already contains the target公众号 with a fresh `set_cookie` and `appmsg_token`.
2. If missing or stale, run `scripts/auto_refresh_wechat_credentials.py --account '<name>=<url>'` for the target accounts.
3. The helper saves the current macOS proxy settings, sets Wi-Fi HTTP and HTTPS proxy to `127.0.0.1:65000`, opens the article URLs, waits for fresh credentials, and restores the previous proxy settings.
4. Ask the user to open or refresh articles manually only if the helper times out or desktop WeChat is not logged in.

Useful proxy commands:

```bash
networksetup -getwebproxy Wi-Fi
networksetup -getsecurewebproxy Wi-Fi
networksetup -setwebproxy Wi-Fi 127.0.0.1 65000
networksetup -setsecurewebproxy Wi-Fi 127.0.0.1 65000
networksetup -setwebproxystate Wi-Fi on
networksetup -setsecurewebproxystate Wi-Fi on
```

Restore to the saved values. In the validated local setup, the user's normal proxy was `127.0.0.1:7897`, but do not assume that in future runs.

## Fetch Metrics

Call `https://mp.weixin.qq.com/mp/getappmsgext` with captured credential values from the matching `__biz`. Required values come from the captured article URL and `set_cookie`:

- `__biz`
- `mid`
- `idx`
- `sn`
- `key`
- `pass_ticket`
- `uin`
- `appmsg_token`
- cookie header derived from `set_cookie`

Use POST with body fields like:

```text
r=<random>
__biz=<biz>
mid=<mid>
idx=<idx>
sn=<sn>
is_only_read=1
is_temp_url=0
appmsg_type=9
reward_uin_count=0
```

Read metrics from `response.appmsgstat`:

- `read_num` -> `阅读数 R`
- `old_like_num` -> `点赞数 L`
- `like_num` -> `在看数`
- `share_num` -> `转发数 S`
- `collect_num` -> `收藏数`
- `comment_count` -> `评论数 C` when returned
- `star_num` -> optional `星标` field if present

If `show_comment=0` on the article JSON and `comment_count` is absent, treat comments as unavailable. Leave `评论数 C` blank and avoid zero-comment claims in `AI复盘`.

## Base-First Delivery

For qbit-wechat-review runs, do not generate local delivery files by default. The normal end-to-end path is:

1. Fetch article JSON/body in memory.
2. Fetch metrics in memory.
3. Build the Feishu Base payload.
4. Search by `文章链接` or `文章标题`.
5. Update the matched record or create a new record.
6. Upload the readable article Markdown to the record's `附件` field when the field exists.

For same-topic analysis runs:

1. Parse one topic name plus three links for 量子位, 新智元, and 机器之心.
2. Fetch body and metrics for all three links with the same local WeChat backend.
3. Upsert the 量子位 article into `文章复盘`.
4. Upsert 新智元 and 机器之心 articles into `竞品文章池`.
5. Upsert one `同题分析` row, link the three article records, snapshot metrics, set `同题状态`, and write structured analysis fields.
6. Do not use `appmsgpublish` for competitor accounts. Competitor articles require user-provided WeChat links in V1.

The Markdown attachment can be a temporary/local intermediate because Base attachment upload requires a local file. Other local files are optional. Only write extra debug files when the user asks for files, when debugging the backend, or when preserving evidence for a failed run. If local files are needed, place them under a descriptive subdirectory in:

```text
/Users/jay/Documents/Lark/exports/wechat-article-test/
```

Optional debug files:

- `article.json`
- `article.txt`
- `article.md`
- `getappmsgext.json`
- `metrics.json`
- `metrics.md`

Do not expose raw credentials or personal identifiers in these debug files.
