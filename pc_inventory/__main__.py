"""支持 ``python -m pc_inventory <子命令>`` 调用.

子命令:
    collect    采集本机信息并输出到共享目录
    aggregate  汇总共享目录里所有 JSON 生成 Excel 报表
    info       仅打印当前机器采集结果到控制台 (调试用)

示例::

    python -m pc_inventory collect -o \\\\server\\share\\pc_inventory_data
    python -m pc_inventory aggregate -i \\\\server\\share\\pc_inventory_data -o 部门电脑清单.xlsx
    python -m pc_inventory info
"""

import sys


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0

    cmd = argv.pop(0)

    if cmd == "collect":
        from . import collect
        return collect.main(argv)
    if cmd == "aggregate":
        from . import aggregate
        return aggregate.main(argv)
    if cmd == "info":
        from . import sysinfo
        import json
        print(json.dumps(sysinfo.gather(), ensure_ascii=False, indent=2))
        return 0

    print(f"未知子命令: {cmd}\n", file=sys.stderr)
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
