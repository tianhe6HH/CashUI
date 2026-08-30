# CashUI 备用金管理系统

面向部门的备用金记账与投票系统。手机浏览器直接访问，用于记录备用金的收入（缴款）、支出（垫付），并对费用支出、资金结转进行民主投票表决。

- 后端：Python + FastAPI + SQLite
- 前端：Vue 3 + Vite + Vant（移动端优先）
- 部署：腾讯云 CVM + Nginx，HTTP 访问

---

## 1. 程序功能

### 1.1 角色权限（三级）

| 功能 | 管理员 | 高级账号 | 普通账号 |
|---|:---:|:---:|:---:|
| 查看余额/各科目结余 | ✅ | ✅ | ✅ |
| 记账（收入/支出） | ✅ | ❌ | ❌ |
| 删除收支记录 | ✅ | ❌ | ❌ |
| 查看收入明细 | ✅ | ✅ | ❌ |
| 科目管理（增删改） | ✅ | ❌ | ❌ |
| 科目结转 | ✅ | ❌ | ❌ |
| 缴款人管理 | ✅ | ✅ | ❌ |
| 新增活动 | ✅ | ✅ | ❌ |
| 发起/参与投票 | ✅ | ✅ | ✅ |
| 下载报表 | ✅ | ✅ | ❌ |
| 账号管理 | ✅ | ❌ | ❌ |

### 1.2 专款专用记账

- 科目：综合使用 / 民主生活会 / 团建 / 年末聚餐（管理员可增删改）
- 收入（缴款）与支出（垫付），每笔关联科目
- 各科目独立核算结余，互不挪用
- 支出余额不足时拦截（类似微信支付提示）
- 科目结转：管理员可将某科目部分金额转至另一科目（结转属于内部调拨，不计入总收入/总支出，但仍影响各科目结余）
- 删除错误记账（仅管理员）：单条删除 + 按时间段批量删除，删除后各科目结余 / 总收入 / 总支出自动重算
- 按时间段筛选查看收支明细

### 1.3 投票工具

- 所有人可发起；参与人筛选（高级账号自动参与、普通账号可选）
- 选项自定义 + 备注，发起前可增删改
- 日历方式选择起止时间（精确到分钟）
- 结果分层可见：普通账号投票期间只看自己选择、结束后看结果；高级/管理员/发起人实时看结果

### 1.4 报表 & 活动

- 月度财务报表（Excel，每月自动生成）：收支汇总 + 收入明细 + 支出明细
- 活动管理：民主生活会 / 团建 / 年末聚餐；办团建的当月自动校验不开例会

### 1.5 账号安全

- 默认密码 `123456` + 首次登录强制改密
- 密码 bcrypt 哈希，JWT 认证
- 登录失败限流：普通/高级账号 3 次锁 1 分钟 → 5 次锁 3 分钟 → 10 次禁止登录并提示联系管理员重置；管理员账号不锁定
- 批量导入 / 批量改权限 / 批量重置密码 / 批量删除 / 导出账号密码（CSV）

---

## 2. 配置 .env（设置默认密码与密钥）

### 2.1 `.env` 是什么

`.env` 是环境变量配置文件，存放**密码、密钥等敏感信息**，已加入 `.gitignore`，**不会提交到代码仓库**。每个部署环境（本地/服务器）都需要单独创建一份。

### 2.2 设置默认密码

程序的默认密码为 `123456`，可通过 `.env` 的 `DEFAULT_PASSWORD` 覆盖。这个密码会用于：

- 首次初始化时创建的管理员账号初始密码
- 管理员「新建账号」时账号的初始密码
- 管理员「重置密码」时重置成的密码

**设置方法（可选）：**

```bash
cd backend
cp .env.example .env     # 复制模板为 .env
```

然后编辑 `backend/.env` 文件，填入你的配置：

```ini
# 所有账号的默认密码（新建/重置时使用），默认 123456
DEFAULT_PASSWORD=123456

# JWT 密钥，改成一段随机长字符串
SECRET_KEY=请改成随机长字符串

# 登录令牌有效期（分钟），默认 1440 = 24 小时
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

> **提示**：若不创建 `.env`，程序默认使用 `123456` 作为所有账号的初始密码。

### 2.3 默认密码说明

默认密码统一为 `123456`。生产环境建议通过 `.env` 的 `DEFAULT_PASSWORD` 改成自己的密码，且每个部署环境尽量用不同的密码。

### 2.4 生成随机 SECRET_KEY

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

把输出填到 `.env` 的 `SECRET_KEY`。

---

## 3. 如何使用并重置数据库

### 3.1 初始化数据库（首次）

```bash
cd backend
# Windows 本地
python -m venv venv
venv\Scripts\python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
venv\Scripts\python -m app.init_db

# Linux 服务器
python3 -m venv venv
venv/bin/pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
venv/bin/python -m app.init_db
```

初始化后会生成：
- `backend/cashui.db` — 数据库文件
- 默认管理员账号 `admin`（密码为默认密码 `123456`，或 `.env` 中配置的 `DEFAULT_PASSWORD`，首次登录需改密）
- 4 个固定科目：综合使用 / 民主生活会 / 团建 / 年末聚餐

### 3.2 重置数据库（清空所有数据）

> 重置会删除**所有数据**（账号、流水、投票、报表），操作前请先备份。

```bash
cd backend
# 1. 停止后端服务（systemd 部署时：sudo systemctl stop cashui）
# 2. 删除数据库文件和报表
rm -f cashui.db cashui.db-wal cashui.db-shm
rm -rf reports/
# 3. 重新初始化
venv/bin/python -m app.init_db
# 4. 重新启动后端（sudo systemctl start cashui）
```

### 3.3 账号密码管理（manage_accounts.py）

> 该脚本用于在服务器上单独或批量配置账号与密码，配合「账号管理 → 导出账号」使用。

```bash
cd backend

# 单独设置/创建某个账号（角色可选：admin / advanced / normal，默认 normal）
venv/bin/python manage_accounts.py set 用户名 密码 [角色]

# 批量导入（CSV 表头：username,password,role；密码留空则不改已有账号密码）
venv/bin/python manage_accounts.py import accounts.csv
```

典型流程：在「账号管理」页点「导出账号」得到 `accounts.csv`，修改其中的密码列（留空=不改，填明文=设为该密码），再上传服务器用 `import` 写回。

### 3.4 备份数据库

```bash
# 定期备份数据库和报表目录即可（SQLite 单文件）
cp backend/cashui.db backup/cashui-$(date +%Y%m%d).db
```

---

## 4. Git 提交（commit）内容要求

提交信息格式：`类型: 简述`

### 类型（type）

| 类型 | 含义 |
|---|---|
| feat | 新增功能 |
| fix | 修复 Bug |
| docs | 文档改动 |
| refactor | 重构（不改变功能） |
| style | 格式调整（空格、缩进等） |
| chore | 杂项、依赖、配置 |

### 示例

```
feat: 新增科目结转功能
fix: 修复投票时间选择器卡死的问题
docs: 更新 README 部署说明
refactor: 重构投票结果可见性逻辑
```

### 要求

1. 用中文描述，简洁明了（一句话说清改了什么）
2. 一次提交只做一件事，避免大杂烩提交
3. 提交前先 `git status` 确认改动范围
4. 提交前先 `git diff` 检查改动内容
5. 不要提交 `venv/`、`node_modules/`、`cashui.db`、`.env`、`manage_accounts.py` 等（已写入 `.gitignore`）

---

## 5. 如何配置代理（访问 GitHub）

> 国内访问 GitHub 常被重置连接，需要通过 v2ray 等客户端的本地端口走代理。

### 5.1 查看当前代理

```bash
git config --local --get http.proxy
git config --local --get https.proxy
```

### 5.2 配置项目级代理（只对当前仓库生效）

```bash
# SOCKS 代理（v2ray 默认 SOCKS 端口 10808）
git config --local http.proxy socks5://127.0.0.1:10808
git config --local https.proxy socks5://127.0.0.1:10808

# HTTP 代理（Clash 默认 7890 等，端口按实际改）
git config --local http.proxy http://127.0.0.1:7890
git config --local https.proxy http://127.0.0.1:7890
```

### 5.3 配置全局代理（所有仓库生效）

```bash
git config --global http.proxy socks5://127.0.0.1:10808
git config --global https.proxy socks5://127.0.0.1:10808
```

### 5.4 取消代理

```bash
git config --local --unset http.proxy
git config --local --unset https.proxy
# 全局取消：
git config --global --unset http.proxy
git config --global --unset https.proxy
```

### 5.5 注意事项

- `socks5://` 对应 SOCKS 端口；`http://` 对应 HTTP 端口，两者端口号不同，别混用。
- 代理地址是 `127.0.0.1:本地端口`（客户端监听的端口），**不是**服务器节点地址。
- 代理要生效，前提是 v2ray/Clash 客户端在运行。
- 验证是否连通：`git ls-remote origin` 能返回远程分支即成功。

---

## 6. 快速部署（新服务器/上位机）

> 以下以 Ubuntu 服务器为例。前提：已有一台有公网 IP 的服务器，且**安全组放行 80 端口**（HTTP）。

### 6.0 一键快速部署（推荐）

项目根目录提供了 `deploy.py` 一键部署脚本，可在全新 Ubuntu/Debian 服务器上自动完成「装依赖 → 拉代码 → 后端 → systemd → 前端 → Nginx」全流程。脚本默认**就地部署**（以脚本所在目录为安装路径），因此你可以把代码放到 `/home` 下的任意路径。

```bash
# 1. 全新服务器先拉取代码到你想放的位置（例如 /home/cashui，路径可自行指定）
sudo apt update && sudo apt install -y git
sudo git clone https://ghproxy.net/https://github.com/tianhe6HH/CashUI.git /home/cashui

# 2. 进入该目录执行部署脚本
cd /home/cashui
sudo python3 deploy.py
```

> 脚本首次运行会生成 `backend/.env` 并退出；先用 `sudo nano /home/cashui/backend/.env` 填好 `DEFAULT_PASSWORD` 与 `SECRET_KEY`，再重新执行 `sudo python3 deploy.py` 即可完成剩余步骤。
> 若服务器已有旧版本，脚本会自动 `git pull` 更新后再部署。

---

以下为**分步骤手动部署**，便于理解每个环节或排查问题：

### 6.1 拉取代码

```bash
# 先装 git（一般已自带）
sudo apt update && sudo apt install -y git

# 拉取仓库到 /home/cashui
sudo mkdir -p /home
cd /home
sudo git clone https://github.com/你的用户名/CashUI.git cashui
# 或使用 Gitee：sudo git clone https://gitee.com/你的用户名/CashUI.git cashui
```

### 6.2 配置 .env（设置默认密码和密钥）

```bash
cd /home/cashui/backend
sudo cp .env.example .env
sudo nano .env     # 编辑，至少改 DEFAULT_PASSWORD 和 SECRET_KEY
```

填入（示例）：

```ini
SECRET_KEY=一段随机长字符串
ACCESS_TOKEN_EXPIRE_MINUTES=1440
DEFAULT_PASSWORD=123456
```

### 6.3 部署后端

```bash
cd /home/cashui/backend
python3 -m venv venv
venv/bin/pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
venv/bin/python -m app.init_db
```

### 6.4 后端常驻（systemd）

```bash
sudo tee /etc/systemd/system/cashui.service > /dev/null <<'EOF'
[Unit]
Description=CashUI backend
After=network.target

[Service]
WorkingDirectory=/home/cashui/backend
ExecStart=/home/cashui/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable cashui
sudo systemctl start cashui
sudo systemctl status cashui   # 看到 active (running) 即成功
```

### 6.5 构建并部署前端

**方式一：本地构建后上传**（服务器不用装 Node）

```bash
# 本地（Windows PowerShell）：
# cd frontend && npm run build && scp -r dist 用户@服务器IP:~/CashUI/frontend/
```

**方式二：服务器直接构建**（需装 Node）

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
cd /home/cashui/frontend
npm install --registry=https://registry.npmmirror.com
npm run build
```

然后把 `dist` 放到 nginx 目录：

```bash
sudo mkdir -p /var/www/cashui
sudo rm -rf /var/www/cashui/dist
sudo cp -r /home/cashui/frontend/dist /var/www/cashui/
```

### 6.6 配置 Nginx

```bash
sudo apt install -y nginx
sudo cp /home/cashui/deploy/nginx.conf /etc/nginx/sites-available/cashui
sudo ln -sf /etc/nginx/sites-available/cashui /etc/nginx/sites-enabled/cashui
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

### 6.7 验证

```bash
curl http://127.0.0.1:8000/api/accounts   # 后端 → 返回 JSON（或 401 提示未登录）
curl http://127.0.0.1/                     # 前端 → 返回 HTML（不再 301）
```

### 6.8 手机访问

在**手机浏览器**地址栏输入：

```
http://你的公网IP/
```

例如公网 IP 是 `159.75.69.198`，就输入 `http://159.75.69.198/`。

**能打开的前提**：

1. 后端已启动（`systemctl status cashui` 为 active）
2. Nginx 已配置并运行（`systemctl status nginx` 为 active）
3. 前端 dist 已放到 `/var/www/cashui/dist`
4. **腾讯云安全组放行了 80 端口**（入站规则：TCP 80，来源 `0.0.0.0/0`）

> 手机用任意 WiFi 或流量都能访问（只要手机能上网），不需要和服务器在同一网络。建议在手机把网址「添加到主屏幕」，体验接近 App。

### 6.9 日常升级

```bash
# 服务器：拉取最新代码 + 重启后端 + 更新前端
cd /home/cashui
sudo git pull
sudo systemctl restart cashui
# 前端有改动时：重新 build 后更新 dist（见 7.5）
```

---

## 7. 项目文件夹说明（目录结构）

```
CashUI/
├── backend/                      # 后端（Python FastAPI）
│   ├── app/
│   │   ├── main.py               # 应用入口（注册路由、建表、启动定时任务）
│   │   ├── config.py             # 配置（JWT 密钥、数据库地址、默认密码）
│   │   ├── database.py           # 数据库连接与会话
│   │   ├── init_db.py            # 初始化数据库（建表 + 默认管理员 + 科目）
│   │   ├── api/                  # API 路由层
│   │   │   ├── auth.py           #   认证（登录 / 修改密码）
│   │   │   ├── users.py          #   账号管理（增删改、批量、重置密码）
│   │   │   ├── balance.py        #   结余 / 科目 / 科目结转
│   │   │   ├── transactions.py   #   记账（收入 / 支出）
│   │   │   ├── funders.py        #   缴款人
│   │   │   ├── activities.py     #   活动（民主生活会 / 团建 / 聚餐）
│   │   │   ├── votes.py          #   投票
│   │   │   └── reports.py        #   报表下载
│   │   ├── core/                 # 核心模块
│   │   │   ├── deps.py           #   依赖注入（当前用户、角色校验）
│   │   │   └── security.py       #   JWT 与密码哈希
│   │   ├── models/               # 数据库模型（ORM 表）
│   │   ├── schemas/              # Pydantic 请求/响应模型
│   │   └── services/             # 业务逻辑（报表生成、定时任务）
│   ├── requirements.txt          # Python 依赖清单
│   ├── run.py                    # 本地启动脚本
│   ├── manage_accounts.py        # 账号密码管理脚本（不入 git，本地保留）
│   └── .env.example              # 环境变量示例（复制为 .env）
├── frontend/                     # 前端（Vue 3 + Vite + Vant）
│   ├── src/
│   │   ├── main.js               # 入口
│   │   ├── App.vue               # 根组件
│   │   ├── api/                  # 接口封装（index.js / request.js）
│   │   ├── router/index.js       # 路由与登录守卫
│   │   ├── stores/auth.js        # 登录态状态管理
│   │   └── views/                # 页面（11 个）
│   ├── package.json              # 前端依赖
│   ├── vite.config.js            # Vite 配置（/api 代理）
│   └── index.html
├── deploy/
│   └── nginx.conf                # Nginx 部署配置
├── .gitignore                    # Git 忽略规则
└── README.md                     # 本文档
```
