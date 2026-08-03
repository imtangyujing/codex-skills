# WeChat Exporter Backend

## Purpose

Use this reference when the input is a WeChat Official Account article link such as `mp.weixin.qq.com/s/...`.

The stable path on this machine is the local `wechat-article-exporter` backend. Prefer it before browser-based page opening, because public WeChat pages often return an environment-verification page to ordinary HTTP clients and some browser-control paths may be blocked.

## Local Components

- Article exporter: `~/Documents/Lark/tools/wechat-article-exporter`
- Local API: `http://127.0.0.1:3000`
- Optional credential service for metrics: `/Users/jay/Documents/Lark/tools/wxdown-service`

For this skill, the normal need is article title and body. Do not use the metrics credential path unless the user explicitly asks for WeChat article metrics, reads, likes, shares, or qbit review analysis.

## Start The Exporter

Check whether the local API is already listening:

```bash
lsof -iTCP:3000 -sTCP:LISTEN -nP
```

If it is not running, start it from the exporter directory:

```bash
wechat_exporter_dir="${HOME}/Documents/Lark/tools/wechat-article-exporter"
if [ ! -d "$wechat_exporter_dir" ]; then
  echo "WeChat exporter directory not found: $wechat_exporter_dir" >&2
  exit 1
fi

wechat_exporter_dir="$(cd "$wechat_exporter_dir" && pwd -P)"
wechat_exporter_entry="${wechat_exporter_dir}/.output/server/index.mjs"
if [ ! -f "$wechat_exporter_entry" ]; then
  echo "WeChat exporter server entry not found: $wechat_exporter_entry" >&2
  exit 1
fi

cd "$wechat_exporter_dir"
PORT=3000 HOST=127.0.0.1 node "$wechat_exporter_entry"
```

Keep the service running only as long as needed for the current task. If the agent started it in the current turn, stop it before final delivery unless ongoing use is helpful.

## Fetch Article Body

Use the public download API.

Fetch JSON when title, metadata, HTML body, or image context may be useful:

```bash
curl -sS --get 'http://127.0.0.1:3000/api/public/v1/download' \
  --data-urlencode 'url=<WECHAT_URL>' \
  --data-urlencode 'format=json' \
  -o article.json
```

Fetch readable text when the task only needs the article body:

```bash
curl -sS --get 'http://127.0.0.1:3000/api/public/v1/download' \
  --data-urlencode 'url=<WECHAT_URL>' \
  --data-urlencode 'format=text' \
  -o article.txt
```

Fetch Markdown when the task asks to preserve article structure or extract a section such as interview Q&A:

```bash
curl -sS --get 'http://127.0.0.1:3000/api/public/v1/download' \
  --data-urlencode 'url=<WECHAT_URL>' \
  --data-urlencode 'format=markdown' \
  -o article.md
```

In JSON output, the original article HTML is usually in `content_noencode`. The exporter may also return fields such as `title`, `author`, and publication metadata.

Before choosing the final filename,apply the `Final Filename Contract` in `references/article-note.md`. When exporter Markdown or JSON does not expose a publication date,fetch the original WeChat URL as untouched raw HTML and retain it in the working directory so the contract can inspect the page-script time. Normalized exporter HTML and Markdown may omit the script that fills `#publish_time`.

## Conservative Markdown Cleanup

After fetching WeChat Markdown, apply a conservative mechanical cleanup before routing the article into downstream note or source-material workflows.

Cleanup goals:

- Remove clear WeChat shell noise, including leading CSS blocks, immersive-reader prompts, novel-reader prompts, and standalone UI lines such as `在小说阅读器读本章`, `去阅读`, and `在小说阅读器中沉浸阅读`.
- Collapse excessive blank lines: replace any run of 3 or more blank lines with exactly one blank line.
- Trim trailing spaces on every line.
- Keep original title, author/source metadata, headings, body text, image Markdown, links, blockquotes, and tables.
- Keep intentional short paragraphing. Do not merge adjacent non-empty text lines, rewrite prose, remove image links, or summarize content.

Use these rules only when the removed content is clearly page chrome or empty spacing. If a line may be article body, keep it.

## Routing Rules

- For ordinary article-note tasks, pass the fetched text or Markdown into `references/article-note.md`.
- For user requests that ask to extract the already-edited interview Q&A from a WeChat article, use the Markdown output when available, keep the Q&A section, remove article boilerplate, and route the final Markdown through the parent skill.
- For WeChat articles that are mainly embedded audio/video or depend on a transcript outside the article body, return to the parent skill and use the audio/video or transcript branch.

## Failure Handling

- Expand `~` through `${HOME}` and verify both the local exporter directory and `.output/server/index.mjs` before starting. If either path is missing, say that the local WeChat exporter is unavailable and fall back to any source text the user supplied.
- If the API returns a verification page, empty body, or incomplete body, state that the local exporter could not fetch the article cleanly and ask the user for copied article text or a saved HTML/Markdown file.
- Do not use Chrome or browser-control access for a `mp.weixin.qq.com/s/...` link when that browser action is blocked by policy.
- Do not print cookies, tokens, `key`, `pass_ticket`, or `appmsg_token` in chat or generated files.
