---
name: qbit-reimbursement
description: 量子位报销发票二维码批量开票工作流。Use when the user sends one or more invoice QR code photos, restaurant receipt QR codes, Beijing tax invoice links, or asks to fill Qbit reimbursement invoices. The skill fills fixed company invoice fields for 北京极客伙伴科技有限公司, collects recipient delivery fields on first use, reuses them afterward, submits each invoice one by one, and saves a screenshot of every success page for checking.
---

# Qbit Reimbursement

## Purpose

Use this skill to process a batch of invoice QR codes for Qbit reimbursement.

The normal user request is: the user sends several QR code photos or invoice links and asks Codex to fill the invoice. Complete one invoice fully, submit it, capture the success page, then move to the next invoice.

## Fixed Company Fields

Always use these buyer/company fields unless the user gives a newer company profile in the same turn:

- 企业名称：北京极客伙伴科技有限公司
- 企业税号：91110108MA009FC62W
- 企业地址：北京市海淀区海淀大街甲36号8层801号
- 企业电话：010-53686780
- 开户银行：招商银行北京大运村支行
- 银行账号：110939580210601

If the page has separate fields for address and phone, fill them separately. If the page has one combined field such as 「地址电话」, fill `北京市海淀区海淀大街甲36号8层801号 010-53686780`. If the page has one combined field such as 「开户行及账号」, fill `招商银行北京大运村支行 110939580210601`.

## Recipient Profile

Recipient fields are personal delivery fields such as:

- 邮箱地址
- 手机号码
- 收件人姓名
- 收件地址

Store the reusable recipient profile outside the skill repo at:

```text
~/.codex/private/qbit-reimbursement-recipient.json
```

On first use:

1. Check whether this file exists and contains the fields required by the current invoice page.
2. If required recipient fields are missing, ask the user only for those missing fields.
3. After the user answers, save or update the JSON file.
4. Use the saved values for all later invoices unless the user says to change them.

Do not invent recipient values. Do not store QR code URLs, invoice page tokens, screenshots, or restaurant details in this profile.

Example profile:

```json
{
  "email": "name@example.com",
  "phone": "13800000000",
  "recipient_name": "",
  "recipient_address": ""
}
```

## Browser And QR Handling

When working with web pages, use the Browser plugin skill if it is available. Keep the browser visible when the user is actively checking the form; otherwise background operation is fine.

For QR code photos:

1. Decode each QR code into a URL.
2. Prefer local tools already available on the machine.
3. If no QR decoder is installed, create a temporary venv under `/tmp`, install a lightweight decoder such as OpenCV/Pillow there, and decode the image locally.
4. If a photo contains multiple QR codes, decode all candidates and use the one that opens an invoice page.

For invoice links, open the link directly.

## Per-Invoice Workflow

Process invoices sequentially. Finish the current invoice before opening the next one.

1. Open the decoded invoice URL.
2. Wait for the page to load and inspect visible fields.
3. Select 「单位」 or equivalent company/buyer type when present.
4. Expand 「全部信息」, 「更多信息」, or similar controls so all buyer fields are visible.
5. Fill fields by stable names, labels, or DOM attributes. Avoid relying only on input order.
6. Fill fixed company fields from this skill.
7. Fill recipient fields from the saved recipient profile.
8. Re-read field labels and current values before submission. If values are shifted into the wrong fields, correct them before continuing.
9. Click 「提交」, 「确认开票」, or equivalent final action when the user has asked to submit invoices in the initial request.
10. If a page asks for CAPTCHA, SMS code, account login, or payment authorization, stop and ask the user to handle or provide the required value.
11. After successful submission, capture a screenshot of the success page.
12. Save the screenshot under a run folder:

```text
~/Downloads/qbit-reimbursement-invoices/YYYYMMDD-HHMMSS/
```

Use filenames like:

```text
invoice-01-success.png
invoice-02-success.png
```

13. Record a short local checklist for the run in the same folder as `summary.md`, with one line per invoice: source image/link, company name, amount if visible, submission status, screenshot filename.
14. Continue to the next QR code.

## Validation Before Submit

Before every submission, verify the visible page has:

- 企业名称：北京极客伙伴科技有限公司
- 企业税号：91110108MA009FC62W
- 企业地址 or 地址电话 includes：北京市海淀区海淀大街甲36号8层801号
- 企业电话 or 地址电话 includes：010-53686780
- 开户银行 or 开户行及账号 includes：招商银行北京大运村支行
- 银行账号 or 开户行及账号 includes：110939580210601
- Required recipient fields are filled from the saved profile

If the page has a phone field prefilled by the merchant platform, overwrite it only when it is clearly the invoice recipient phone field and the saved recipient profile has a phone number. Leave unrelated merchant, cashier, or verification fields untouched.

## Completion Response

At the end, report:

- How many invoices were submitted.
- Screenshot folder path.
- Any invoices that were skipped or blocked, with the reason.
- Any user action still needed, such as CAPTCHA, SMS code, login, or expired QR code.

Keep the response concise. Do not paste private invoice links unless needed for debugging.
