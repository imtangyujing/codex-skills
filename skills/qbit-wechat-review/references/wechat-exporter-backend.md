# WeChat Exporter Backend

## Validated Local Components

- Article body/base JSON: `/Users/jay/Documents/Lark/tools/wechat-article-exporter`
- Frontend/API service: `http://127.0.0.1:3000`

The current backend replaces browser-only public page extraction for `mp.weixin.qq.com/s/...` tasks. For title-only inputs, resolve an article URL with ordinary web search first.

Metric retrieval through `wxdown-service`, proxy capture, and `getappmsgext` is temporarily offline in the `Hybrid` branch. Use user-provided WeChat backend screenshots or user-provided metric tables for metrics.

## Qbit-Owned Article Entry Points

Use these two fixed entry points for 量子位自有文章:

- Link input: when the user provides `mp.weixin.qq.com/s/...`, use that link directly and fetch body/base JSON with the local download API. Read metrics from user-provided screenshots or tables.
- Title input: when the user provides only article titles, use ordinary web search to resolve each title to an article URL. Take the first usable high-confidence result as the body source. If the result is a WeChat URL, run the same link input path for body, screenshot/table metrics, author extraction, attachment upload, and review writing. If the result is a repost or media page, use it for body context and attachment only.
- Do not use any fixed official-site path for title-only inputs.
- A title/link discovery pass is incomplete by itself. Do not stop after writing only title, date, link, read count, or publication position.

## First-Run Install

Run this section before the first review task on a new computer, or when the article exporter is missing.

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

If the directory already exists, run `git pull` in that directory instead of cloning again.

Install and build `wechat-article-exporter`:

```bash
cd /Users/jay/Documents/Lark/tools/wechat-article-exporter
npx -y yarn@1.22.22 install --frozen-lockfile
NODE_OPTIONS=--max-old-space-size=4096 npx -y yarn@1.22.22 build
```

### Start Services

Start `wechat-article-exporter`:

```bash
cd /Users/jay/Documents/Lark/tools/wechat-article-exporter
PORT=3000 HOST=127.0.0.1 node .output/server/index.mjs
```

Verify listeners:

```bash
lsof -iTCP:3000 -sTCP:LISTEN -nP
```

When setup succeeds, tell the user:

```text
正文抓取准备好了，指标请提供后台截图。
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

Verify listeners:

```bash
lsof -iTCP:3000 -sTCP:LISTEN -nP
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

## Read Metrics From Screenshots

Use user-provided WeChat backend screenshots, OCR output, or user-provided metric tables. Map fields as:

- `阅读`/`阅读数` -> `阅读数 R`
- `点赞`/`点赞数` -> `点赞数 L`
- `评论`/`评论数` -> `评论数 C`
- `分享`/`转发`/`转发数` -> `转发数 S`
- `收藏`/`收藏数` -> `收藏数`
- `在看`/`在看数` -> `在看数`

If the screenshot omits a metric, leave that field blank. Write `0` only when the screenshot or table explicitly shows zero.

## Base-First Delivery

For qbit-wechat-review runs, do not generate local delivery files by default. The normal end-to-end path is:

1. Fetch article JSON/body in memory.
2. Read metrics from screenshots or user-provided tables.
3. Build the Feishu Base payload.
4. Search by `文章链接` or `文章标题`.
5. Update the matched record or create a new record.
6. Upload the readable article Markdown to the record's `附件` field when the field exists.

For same-topic analysis runs:

1. Parse one topic name plus three links for 量子位, 新智元, and 机器之心.
2. Fetch body for all three links with the same local WeChat backend, then read metrics from user-provided screenshots or tables.
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
- `metrics.json`
- `metrics.md`

Do not expose sensitive identifiers in these debug files.
