"""部门电脑资产采集工具.

子模块:
    sysinfo   - 跨平台获取主机名/序列号/IP/MAC/用户等
    collect   - 单机采集器: 在每台电脑上运行, 输出一份 JSON 到共享目录
    aggregate - 汇总器: 在管理员电脑上运行, 合并共享目录的 JSON 成 Excel
"""

__version__ = "0.1.0"
