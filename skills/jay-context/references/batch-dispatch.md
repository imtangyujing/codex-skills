# Batch Dispatch

Read this reference when the user provides two or more distinct URLs in one request.

## Contract

The current main agent is the batch coordinator. It classifies sources,creates jobs,assigns one end-to-end worker per source,waits for completion,verifies file existence,and summarizes results.

Each worker owns exactly one source from acquisition through final Markdown. A worker must not call `spawn_agent`,delegate polishing,or create acquisition,ASR,note,or validation agents.

## Input Normalization

1. Trim surrounding whitespace from each URL.
2. Preserve query parameters,fragments,and input order.
3. Deduplicate only exact duplicate URL strings. Keep the first occurrence.
4. Assign stable IDs in input order: `J001`,`J002`,`J003`,and so on.
5. Use `~/Downloads/<source-slug>/` as the working directory. Use `~/Downloads/jay-context-<job_id>/` until a reliable slug is available.
6. Resolve `output_language` once in the coordinator and copy the same value into every job record.

Do not create a batch index Markdown file unless the user explicitly asks for one.

## Classification

Perform a lightweight classification before dispatch. Inspect the domain,file extension,title,content type,or visible metadata when the URL alone is ambiguous. Do not fetch full media or draft source content in the coordinator.

Use these source types and routes:

| source_type | Typical sources | worker_route | resource_class |
|---|---|---|---|
| `article` | Ordinary article,newsletter,complete web page | `article-note` | `network` |
| `wechat` | `mp.weixin.qq.com` | `wechat-exporter` then `article-note` | `network` |
| `feishu_document` | Feishu Docx or wiki | Lark document fetch,then reclassify inside the worker | `network` |
| `audio_video` | YouTube,Bilibili,podcast,direct media | `audio-to-text` then `interview-polish` | `network_asr` |
| `existing_transcript` | Caption page,transcript document,rough interview text | `interview-polish` or `article-note` | `text` |
| `event` | Salon,panel,conference,workshop,roadshow | `event-transcript` plus `interview-polish` | `text_or_asr` |
| `unknown_web` | Ambiguous accessible URL | Full Source Router inside the worker | `network` |

Create one job record per distinct URL:

```json
{
  "job_id": "J001",
  "source_url": "https://example.com/source",
  "source_type": "article",
  "worker_route": "article-note",
  "work_dir": "/Users/name/Downloads/source-slug",
  "resource_class": "network",
  "output_language": "zh-CN"
}
```

## Scheduling

- Keep the coordinator in the main agent.
- Use the currently available child-agent capacity. In a four-slot environment,start at most three source workers at once.
- Start jobs in input order.
- When a worker completes or fails,start the next queued job immediately.
- Let article fetching,caption inspection,local media downloads,Doubao Flash recognition,and other network work proceed in parallel.
- Continue scheduling after individual failures. Do not retry automatically.

If collaboration tools are unavailable,process the jobs sequentially in the current agent while preserving the same job records and result contract.

## Worker Prompt Contract

Give each worker exactly one job record and the absolute Jay-Context skill path. Include these instructions:

```text
Use the Jay-Context skill to process exactly one source end to end.

Job: <job JSON>
Jay-Context path: <absolute skill path>
Coordinator target: <canonical coordinator task name>

Read SKILL.md,the Final Filename Contract in article-note.md,and only the route references required by this job. You are the sole source owner. Complete acquisition,ASR when needed,language conversion,temporary-source cleanup,polishing,note packaging,filename selection,routing,and self-check in this agent. Use the job's output_language for every semantic deliverable and localized structure label.

Do not call spawn_agent. Do not delegate acquisition,ASR,polishing,note writing,or validation. Treat interview-polish,article-note,and event-transcript as execution rules.

Return only the Worker Result JSON.
```

## End-to-End Worker Rules

For audio/video polished delivery,the worker executes:

```text
check page transcript or captions
→ download media locally when needed
→ run eligible ASR route
→ convert semantic text to output_language
→ save only the converted transcript and content-free processing status
→ remove source-language captions,transcripts,and response bodies
→ read interview-polish.md
→ polish in the same agent
→ generate the localized notes section from the polished body
→ apply the Final Filename Contract in article-note.md
→ write one final Markdown file
→ self-check
```

Raw transcript readiness never creates another worker. Existing transcripts and event materials follow the same one-owner rule.

Before returning,the worker confirms:

- Expected converted transcript and content-free processing status exist when ASR or captions ran.
- `source-media.<ext>` and content-free `source-media.info.json` exist for platform-page downloads.
- Final Markdown exists at the routed path.
- The filename uses the strongest first-hand source and exactly one primary topic.
- The filename date matches `source_date`,and `date_source` identifies the evidence used.
- A WeChat filename follows the page-script date priority and never uses the task execution or file-system date.
- The localized title is first,the localized notes heading precedes the converted source or polished body,and no duplicate note section exists.
- For URL-based sources,the final Markdown ends with the localized italicized source line containing the exact `source_url` from the job record and has no dedicated source heading.
- No source-language article body,caption,transcript,quotation page,or ASR response body remains.
- No second note file was created.

## Worker Result

Return one JSON object:

```json
{
  "job_id": "J001",
  "status": "completed",
  "source_type": "article",
  "output_language": "zh-CN",
  "source_date": "20260720",
  "date_source": "source_metadata",
  "engine": null,
  "local_media_path": null,
  "converted_text_path": null,
  "processing_status_path": null,
  "final_path": "/absolute/path/final.md",
  "error": null,
  "retry_hint": null
}
```

Use `status: "failed"` when the source cannot be completed. Set `final_path` to `null`,put the concise failure in `error`,and give a targeted next action in `retry_hint`. Do not retry automatically.

Use `source_date: "未知"` and `date_source: "unknown"` only for a WeChat source whose raw page script contains none of `createTime`,`oriCreateTime`,or `ori_create_time`.

## Coordinator Delivery

Wait for every queued job to reach `completed` or `failed`. Verify that each reported `final_path` exists and that its filename date field matches the reported `source_date`. Confirm `date_source` is present. Do not reopen or rewrite worker-created Markdown unless the user requests review,excerpting,or debugging.

Report results in original input order with source URL,status,engine,and final path or error. Keep one final Markdown per source by default.

When the user explicitly requests cross-source synthesis,finish all source jobs first. The coordinator may then create one synthesis worker and pass only the completed final Markdown paths.
