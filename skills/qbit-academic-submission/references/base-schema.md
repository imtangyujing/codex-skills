# Scholar投稿Base字段参考

默认Base链接：

`https://jkhbjkhb.feishu.cn/base/LDetbM4O1aHK3QsvGo0c19honic?table=tblE1p8JMtjSK6ly&view=vewGObQO7t`

默认参数：

- base token：`LDetbM4O1aHK3QsvGo0c19honic`
- table id：`tblE1p8JMtjSK6ly`
- table name：`数据表`

字段：

|字段名|字段ID|类型|用途|
|---|---|---|---|
|技术标签【新】|fldMuy2vR2|select,multiple|自由生成技术标签，后续MVP写这里|
|项目参与者|fld7hJn0cY|text|投稿人姓名，缺失写待补充|
|研究项目|fldxo3kLbW|text|短项目描述，格式偏“方法/简称：解决什么问题”|
|父记录|fldhzVMhVn|link|当前MVP不用|
|日期|fld1QBExo9|datetime|处理或投稿日期，缺省可用当天|
|技术方向|fldEus3hSq|select,multiple|旧字段，默认不要写|
|院校/机构|fldhQhCy7T|text|只按用户消息明示内容填写，消息没给写待补充|
|入选会议|fldfwaCNyV|select,multiple|明确会议/期刊才写，缺失时留空|
|附件|fldiCG3Y7N|attachment|原始稿件附件，用附件上传命令写|
|微信链接|fldidwRQEa|text|发布后的微信文章链接|

常用命令形态：

```bash
lark-cli base +record-upsert \
  --base-token LDetbM4O1aHK3QsvGo0c19honic \
  --table-id tblE1p8JMtjSK6ly \
  --json '{"项目参与者":"李文杰","院校/机构":"上海创智学院LeapQuest","研究项目":"Think with Images/Videos：解决医学多模态模型推理缺少视觉证据查证的问题","技术标签【新】":["医学AI","视觉推理","多模态Agent"],"入选会议":["ICML 2026"]}'
```

```bash
lark-cli base +record-upload-attachment \
  --base-token LDetbM4O1aHK3QsvGo0c19honic \
  --table-id tblE1p8JMtjSK6ly \
  --record-id rec_xxx \
  --field-id fldiCG3Y7N \
  --file './稿件.docx'
```

注意：附件上传的`--file`必须是当前目录内相对路径。
