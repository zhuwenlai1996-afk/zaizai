"""单机采集器: 在每台电脑上运行, 输出一份 JSON 到共享目录.

部署方式建议:
    1. 用 PyInstaller 打包成 ``pc_inventory_collect.exe``
    2. 把 exe 放到一个所有员工都可读 / 可写的共享目录, 例如:
           \\\\fileserver\\share\\pc_inventory\\
    3. 在共享目录里准备:
       - ``pc_inventory_collect.exe``
       - ``department_map.csv``    (可选, 账号 -> 姓名/部门 映射)
       - 一个空目录 ``data\\`` 用于接收采集结果
    4. 通过 域组策略 / 登录脚本 / 定时任务 / 一键 .bat 调用:

           pc_inventory_collect.exe -o \\\\fileserver\\share\\pc_inventory\\data --silent

JSON 文件名规则::

    {部门}__{姓名}__{主机名}.json     (有部门映射时)
    {主机名}__{用户名}.json           (无映射时)

同一台主机重复采集会**覆盖**之前的文件, 保证最终目录里每台机器只有一份最新记录.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import datetime
from typing import Dict, Optional

from . import sysinfo


# ---------------------------------------------------------------------------
# 部门映射
# ---------------------------------------------------------------------------
def load_department_map(path: Optional[str]) -> Dict[str, dict]:
    """从 CSV 加载 ``username -> {real_name, department}`` 映射.

    CSV 列名 (大小写不敏感, 多余列会被忽略)::

        username, real_name, department

    找不到文件时返回空字典, 不抛异常.
    """
    if not path or not os.path.isfile(path):
        return {}
    mapping: Dict[str, dict] = {}
    # 支持 utf-8-sig (带 BOM 的 Excel 另存为)
    for enc in ("utf-8-sig", "utf-8", "gbk"):
        try:
            with open(path, encoding=enc, newline="") as f:
                reader = csv.DictReader(f)
                # 把列名都小写化, 容错用户大小写不一
                for row in reader:
                    norm = {(k or "").strip().lower(): (v or "").strip()
                            for k, v in row.items()}
                    user = norm.get("username") or norm.get("account") or norm.get("账号")
                    if not user:
                        continue
                    mapping[user.lower()] = {
                        "real_name": norm.get("real_name") or norm.get("name") or norm.get("姓名") or "",
                        "department": norm.get("department") or norm.get("dept") or norm.get("部门") or "",
                    }
            return mapping
        except UnicodeDecodeError:
            continue
        except (OSError, csv.Error):
            return {}
    return {}


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def _safe_filename(s: str) -> str:
    """剔除文件名里非法字符."""
    if not s:
        return "_"
    return "".join(c if c not in r'<>:"/\|?*' else "_" for c in s).strip() or "_"


def collect_record(
    *,
    department: Optional[str] = None,
    real_name: Optional[str] = None,
    map_path: Optional[str] = None,
) -> dict:
    """组装一份完整的采集记录."""
    info = sysinfo.gather()

    # 部门 / 姓名 优先级: 命令行参数 > 环境变量 > 映射表 > 空
    dept_map = load_department_map(map_path)
    mapped = dept_map.get(info["username"].lower(), {}) if info["username"] else {}

    final_department = (
        department
        or os.environ.get("PC_DEPARTMENT")
        or mapped.get("department", "")
    )
    final_real_name = (
        real_name
        or os.environ.get("PC_REAL_NAME")
        or mapped.get("real_name", "")
    )

    record = {
        "schema_version": 1,
        "collected_at": datetime.now().isoformat(timespec="seconds"),
        "department": final_department,
        "real_name": final_real_name,
        **info,
    }
    return record


def write_record(record: dict, output_dir: str) -> str:
    """把记录写入 ``output_dir`` 下的 JSON 文件, 返回完整路径."""
    os.makedirs(output_dir, exist_ok=True)

    if record["department"] and record["real_name"]:
        fname = f"{record['department']}__{record['real_name']}__{record['hostname']}.json"
    else:
        fname = f"{record['hostname']}__{record['username'] or 'unknown'}.json"

    path = os.path.join(output_dir, _safe_filename(fname))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    return path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="pc_inventory collect",
        description="采集本机的部门/使用人/序列号/IP, 输出到共享目录.",
    )
    parser.add_argument(
        "-o", "--output", required=True,
        help="共享目录路径, 例如 \\\\server\\share\\pc_inventory\\data",
    )
    parser.add_argument(
        "-d", "--department", default=None,
        help="部门名 (覆盖映射表). 也可用环境变量 PC_DEPARTMENT.",
    )
    parser.add_argument(
        "-n", "--name", dest="real_name", default=None,
        help="使用人姓名 (覆盖映射表). 也可用环境变量 PC_REAL_NAME.",
    )
    parser.add_argument(
        "-m", "--map", dest="map_path", default=None,
        help="账号映射 CSV 路径, 默认在 exe 同目录找 department_map.csv.",
    )
    parser.add_argument(
        "--silent", action="store_true",
        help="静默模式, 不向控制台输出 (登录脚本场景使用).",
    )

    args = parser.parse_args(argv)

    # 默认映射表: exe 同目录 / 当前目录
    map_path = args.map_path
    if map_path is None:
        for guess in (
            os.path.join(os.path.dirname(_executable_dir()), "department_map.csv"),
            os.path.join(_executable_dir(), "department_map.csv"),
            os.path.abspath("department_map.csv"),
        ):
            if os.path.isfile(guess):
                map_path = guess
                break

    try:
        record = collect_record(
            department=args.department,
            real_name=args.real_name,
            map_path=map_path,
        )
        path = write_record(record, args.output)
    except Exception as exc:  # 任何意外都不应让登录脚本失败
        if not args.silent:
            print(f"[pc_inventory] 采集失败: {exc}", file=sys.stderr)
        return 1

    if not args.silent:
        print(f"[pc_inventory] 采集成功 -> {path}")
        print(f"  主机: {record['hostname']}  用户: {record['username']}")
        print(f"  部门: {record['department'] or '(未填)'}  姓名: {record['real_name'] or '(未填)'}")
        print(f"  序列号: {record['serial_number'] or '(未取到)'}")
        print(f"  主 IP: {record['primary_ip']}  全部 IP: {record['all_ips']}")
    return 0


def _executable_dir() -> str:
    """获取 exe / 脚本所在目录, 兼容 PyInstaller 打包后的环境."""
    if getattr(sys, "frozen", False):  # PyInstaller --onefile 也是 frozen
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


if __name__ == "__main__":
    raise SystemExit(main())
