#!/usr/bin/env bash
# 国内云服务器的每日运行脚本（由 /etc/cron.d/timemachine 定时调用，以 timemachine 用户运行）
#
# 流程：拉取最新代码 → 采集"归服务器采集"的数据源 → 只增不改检查 → 提交 → 推送
#       推送时顺带更新 .github/kick，触发 GitHub 重建当天账本，把服务器的数据也登记进哈希链。
set -uo pipefail

REPO_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
UNSENT="$(dirname "$REPO_DIR")/unsent"
cd "$REPO_DIR"

# 同一时间只允许一个实例运行
exec 9>/tmp/timemachine.lock
flock -n 9 || { echo "$(date '+%F %T') 已有任务在运行，跳过"; exit 0; }

TODAY=$(TZ=Asia/Shanghai date +%F)
NOW=$(TZ=Asia/Shanghai date '+%F %T')
echo "========== $NOW 开始 =========="

retry() {
  local i
  for i in 1 2 3 4 5; do
    "$@" && return 0
    echo "   失败，$((i * 20)) 秒后重试（第 $i 次）: $*"
    sleep $((i * 20))
  done
  return 1
}

# 1. 往日"已提交但没推上去"的数据：过了当天就不能再进入历史（只增不改），撤销本地提交、文件另存
if retry git fetch -q origin main; then
  if [ -n "$(git log origin/main..HEAD --oneline)" ]; then
    stale=$(git diff --name-only --diff-filter=A origin/main...HEAD -- data/raw | grep -v "$TODAY" || true)
    if [ -n "$stale" ]; then
      for f in $stale; do
        [ -f "$f" ] && mkdir -p "$UNSENT/$(dirname "$f")" && cp "$f" "$UNSENT/$f"
      done
      echo "往日未推送的数据已另存到 $UNSENT，撤销本地提交"
      git reset -q --hard origin/main
    fi
  fi
fi

# 2. 拉取最新代码（以后改代码只需推到 GitHub，服务器下次运行自动用上）
retry git pull --rebase -q origin main || echo "拉取失败，先用本地已有代码继续"

# 3. 往日未能推送的数据：按"只增不改"规则不能再补进历史，移出仓库另存，避免卡住后续提交
for f in $(git ls-files --others --exclude-standard data/raw); do
  case "$f" in
    *"$TODAY"*) ;;
    *) mkdir -p "$UNSENT/$(dirname "$f")" && mv "$f" "$UNSENT/$f" && echo "移出过期未推送文件: $f" ;;
  esac
done

# 4. 采集（额外参数原样传给 collect.py，如 --intraday-only 只跑一天多次的数据源）
python3 collect.py --runner server "$@"
rc=$?

# 5. 提交并推送当天的新数据
if [ -n "$(git status --porcelain data/raw)" ]; then
  git add data/raw
  if ! python3 scripts/check_immutable.py "$TODAY"; then
    echo "只增不改检查未通过，放弃本次提交"; git reset -q; exit 1
  fi
  printf '# 修改本文件（任意内容）并提交，即可立即触发一次采集。当天数据已齐则自动跳过。\n# last kick: %s 国内服务器推送后触发账本重建\n' "$NOW" > .github/kick
  git add .github/kick
  git commit -q -m "data(server): $TODAY"
  if retry bash -c 'git pull --rebase -q origin main && git push -q origin HEAD:main'; then
    echo "推送成功"
  else
    echo "推送失败：数据已提交在本地，下次运行（今天内）会自动重试推送"
    rc=1
  fi
else
  # 没有新数据，但可能有之前没推上去的提交
  if [ -n "$(git log origin/main..HEAD --oneline 2>/dev/null)" ]; then
    retry bash -c 'git pull --rebase -q origin main && git push -q origin HEAD:main' && echo "补推成功"
  fi
  echo "没有新数据（今天已采集，或数据源全部失败）"
fi

echo "========== $(TZ=Asia/Shanghai date '+%F %T') 结束 rc=$rc =========="
exit $rc
