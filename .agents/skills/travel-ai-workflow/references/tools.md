# Tool Commands

Prefer commands from the specialized skill. Use this file only as a fallback.

## Search

```powershell
rg -n "pattern" .
rg --files
```

## Validation

Templates / plans:

```powershell
.\.venv\Scripts\python.exe scripts\validate_template.py japan\kansai\templates
.\.venv\Scripts\python.exe -m pytest app\tests\test_plan_contract.py -q
```

Data pools:

```powershell
.\.venv\Scripts\python.exe scripts\validate_entity.py
.\.venv\Scripts\python.exe scripts\validate_restaurants.py
.\.venv\Scripts\python.exe scripts\validate_hotels.py
```

Frontend:

```powershell
cd web
npm run build
```

## Specialized Tools

- Xiaohongshu / opencli: use `travel-ai-research` or `travel-ai-marketing`.
- Image generation and cutouts: use `handbook-image-assets`.
- Review boards and visual production: use `handbook-visual-production`.
