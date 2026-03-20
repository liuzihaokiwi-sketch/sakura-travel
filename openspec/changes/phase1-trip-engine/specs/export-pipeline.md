# Spec: export-pipeline

## 概述

导出管线负责将渲染完成的 HTML/PDF 存储为可交付文件，并生成下载/分享链接。

---

## 管线流程

```
render_export(plan_id)
  ↓
1. 渲染 HTML（magazine-renderer）
2. WeasyPrint → PDF bytes
3. 保存 PDF → /exports/{plan_id}/itinerary.pdf
4. 保存 HTML → /exports/{plan_id}/preview.html
5. 写入 export_assets 记录
6. 更新 itinerary_plans.status = "ready"
7. 更新 trip_requests.status = "completed"
```

---

## 数据写入规格

### export_jobs
```
job_id          UUID PK
plan_id         UUID FK
status          VARCHAR(16)  -- pending/running/done/failed
format          VARCHAR(16)  -- pdf/html
started_at      TIMESTAMPTZ
completed_at    TIMESTAMPTZ
error_msg       TEXT
```

### export_assets
```
asset_id        UUID PK
job_id          UUID FK
plan_id         UUID FK
format          VARCHAR(16)  -- pdf/html
file_path       TEXT         -- 本地路径或对象存储 Key
public_url      TEXT         -- 对外分享 URL
file_size_bytes INTEGER
expires_at      TIMESTAMPTZ  -- 默认 30 天
created_at      TIMESTAMPTZ
```

---

## 初期存储方案

- **本地存储**：`/exports/{plan_id}/` 目录
- **Nginx 静态服务**：`/exports/` 挂载为静态目录，`public_url = https://domain/exports/{plan_id}/preview.html`
- **Phase 2 升级**：迁移至对象存储（S3/OSS），修改 `file_path` 和 `public_url` 即可

---

## 验收标准

- [ ] `render_export(plan_id)` job 实现并注册到 arq
- [ ] PDF 文件正确生成，大小合理（< 10MB）
- [ ] H5 预览链接可访问
- [ ] export_assets 记录写入正确
- [ ] trip_requests.status 更新为 "completed"
