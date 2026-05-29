"""跨平台获取本机硬件/网络/账号信息.

主入口::

    info = gather()  # -> dict

返回字段::

    {
        "hostname":       "DESKTOP-ABC123",
        "username":       "zhangsan",
        "domain":         "CORP",
        "os":             "Windows-10-...",
        "serial_number":  "PF1234XY",       # 主板/BIOS 序列号
        "primary_ip":     "10.20.30.40",    # 默认对外网卡的 IPv4
        "all_ips":        ["10.20.30.40"],
        "mac":            "AA-BB-CC-DD-EE-FF",
        "manufacturer":   "LENOVO",
        "model":          "ThinkPad T14",
    }

设计原则:
    1. 全部使用标准库, 不引入 psutil 等额外依赖, 方便 PyInstaller 单文件打包.
    2. 任意一项采集失败不会让整体崩溃, 失败字段返回 None 或空串.
    3. Windows 优先用 PowerShell + CIM, 失败回落到已废弃但仍可用的 wmic.
"""

from __future__ import annotations

import os
import platform
import re
import socket
import subprocess
import sys
import uuid
from typing import List, Optional


# ---------------------------------------------------------------------------
# subprocess 公共参数: 在 Windows 下隐藏黑窗口 (登录脚本场景必需)
# ---------------------------------------------------------------------------
_IS_WINDOWS = sys.platform.startswith("win")
_NO_WINDOW = 0x08000000 if _IS_WINDOWS else 0  # CREATE_NO_WINDOW


def _run(cmd: List[str], timeout: int = 15) -> str:
    """执行外部命令, 返回 stdout 字符串. 失败返回空串."""
    try:
        out = subprocess.check_output(
            cmd,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
            creationflags=_NO_WINDOW,
        )
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return ""
    # Windows 中文系统输出常是 GBK; 优先 UTF-8 然后 GBK
    for enc in ("utf-8", "gbk", "latin-1"):
        try:
            return out.decode(enc).strip()
        except UnicodeDecodeError:
            continue
    return ""


# ---------------------------------------------------------------------------
# 用户 / 主机
# ---------------------------------------------------------------------------
def get_username() -> str:
    """获取当前登录账号. 优先环境变量, 兜底 getpass."""
    for key in ("USERNAME", "USER", "LOGNAME"):
        val = os.environ.get(key)
        if val:
            return val
    try:
        import getpass
        return getpass.getuser()
    except Exception:
        return ""


def get_domain() -> str:
    return os.environ.get("USERDOMAIN") or os.environ.get("USERDNSDOMAIN") or ""


def get_hostname() -> str:
    try:
        return socket.gethostname() or platform.node()
    except Exception:
        return platform.node()


# ---------------------------------------------------------------------------
# 序列号 / 厂商 / 型号 (Windows)
# ---------------------------------------------------------------------------
_PS_BIOS = (
    "powershell", "-NoProfile", "-NonInteractive", "-Command",
    "(Get-CimInstance -ClassName Win32_BIOS).SerialNumber"
)
_PS_CSPRODUCT = (
    "powershell", "-NoProfile", "-NonInteractive", "-Command",
    "$p=Get-CimInstance -ClassName Win32_ComputerSystem;"
    "Write-Output ($p.Manufacturer + '|' + $p.Model)"
)


def get_serial_number_windows() -> str:
    s = _run(list(_PS_BIOS))
    if s and s.lower() not in ("to be filled by o.e.m.", "default string", "none"):
        return s
    # 回落到 wmic (Win 11 22H2 起逐步移除, 但绝大多数现网仍有)
    out = _run(["wmic", "bios", "get", "serialnumber"])
    if out:
        for line in out.splitlines()[1:]:
            v = line.strip()
            if v:
                return v
    return ""


def get_manufacturer_model_windows() -> tuple:
    s = _run(list(_PS_CSPRODUCT))
    if s and "|" in s:
        m, model = s.split("|", 1)
        return m.strip(), model.strip()
    out = _run(["wmic", "computersystem", "get", "manufacturer,model", "/format:csv"])
    if out:
        # CSV: Node,Manufacturer,Model
        for line in out.splitlines()[1:]:
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 3 and parts[1]:
                return parts[1], parts[2]
    return "", ""


def get_serial_number_linux() -> str:
    """Linux 兜底, 仅在沙箱测试用."""
    for path in (
        "/sys/class/dmi/id/product_serial",
        "/sys/class/dmi/id/board_serial",
    ):
        try:
            with open(path) as f:
                v = f.read().strip()
                if v and v.lower() not in ("none", "default string"):
                    return v
        except (PermissionError, FileNotFoundError):
            continue
    return ""


# ---------------------------------------------------------------------------
# 网络: IP / MAC
# ---------------------------------------------------------------------------
def get_primary_ip() -> Optional[str]:
    """获取默认外联网卡的 IPv4. 不真正发包, 只触发路由选择."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return None
    finally:
        s.close()


def _ips_from_ipconfig() -> List[str]:
    out = _run(["ipconfig"])
    if not out:
        return []
    ips = re.findall(r"IPv4[^\n:]*[:\.]\s*([0-9]+(?:\.[0-9]+){3})", out)
    return [ip for ip in ips if not ip.startswith("127.") and not ip.startswith("169.254.")]


def _ips_from_hostname() -> List[str]:
    try:
        _, _, addrs = socket.gethostbyname_ex(socket.gethostname())
        return [a for a in addrs if not a.startswith("127.")]
    except OSError:
        return []


def get_all_ips() -> List[str]:
    """汇总所有非回环的 IPv4. Windows 优先解析 ipconfig 结果."""
    ips: List[str] = []
    if _IS_WINDOWS:
        ips = _ips_from_ipconfig()
    if not ips:
        ips = _ips_from_hostname()
    primary = get_primary_ip()
    if primary and primary not in ips:
        ips.insert(0, primary)
    # 去重保序
    seen = set()
    result = []
    for ip in ips:
        if ip not in seen:
            seen.add(ip)
            result.append(ip)
    return result


def _mac_from_ipconfig(target_ip: Optional[str]) -> str:
    """从 ipconfig /all 中找出包含 target_ip 的网卡的物理地址."""
    out = _run(["ipconfig", "/all"])
    if not out:
        return ""
    blocks = re.split(r"\r?\n\r?\n", out)
    for block in blocks:
        if target_ip and target_ip in block:
            m = re.search(r"([0-9A-Fa-f]{2}(?:[-:][0-9A-Fa-f]{2}){5})", block)
            if m:
                return m.group(1).upper().replace(":", "-")
    # 没匹配上 IP, 取第一个非全零的 MAC
    m = re.search(r"([0-9A-Fa-f]{2}(?:[-:][0-9A-Fa-f]{2}){5})", out)
    return m.group(1).upper().replace(":", "-") if m else ""


def get_mac(primary_ip: Optional[str] = None) -> str:
    if _IS_WINDOWS:
        v = _mac_from_ipconfig(primary_ip)
        if v:
            return v
    # uuid.getnode 在容器/虚拟环境下可能返回随机值, 仅作兜底
    node = uuid.getnode()
    if (node >> 40) & 0x01:  # 多播位被置 = uuid 模块返回的是随机值
        return ""
    return "-".join(f"{(node >> i) & 0xFF:02X}" for i in range(40, -1, -8))


# ---------------------------------------------------------------------------
# 汇总
# ---------------------------------------------------------------------------
def gather() -> dict:
    primary_ip = get_primary_ip()
    all_ips = get_all_ips()

    if _IS_WINDOWS:
        serial = get_serial_number_windows()
        manufacturer, model = get_manufacturer_model_windows()
    else:
        serial = get_serial_number_linux()
        manufacturer, model = "", ""

    return {
        "hostname": get_hostname(),
        "username": get_username(),
        "domain": get_domain(),
        "os": platform.platform(),
        "serial_number": serial,
        "primary_ip": primary_ip or "",
        "all_ips": all_ips,
        "mac": get_mac(primary_ip),
        "manufacturer": manufacturer,
        "model": model,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(gather(), ensure_ascii=False, indent=2))
