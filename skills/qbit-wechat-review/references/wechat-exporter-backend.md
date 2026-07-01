# WeChat Exporter Backend

## Validated Local Components

- Account search/article list/article body JSON: `~/Documents/Lark/tools/wechat-article-exporter`
- Frontend/API service: `http://127.0.0.1:3000`

The local backend handles `mp.weixin.qq.com/s/...` article body retrieval and title/media-based article discovery. For title-only inputs, use local account search + article list first; use ordinary web search only as fallback.

Metric retrieval through `wxdown-service`, proxy capture, and `getappmsgext` is offline. Use **用户指标来源**（see SKILL.md §Terminology）for metrics.

## First-Run Install

Run this section before the first review task on a new computer, or when `~/Documents/Lark/tools/wechat-article-exporter` is missing or `http://127.0.0.1:3000/api/public/v1/download` is unavailable.

### Clone And Build

```bash
mkdir -p ~/Documents/Lark/tools

git clone https://github.com/wechat-article/wechat-article-exporter.git \
  ~/Documents/Lark/tools/wechat-article-exporter
```

If the directory already exists, run `git pull` instead.

```bash
cd ~/Documents/Lark/tools/wechat-article-exporter
npx -y yarn@1.22.22 install --frozen-lockfile
NODE_OPTIONS=--max-old-space-size=4096 npx -y yarn@1.22.22 build
```

### Start And Verify

```bash
cd ~/Documents/Lark/tools/wechat-article-exporter
DEBUG_KEY=qbit-local PORT=3000 HOST=127.0.0.1 node .output/server/index.mjs
```

If rebuilding is needed:

```bash
NODE_OPTIONS=--max-old-space-size=4096 npx -y yarn@1.22.22 build
```

Verify:

```bash
lsof -iTCP:3000 -sTCP:LISTEN -nP
```

When setup succeeds, tell the user: `文章列表和正文抓取准备好了，指标请提供后台截图。`

## Auth For Article List

Body download does not require login, but account search and article list require the exporter backend to hold a valid `auth-key`.

Check auth:

```bash
curl -sS 'http://127.0.0.1:3000/api/public/v1/authkey'
```

If it returns `{"code":-1,...}`, open `http://127.0.0.1:3000` and scan-login with a WeChat public-platform account. Do not ask for `app_secret`.

For Python scripts, pass auth in either form:

```bash
# Preferred when the service was started with DEBUG_KEY=qbit-local.
export QBIT_WECHAT_EXPORTER_DEBUG_KEY=qbit-local

# Or pass the browser/API auth-key explicitly when known.
export QBIT_WECHAT_EXPORTER_AUTH_KEY=<AUTH_KEY>
```

The scripts send both `X-Auth-Key` and `auth-key` cookie when `QBIT_WECHAT_EXPORTER_AUTH_KEY` is available. When only `QBIT_WECHAT_EXPORTER_DEBUG_KEY` is set, scripts read `/api/_debug?key=...` and reuse the latest local auth-key.

## Fetch Account And Article List

Search account:

```bash
curl -sS --get 'http://127.0.0.1:3000/api/public/v1/account' \
  --data-urlencode 'keyword=<MEDIA_NAME>' \
  --data-urlencode 'begin=0' \
  --data-urlencode 'size=5'
```

Fetch/search articles:

```bash
curl -sS --get 'http://127.0.0.1:3000/api/public/v1/article' \
  --data-urlencode 'fakeid=<FAKEID>' \
  --data-urlencode 'begin=0' \
  --data-urlencode 'size=10' \
  --data-urlencode 'keyword=<TITLE_OR_TOPIC_KEYWORD>'
```

Use returned `articles[]` as article candidates. Field mapping:

| Exporter field | Review use |
|---|---|
| `title` | `文章标题` and title matching |
| `link` | `文章链接`, then body download |
| `cover`/`cover_img` | WeChat cover reference when needed |
| `digest` | disambiguation hint |
| `create_time`/`update_time` | `发布时间` fallback |
| `aid`/`appmsgid` | stable candidate identity |
| `itemidx` | `发布位置` hint when reliable |

## Fetch Article Body

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

## Base-First Delivery

For review runs, do not generate local delivery files by default. The normal path is:

1. Fetch article JSON/body in memory.
2. Read metrics from **用户指标来源**.
3. Build the Feishu Base payload.
4. Search by `文章链接` or `文章标题`.
5. Update or create the record.
6. Upload readable article Markdown to `附件` when the field exists.

For same-topic runs:

1. Parse one topic name plus three links for 量子位, 新智元, 机器之心.
2. Fetch body for all three with the local backend; read metrics from **用户指标来源**.
3. Upsert 量子位 article into `文章复盘`.
4. Upsert 新智元 and 机器之心 into `竞品文章池`.
5. Upsert one `同题分析` row, link the three records, write structured analysis.
6. If competitor links are missing, use local account search + article list before web-search fallback.

The Markdown attachment can be a temporary local intermediate. Only write extra debug files when the user asks or when preserving evidence for a failed run. Debug file location:

```text
~/Documents/Lark/exports/wechat-article-test/
```
