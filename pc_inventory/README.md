# 部门电脑资产采集工具 (pc_inventory)

按部门统计电脑的 **使用人 / 序列号 / IP** 等信息。

工作模式:

```
                   [每台员工电脑]
                  ┌────────────────────┐
                  │ pc_inventory_collect.exe │   <- 登录脚本 / 组策略 / 手动
                  └─────────┬──────────┘
                            │ 写入一份 JSON
                            ▼
              \\\\fileserver\\share\\pc_inventory\\data\\
                            │
                            ▼
                  [管理员电脑, 任意时机执行]
              python -m pc_inventory aggregate
                            │
                            ▼
                   部门电脑清单.xlsx
```

每台电脑的采集结果是一个独立 JSON 文件 (按 `部门__姓名__主机名.json` 命名),
所以即便上百台电脑同时运行也不会冲突, 重复采集会覆盖旧文件 → 永远拿到最新状态。

---

## 一、采集字段

| 字段 | 来源 |
|------|------|
| 部门 / 使用人 | 优先 命令行参数, 其次 `PC_DEPARTMENT` / `PC_REAL_NAME` 环境变量, 再其次 `department_map.csv` 映射 |
| 登录账号 (username) | Windows 当前登录用户 |
| 主机名 (hostname) | `socket.gethostname()` |
| 序列号 (serial_number) | PowerShell `Get-CimInstance Win32_BIOS`, 失败回落到 `wmic bios get serialnumber` |
| 厂商 / 型号 | PowerShell `Win32_ComputerSystem` |
| 主 IP / 全部 IP | 解析 `ipconfig` + 默认路由探测 |
| MAC 地址 | 解析 `ipconfig /all` |
| 操作系统 | `platform.platform()` |
| 采集时间 | 本机当前时间 |

> **不联网, 不发包**, 全部信息从本机系统调用获取。

---

## 二、部署方式

### 准备共享目录

在文件服务器建一个目录, 给"域用户"或者"Authenticated Users" **读 + 写** 权限:

```
\\fileserver\share\pc_inventory\
├── pc_inventory_collect.exe       # 打包后的采集器
├── department_map.csv             # 账号 -> 姓名/部门 映射 (可选)
└── data\                          # 用于接收 JSON 结果, 一开始为空
```

`department_map.csv` 格式 (UTF-8 或 GBK 都可, 列名大小写不敏感):

```csv
username,real_name,department
zhangsan,张三,研发部
lisi,李四,研发部
wangwu,王五,销售部
```

### 方式 A: 域组策略 (GPO) 登录脚本 — 推荐

1. `组策略管理` → 编辑某个 OU 的 GPO →
   `用户配置 → 策略 → Windows 设置 → 脚本(登录/注销)` → 双击"登录"
2. 添加脚本: `\\fileserver\share\pc_inventory\pc_inventory_collect.exe`,
   参数: `-o \\fileserver\share\pc_inventory\data --silent`
3. 用户下次登录就会静默采集一次。

### 方式 B: 计划任务 (无域环境)

在每台电脑创建一个开机任务:

```bat
schtasks /create /tn "PCInventory" /tr ^
  "\\fileserver\share\pc_inventory\pc_inventory_collect.exe -o \\fileserver\share\pc_inventory\data --silent" ^
  /sc onlogon /rl highest /f
```

### 方式 C: 手动一键 .bat (无映射时由员工自己填)

在共享目录里放一个 `跑我.bat`:

```bat
@echo off
set /p DEPT=请输入你的部门:
set /p NAME=请输入你的姓名:
"%~dp0pc_inventory_collect.exe" -o "%~dp0data" -d "%DEPT%" -n "%NAME%"
pause
```

员工双击 → 输入部门和姓名 → 自动上传。

---

## 三、汇总成 Excel

在管理员电脑上 (有 Python + 已 `pip install openpyxl` 即可):

```bash
python -m pc_inventory aggregate -i \\fileserver\share\pc_inventory\data -o 部门电脑清单.xlsx
```

输出 Excel 包含:

- **总览** — 全部电脑, 按部门 + 姓名排序
- **<部门>** — 每个部门一个独立 Sheet
- **未分类** — 没填部门的记录, 用来催员工补
- **汇总** — 各部门电脑数量统计

可加 `--no-dept-sheets` 不为每个部门单独建 Sheet。

---

## 四、采集器命令行参数

```
python -m pc_inventory collect -o <共享目录> [选项]
```

| 参数 | 说明 |
|------|------|
| `-o, --output` | **必填**, 共享目录路径, JSON 写到这里 |
| `-d, --department` | 部门名 (覆盖映射表) |
| `-n, --name` | 使用人姓名 (覆盖映射表) |
| `-m, --map` | 映射 CSV 路径 (默认在 exe 同目录找 `department_map.csv`) |
| `--silent` | 静默模式, 不向控制台输出, 适合登录脚本 |

环境变量 (低于命令行参数, 高于映射表):

- `PC_DEPARTMENT`
- `PC_REAL_NAME`

---

## 五、打包成 .exe (无 Python 环境部署)

双击运行项目根目录的 `build_pc_inventory.bat`, 完成后产物:

```
dist\pc_inventory_collect.exe        <- 单文件 ~ 10 MB
```

把这个文件复制到共享目录, 即可分发。手动打包:

```bash
pip install pyinstaller>=6.3
pyinstaller pc_inventory_collect.spec --clean --noconfirm
```

---

## 六、调试

仅打印当前机器的采集结果, 不写文件:

```bash
python -m pc_inventory info
```

输出形如:

```json
{
  "hostname": "DESKTOP-ABC123",
  "username": "zhangsan",
  "domain": "CORP",
  "os": "Windows-10-10.0.22631-SP0",
  "serial_number": "PF1234XY",
  "primary_ip": "10.20.30.40",
  "all_ips": ["10.20.30.40"],
  "mac": "AA-BB-CC-DD-EE-FF",
  "manufacturer": "LENOVO",
  "model": "ThinkPad T14"
}
```

---

## 七、依赖

- 采集器: 仅依赖 Python 标准库 → 打包后 exe 体积小, 不依赖 PyTorch 等大库
- 汇总器: `openpyxl>=3.0`

```bash
pip install openpyxl
```

---

## 八、目录结构

```
pc_inventory/
├── __init__.py
├── __main__.py                 # 子命令分发: collect / aggregate / info
├── sysinfo.py                  # 跨平台底层采集 (主机名/序列号/IP/MAC...)
├── collect.py                  # 单机采集器
├── aggregate.py                # 汇总成 Excel
├── department_map.example.csv  # 示例映射
└── README.md
```
