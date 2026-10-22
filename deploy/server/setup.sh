#!/usr/bin/env bash
# 国内云服务器一键安装（Ubuntu 22.04/24.04，以 root 运行一次即可，重复运行安全）
#
#   curl -fsSL https://raw.githubusercontent.com/wenxizhang0919/cn-data-timemachine/main/deploy/server/setup.sh | bash
#
# 做的事情：
#   1. 安装 git、python3、requests，开启系统安全更新自动安装，时区设为北京时间
#   2. 创建专用的低权限用户 timemachine（不用 root 跑采集）
#   3. 生成一把只用于本仓库的 SSH 部署密钥（私钥只存在这台服务器上）
#   4. 克隆仓库到 /opt/timemachine/repo
#   5. 设定时任务：每天北京时间 10:47 / 14:07 / 17:37 / 20:47 运行 run.sh（先成功者采集，其余自动跳过）
#   6. 打印部署公钥：把它加到 GitHub 仓库 Settings → Deploy keys（勾选 Allow write access）
set -euo pipefail

REPO="wenxizhang0919/cn-data-timemachine"
APP_USER="timemachine"
APP_HOME="/opt/timemachine"
REPO_DIR="$APP_HOME/repo"
LOG="/var/log/timemachine.log"

if [ "$(id -u)" -ne 0 ]; then
  echo "请用 root 运行（或在命令前加 sudo）"; exit 1
fi

echo "==> 1/6 安装依赖"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y -q
apt-get install -y -q git python3 python3-requests unattended-upgrades ca-certificates openssh-client
timedatectl set-timezone Asia/Shanghai || true
dpkg-reconfigure -f noninteractive unattended-upgrades || true

echo "==> 2/6 创建专用用户 $APP_USER"
if ! id -u "$APP_USER" >/dev/null 2>&1; then
  useradd --system --create-home --home-dir "$APP_HOME" --shell /bin/bash "$APP_USER"
fi
mkdir -p "$APP_HOME/.ssh" "$APP_HOME/unsent"
chmod 700 "$APP_HOME/.ssh"

echo "==> 3/6 生成部署密钥（只用于本仓库）"
if [ ! -f "$APP_HOME/.ssh/id_ed25519" ]; then
  ssh-keygen -q -t ed25519 -N "" -f "$APP_HOME/.ssh/id_ed25519" -C "timemachine-server@$(hostname)"
fi
# 国内访问 github.com:22 不稳定，走 443 端口（ssh.github.com）更可靠
cat > "$APP_HOME/.ssh/config" <<EOF
Host github.com
  HostName ssh.github.com
  Port 443
  User git
  IdentityFile $APP_HOME/.ssh/id_ed25519
  IdentitiesOnly yes
  StrictHostKeyChecking accept-new
  ServerAliveInterval 30
EOF
chmod 600 "$APP_HOME/.ssh/config"
chown -R "$APP_USER:$APP_USER" "$APP_HOME"

echo "==> 4/6 克隆仓库（国内访问 GitHub 可能较慢，失败会自动重试）"
if [ ! -d "$REPO_DIR/.git" ]; then
  ok=0
  for i in 1 2 3 4 5; do
    if sudo -u "$APP_USER" git clone -q "https://github.com/$REPO.git" "$REPO_DIR"; then ok=1; break; fi
    echo "   第 $i 次克隆失败，$((i * 15)) 秒后重试..."; rm -rf "$REPO_DIR"; sleep $((i * 15))
  done
  [ "$ok" = 1 ] || { echo "克隆失败：请稍后重新运行本脚本"; exit 1; }
fi
cd "$REPO_DIR"
sudo -u "$APP_USER" git remote set-url --push origin "git@github.com:$REPO.git"
sudo -u "$APP_USER" git config user.name "timemachine-server"
sudo -u "$APP_USER" git config user.email "timemachine-server@users.noreply.github.com"
chmod +x deploy/server/run.sh

echo "==> 5/6 设置定时任务"
cat > /etc/cron.d/timemachine <<EOF
# 每日数据时光机：国内数据源采集（北京时间）。先成功者采集，其余自动跳过。
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
47 10 * * * $APP_USER $REPO_DIR/deploy/server/run.sh >> $LOG 2>&1
7 14 * * *  $APP_USER $REPO_DIR/deploy/server/run.sh >> $LOG 2>&1
37 17 * * * $APP_USER $REPO_DIR/deploy/server/run.sh >> $LOG 2>&1
47 20 * * * $APP_USER $REPO_DIR/deploy/server/run.sh >> $LOG 2>&1
EOF
chmod 644 /etc/cron.d/timemachine
touch "$LOG" && chown "$APP_USER:$APP_USER" "$LOG"
cat > /etc/logrotate.d/timemachine <<EOF
$LOG {
  weekly
  rotate 8
  compress
  missingok
  notifempty
  copytruncate
}
EOF

echo "==> 6/6 完成"
echo
echo "================ 请把下面这一整行加到 GitHub 仓库的 Deploy keys ================"
echo "  地址：https://github.com/$REPO/settings/keys/new"
echo "  标题：aliyun-server    勾选：Allow write access"
echo
cat "$APP_HOME/.ssh/id_ed25519.pub"
echo
echo "==================================================================================="
echo "加好后运行这条命令测试一次（会立即采集并推送）："
echo "  sudo -u $APP_USER $REPO_DIR/deploy/server/run.sh"
