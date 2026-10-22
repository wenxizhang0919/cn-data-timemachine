# 国内云服务器部署

有些数据源拒绝海外机房访问（例如 Steam 对 GitHub Actions 返回 502，部分政府网站只允许境内 IP），这些数据源在 `sources/` 里标注 `RUNNER = "server"`，由国内云服务器采集。

## 分工

| 机器 | 采集 | 其他 |
|---|---|---|
| GitHub Actions（海外） | `RUNNER` 未标注或为 `github` 的数据源 | 生成每日账本、时间戳、版本标签 |
| 国内云服务器 | `RUNNER = "server"` 的数据源 | 推送后触发 GitHub 重建当天账本 |

两台机器各写各的状态文件（`data/raw/_status/<日期>.json` 与 `<日期>.server.json`），账本合并两者。

## 安装（一次）

以 root 在服务器上运行：

```bash
curl -fsSL https://raw.githubusercontent.com/wenxizhang0919/cn-data-timemachine/main/deploy/server/setup.sh | bash
```

脚本最后会打印一行部署公钥，把它加到仓库 **Settings → Deploy keys**（勾选 *Allow write access*）。部署密钥只能写这一个仓库。

然后测试一次：

```bash
sudo -u timemachine /opt/timemachine/repo/deploy/server/run.sh
```

## 日常

- 定时任务写在 [`crontab`](crontab)：一天一次的数据源在 10:47 / 14:07 / 17:37 / 20:47 先成功者采集；每小时的数据源 0:27–22:27 每小时一次；21:47 兜底补采（含 GitHub 当天没采到的数据源）。每次运行最多 50 分钟。
- 每次运行前自动 `git pull`，并把 `crontab` 同步到服务器，所以改代码、改定时都只需推到 GitHub，不用登录服务器。
- 没有密码也能运维：阿里云控制台 → 云服务器 ECS → 云助手 → 对实例执行命令（以 root 运行）。
- 日志：`/var/log/timemachine.log`
- 推送失败时数据留在本地，当天内下次运行自动补推；跨天仍未推送的文件按"只增不改"规则不进入历史，移到 `/opt/timemachine/unsent/` 另存。
