# Feishu Markdown Import

Use this subskill for local Qbit Markdown drafts → Feishu/Lark docx documents.

## Goal

Create a Feishu docx document that keeps the Markdown draft wording and order, preserves Qbit article spacing, and renders images/videos as real Feishu media blocks instead of plain links or Obsidian embed text.

## Required Inputs

- Local Markdown file path.
- Optional target Feishu folder token. If omitted, create in the current user's root Drive.
- Optional output title. If omitted, derive it from the first clear draft title.

## Spacing Rules

- Treat one or more blank Markdown lines as one visual blank paragraph in Feishu.
- Use `<p></p>` for inserted blank paragraphs. Avoid `<p><br/></p>` because it renders too tall.
- Keep reference-link sections compact when they are a Qbit source list:
  - `参考链接：`
  - `[1]...`
  - `[2]...`
  - through `[8]...`
- Do not insert blank paragraphs between the reference heading and numbered reference lines.
- Do not insert a blank paragraph immediately after `[8]` when the draft continues with social copy or backup text.

## Media Rules

Handle both standard Markdown media and Obsidian embeds:

- Markdown image URL: `![alt](https://...)`
  - Prefer writing `<img href="https://..." caption="alt"/>` in the initial doc content.
- Obsidian local image: `![[file.png]]`, `![[file.jpeg]]`, `![[file.jpg]]`
  - Resolve the file under the Obsidian workspace.
  - Insert it as a real Feishu image with `lark-cli docs +media-insert --type image`.
- Obsidian local video: `![[file.mov]]`, `![[file.mp4]]`, `![[file.m4v]]`
  - Resolve the file under the Obsidian workspace.
  - Insert it as a real Feishu file preview block with `lark-cli docs +media-insert --type file --file-view preview`.
- Plain source links in a references section stay clickable text links. Do not convert YouTube/source URLs to media unless the user asks.

## Recommended Procedure

1. Read the Markdown file and build an XML body:
   - Use `<title>...</title>` once.
   - Convert headings to `h1` through `h6`.
   - Convert non-empty text lines to `<p>...</p>`.
   - Convert one or more blank-line runs to one `<p></p>`, except inside the compact reference-link section.
   - Convert remote Markdown images to `<img href="..."/>`.
   - Replace local Obsidian media embeds with unique placeholder paragraphs.
2. Create the Feishu doc:

   ```bash
   lark-cli docs +create --api-version v2 --content @relative/path/to/content.xml --format json
   ```

   `@file` must be a relative path inside the current working directory.

3. Insert local media at placeholders:
   - Use relative file paths inside the command working directory.
   - For images:

     ```bash
     lark-cli docs +media-insert --doc "<doc_id>" --file "<relative-image>" --selection-with-ellipsis "<placeholder>" --before --type image --align center --width 800
     ```

   - For videos:

     ```bash
     lark-cli docs +media-insert --doc "<doc_id>" --file "<relative-video>" --selection-with-ellipsis "<placeholder>" --before --type file --file-view preview
     ```

4. Fetch with IDs and delete placeholder text blocks:

   ```bash
   lark-cli docs +fetch --api-version v2 --doc "<doc_id>" --detail with-ids --format json
   lark-cli docs +update --api-version v2 --doc "<doc_id>" --command block_delete --block-id "<comma-separated-placeholder-block-ids>"
   ```

5. Fetch again and verify:
   - No placeholder text remains.
   - Media count matches the draft media count.
   - Blank paragraph runs have max length `1`.
   - Blank paragraphs are serialized as `<p id="..."></p>`, not `<p id="..."><br/></p>`.
   - The reference-link section has no blank paragraph between `参考链接：`, `[1]` through `[8]`, and the next continuation line.

## Implementation Notes

- Use `lark-doc`, `lark-drive`, and `lark-shared` skills as required by their own instructions before running Feishu commands.
- Prefer block-level operations for cleanup. Avoid `overwrite` after media is inserted because it can destroy media blocks.
- Keep temporary import files hidden or clearly temporary, then remove them after validation.
- If `lark-cli` reports a newer version in `_notice.update`, finish the user task first, then mention the update briefly.
