#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CashUI 一键快速部署脚本（Ubuntu/Debian，需 root 权限执行）。

用法：
    sudo python3 deploy.py [仓库地址] [安装路径]

- 仓库地址：默认 https://github.com/你的用户名/CashUI.git
- 安装路径：默认脚本所在目录（即项目根目录，就地部署），可用第二个参数覆盖

首次运行会生成 <安装路径>/backend/.env 并退出；填好密码后再次运行即可完成剩余步骤。
"""

import os
import shutil
import subprocess
import sys

DEFAULT_REPO = "https://github.com/你的用户名/CashUI.git"


def run(cmd, cwd=None, shell=False):
    """执行命令并打印；失败时抛出异常终止脚本（等价于 bash 的 set -e）。"""
    display = cmd if isinstance(cmd, str) else " ".join(cmd)
    print(f"  $ {display}")
    subprocess.run(cmd, check=True, cwd=cwd, shell=shell)


def main():
    repo = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_REPO
    app_dir = (
        sys.argv[2] if len(sys.argv) > 2
        else os.path.dirname(os.path.abspath(__file__))
    )

    backend = os.path.join(app_dir, "backend")
    frontend = os.path.join(app_dir, "frontend")
    venv_py = os.path.join(backend, "venv", "bin", "python")
    venv_pip = os.path.join(backend, "venv", "bin", "pip")

    print(f"安装路径：{app_dir}")
    print(f"仓库地址：{repo}")

    print("==> 1/8 安装系统依赖")
    run(["apt", "update"])
    run(["apt", "install", "-y", "git", "python3", "python3-venv", "python3-pip", "nginx"])

    print("==> 2/8 拉取代码")
    if os.path.isdir(os.path.join(app_dir, ".git")):
        run(["git", "-C", app_dir, "pull"])
    else:
        run(["git", "clone", repo, app_dir])

    print("==> 3/8 配置后端虚拟环境")
    if not os.path.exists(venv_py):
        run(["python3", "-m", "venv", os.path.join(backend, "venv")])
    run([venv_pip, "install", "-r", os.path.join(backend, "requirements.txt"),
         "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"])

    print("==> 4/8 初始化 .env")
    env_file = os.path.join(backend, ".env")
    if not os.path.exists(env_file):
        run(["cp", os.path.join(backend, ".env.example"), env_file])
        print(f"!!! 已生成 {env_file}，请先编辑填入 DEFAULT_PASSWORD 和 SECRET_KEY：")
        print(f"    sudo nano {env_file}")
        print("    编辑完成后重新运行本脚本即可继续。")
        return

    print("==> 5/8 初始化数据库")
    run([venv_py, "-m", "app.init_db"], cwd=backend)

    print("==> 6/8 配置后端常驻（systemd）")
    service_content = (
        "[Unit]\n"
        "Description=CashUI backend\n"
        "After=network.target\n"
        "\n"
        "[Service]\n"
        f"WorkingDirectory={backend}\n"
        f"ExecStart={venv_py} -m uvicorn app.main:app --host 127.0.0.1 --port 8000\n"
        "Restart=always\n"
        "RestartSec=3\n"
        "\n"
        "[Install]\n"
        "WantedBy=multi-user.target\n"
    )
    service_path = "/etc/systemd/system/cashui.service"
    with open(service_path, "w", encoding="utf-8") as f:
        f.write(service_content)
    run(["systemctl", "daemon-reload"])
    run(["systemctl", "enable", "--now", "cashui"])

    print("==> 7/8 构建前端")
    if shutil.which("node") is None:
        run("curl -fsSL https://deb.nodesource.com/setup_20.x | bash -", shell=True)
        run(["apt", "install", "-y", "nodejs"])
    run(["npm", "install", "--registry=https://registry.npmmirror.com"], cwd=frontend)
    run(["npm", "run", "build"], cwd=frontend)

    print("==> 8/8 部署前端到 Nginx")
    run(["mkdir", "-p", "/var/www/cashui"])
    run(["rm", "-rf", "/var/www/cashui/dist"])
    run(["cp", "-r", os.path.join(frontend, "dist"), "/var/www/cashui/"])
    run(["cp", os.path.join(app_dir, "deploy", "nginx.conf"),
         "/etc/nginx/sites-available/cashui"])
    run(["ln", "-sf", "/etc/nginx/sites-available/cashui",
         "/etc/nginx/sites-enabled/cashui"])
    run(["rm", "-f", "/etc/nginx/sites-enabled/default"])
    run(["nginx", "-t"])
    run(["systemctl", "reload", "nginx"])

    print()
    print("部署完成！请在腾讯云安全组放行 80 端口后，用手机/浏览器访问：")
    print("  http://服务器公网IP/")


if __name__ == "__main__":
    main()
