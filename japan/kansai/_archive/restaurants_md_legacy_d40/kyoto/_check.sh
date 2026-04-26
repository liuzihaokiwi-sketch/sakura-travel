#!/usr/bin/env bash
# 京都餐厅 md 自检脚本·防止数字/假名/Full 数对账漂移
# 用法：cd 到本目录 bash _check.sh
# 每次改完 md 必跑·不过不准交付
set -u
cd "$(dirname "$0")"
FAIL=0

echo "=== [1] showcase 表行计数（权威源：标准表 grep）==="
declare -A sc
total=0
for f in 东山轴.md 河原町-先斗町.md 烏丸御池.md 京都站.md 岚山.md 伏见.md 北区.md; do
  n=$(grep -cE '^\| [0-9]+ \| .* \| showcase \|' "$f")
  sc[$f]=$n
  total=$((total+n))
  printf "  %-24s %d\n" "$f" "$n"
done
echo "  TOTAL: $total"

echo ""
echo "=== [2] showcase 声明数字对账（所有 md 应写同一个 total）==="
# 检查 index.md / 当前状态.md / 北区.md 里是否都是 total
for path_and_pattern in \
  "./index.md" \
  "./北区.md" \
  "../../../当前状态.md"; do
  p="$path_and_pattern"
  if [ -f "$p" ]; then
    hits=$(grep -oE '累计 [0-9]+ 家|累计 showcase [^·]*[0-9]+ 家|showcase \*\*[0-9]+ 家|累计 \*\*[0-9]+ 家|池累计 showcase \*\*[0-9]+ 家' "$p" || true)
    nums=$(echo "$hits" | grep -oE '[0-9]+' | sort -u)
    if [ -n "$nums" ]; then
      for n in $nums; do
        if [ "$n" != "$total" ]; then
          echo "  ❌ $p 写了 $n 家·应为 $total 家"
          FAIL=1
        else
          echo "  ✅ $p 声明 $n 家·一致"
        fi
      done
    fi
  fi
done

echo ""
echo "=== [3] Full 数对账（<!-- depth: full --> 与顶部 Full 目标）==="
for f in 东山轴.md 河原町-先斗町.md 烏丸御池.md 京都站.md 岚山.md 伏见.md 北区.md; do
  actual=$(grep -c '<!-- depth: full -->' "$f")
  claimed=$(grep -oE '\*\*Full 目标\*\*：[0-9]+ 家|Full 目标 [0-9]+ 家' "$f" | head -1 | grep -oE '[0-9]+' || echo "?")
  if [ "$claimed" = "?" ]; then
    printf "  %-24s full=%d  claimed=未声明\n" "$f" "$actual"
  elif [ "$actual" = "$claimed" ]; then
    printf "  ✅ %-22s full=%d  claimed=%s\n" "$f" "$actual" "$claimed"
  else
    printf "  ❌ %-22s full=%d  claimed=%s  不一致\n" "$f" "$actual" "$claimed"
    FAIL=1
  fi
done

echo ""
echo "=== [4] 假名残留黑名单扫（应在中文或首次括号格式）==="
# 禁裸写词·白名单通过「（词）」格式豁免·即词前有中文+左括号
BLACKLIST='コース|タクシー|ビル|ランチ|ディナー|きき酒|きんぴら|ホットケーキ|旅館'
# 白名单豁免：词前字符是 （ ( 「 —— 即已在括号/引号内作为原文标注·用 python 精确判更稳
violations=$(python3 -c "
import re,sys
pat=re.compile(r'($BLACKLIST)')
files='东山轴.md 河原町-先斗町.md 烏丸御池.md 京都站.md 岚山.md 伏见.md 北区.md'.split()
for fn in files:
    for i,line in enumerate(open(fn,encoding='utf-8'),1):
        for m in pat.finditer(line):
            s=m.start()
            # 向前找最近的 '（' '(' '「'·如果在命中词之前且未被闭合·算豁免
            pre=line[:s]
            open_paren=max(pre.rfind('（'),pre.rfind('('),pre.rfind('「'))
            close_paren=max(pre.rfind('）'),pre.rfind(')'),pre.rfind('」'))
            if open_paren>close_paren and open_paren!=-1:
                continue
            print(f'{fn}:{i}:{line.rstrip()}')
            break
" 2>/dev/null || true)
if [ -z "$violations" ]; then
  echo "  ✅ 无裸假名残留"
else
  echo "$violations" | head -20
  echo "  ❌ 发现裸假名·请加「中文（日文）」格式或改中文"
  FAIL=1
fi

echo ""
if [ $FAIL -eq 0 ]; then
  echo "=== ✅ 全部通过 ==="
else
  echo "=== ❌ 有不一致·修掉再交付 ==="
  exit 1
fi
