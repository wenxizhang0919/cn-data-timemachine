#!/usr/bin/env bash
# 服务器运维小工具（以 root 运行，例如在阿里云「云助手」里执行）。先拉最新代码，再做指定的事。
#
#   bash /opt/timemachine/repo/deploy/server/ops.sh status          内存、交换空间、磁盘、定时任务、最近日志
#   bash /opt/timemachine/repo/deploy/server/ops.sh apply           重新运行一键安装（幂等，用于更新系统级设置）
#   bash /opt/timemachine/repo/deploy/server/ops.sh try <数据源> [N] 试跑一个数据源，只打印不写文件（N=只抓前 N 个）
#   bash /opt/timemachine/repo/deploy/server/ops.sh run [参数]       立即执行一次正式采集（参数同 run.sh，如 --intraday-only）
set -uo pipefail
REPO_DIR=/opt/timemachine/repo
APP_USER=timemachine
cd "$REPO_DIR" || exit 1
sudo -u "$APP_USER" timeout 120 git pull -q --rebase origin main || echo "（拉取代码失败，使用本地已有版本）"

case "${1:-status}" in
  status)
    echo "== 内存 =="; free -m
    echo "== 交换空间 =="; swapon --show
    echo "== 磁盘 =="; df -h / | tail -1
    echo "== 定时任务 =="; crontab -u "$APP_USER" -l | grep -v '^#'
    echo "== 最近日志 =="; tail -30 /var/log/timemachine.log
    ;;
  apply)
    bash deploy/server/setup.sh > /tmp/setup.log 2>&1; echo "setup 退出码 $?（详细日志 /tmp/setup.log）"
    free -m; swapon --show
    ;;
  try)
    shift
    sudo -u "$APP_USER" python3 scripts/dry_run.py "$1" ${2:+--limit "$2"}
    ;;
  run)
    shift
    sudo -u "$APP_USER" timeout 50m deploy/server/run.sh "$@" 2>&1 | tee -a /var/log/timemachine.log | tail -20
    ;;
  *)
    echo "未知操作：$1"; exit 1 ;;
esac
