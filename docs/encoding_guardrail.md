# 编码防错记录（2026-03-26）

## 这次乱码的主要原因

1. 在 Windows/PowerShell 下对整文件做了重写（而不是小范围补丁），触发了编码和换行被重新序列化。  
2. 含中文内容的文件在“读写链路”中经过了终端代码页/工具默认编码，出现了字符误解码（mojibake）。  
3. 一次小需求被放大成“整文件文本变化”，导致本来只改几行，diff 却出现大面积中文异常。

## 以后必须遵守的规则

1. 只做最小补丁，不做整文件覆盖。  
2. 修改含中文 Python 常量时，优先使用 `\uXXXX` 形式，降低终端/代码页影响。  
3. 禁止用“管道 + 重写整文件”方式做恢复（例如直接 `git show ... | Set-Content ...`）。  
4. 每次改完含中文文件，必须先跑“编码检查三步”再结束任务。

## 编码检查三步（执行版）

1. 语法检查  
```powershell
python -m py_compile app/api/submissions.py app/workers/__main__.py
```

2. 只看目标文件 diff，确认没有异常大改  
```powershell
git diff -- app/api/submissions.py app/workers/__main__.py
```

3. 检查是否意外写入 BOM  
```powershell
@'
from pathlib import Path
for p in [Path("app/api/submissions.py"), Path("app/workers/__main__.py")]:
    b = p.read_bytes()
    print(p, "BOM" if b.startswith(b"\xef\xbb\xbf") else "NO_BOM")
'@ | python -
```

## 触发回滚的红线

出现下面任一条，立即停止并回到修改前状态（只回滚本次改动范围）：

1. 目标是小修，但 diff 出现大段中文/注释整体变化。  
2. 文件首行出现不可预期字符（例如 `﻿`）。  
3. 编译通过但中文注释/字符串明显乱码。  

