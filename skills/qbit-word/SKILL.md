---
name: qbit-word
description: "Export confirmed Feishu/Lark outline documents into the Qbit Word outline template. Use when the user gives a Feishu wiki/docx URL and asks to download/export a finalized outline as Word, paste it 1:1 into the local XX-提纲.docx template, rename it from the Feishu title, or save the resulting .docx in Downloads."
---

# Qbit Outline Word

## Workflow

Use `scripts/feishu_outline_to_word.py` for the whole operation. The script:

1. Inspects a Feishu wiki/docx URL with `lark-cli drive +inspect --as user`.
2. Exports the resolved docx to Word.
3. Merges the exported body into the local Qbit template.
4. Removes Feishu AI-generated content disclaimer paragraphs such as `内容由AI生成，请谨慎参考`.
5. Forces the first non-empty banner title paragraph to be centered.
6. Saves the finished `.docx` to `~/Downloads` by default.

Run:

```bash
python3 /Users/lzw/.codex/skills/qbit-word/scripts/feishu_outline_to_word.py '<FEISHU_URL>'
```

## Defaults

- Template: `assets/qbit-template.docx` inside this skill directory
- Output folder: `~/Downloads`
- Output filename: Feishu document title plus `.docx`
- Identity: `--as user`

## Options

Use `--name '<filename-without-docx>'` to override the output filename.
Use `--output-dir '<folder>'` only when the user explicitly wants a different destination.
Use `--keep-export` only when the user wants the raw Feishu export retained next to the final Word file.
Use `--drop-from-heading '<heading-text>'` when the user wants to remove a final draft or appendix section from that heading through the end of the body, for example `--drop-from-heading '草稿'`.
Template header/banner images are kept by default. Source document media files are copied with collision-safe names so they do not overwrite template banner assets.


## Validation

After running, verify at least the script JSON says `"ok": true` and the output path is under `~/Downloads` unless the user requested another folder. 

If `lark-cli` reports a newer version in `_notice.update`, finish the requested export first, then mention the available update briefly.
