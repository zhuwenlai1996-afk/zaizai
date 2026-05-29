#!/usr/bin/env python3
"""Attendance ranking automation for Hefei base (合肥基地氛围排名)."""

import argparse
import os
import sys
from datetime import datetime, date, timedelta

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import BarChart, Reference
from openpyxl.utils import get_column_letter



def read_parameters(wb):
    """Read parameters from 参数设置 sheet."""
    ws = wb['参数设置']
    start_date = ws['B4'].value
    end_date = ws['B5'].value
    threshold = ws['B6'].value

    # Convert datetime to date if needed
    if isinstance(start_date, datetime):
        start_date = start_date.date()
    if isinstance(end_date, datetime):
        end_date = end_date.date()

    # Special workdays (E5:E100)
    special_workdays = set()
    for row in ws.iter_rows(min_row=5, max_row=100, min_col=5, max_col=5, values_only=True):
        val = row[0]
        if val is not None:
            if isinstance(val, datetime):
                special_workdays.add(val.date())
            elif isinstance(val, date):
                special_workdays.add(val)

    # Excluded dates (H5:H100)
    excluded_dates = set()
    for row in ws.iter_rows(min_row=5, max_row=100, min_col=8, max_col=8, values_only=True):
        val = row[0]
        if val is not None:
            if isinstance(val, datetime):
                excluded_dates.add(val.date())
            elif isinstance(val, date):
                excluded_dates.add(val)

    # 职能部门 (K5:L10)
    zhineng_depts = []
    for row in ws.iter_rows(min_row=5, max_row=10, min_col=11, max_col=12, values_only=True):
        if row[0] is not None:
            zhineng_depts.append({'name': row[0], 'leader': row[1]})

    # 销售部门 (N5:O9)
    xiaoshou_depts = []
    for row in ws.iter_rows(min_row=5, max_row=9, min_col=14, max_col=15, values_only=True):
        if row[0] is not None:
            xiaoshou_depts.append({'name': row[0], 'leader': row[1]})

    return {
        'start_date': start_date,
        'end_date': end_date,
        'threshold': threshold,
        'special_workdays': special_workdays,
        'excluded_dates': excluded_dates,
        'zhineng_depts': zhineng_depts,
        'xiaoshou_depts': xiaoshou_depts,
    }


def read_roster(wb):
    """Read staff roster from 名单_维护 sheet."""
    ws = wb['名单_维护']
    roster = []
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=7, values_only=True):
        if row[0] is not None:
            roster.append({
                'employee_id': str(row[0]).strip(),
                'department': row[1],
                'hrbp': row[2],
                'name': row[3],
                'is_counted': row[4],
                'entry_leave_time': row[5],
                'mark': row[6],
            })
    return roster


def read_source_data(wb):
    """Read attendance source data from 源数据_粘贴 sheet (columns A:R only)."""
    ws = wb['源数据_粘贴']
    records = []
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=18, values_only=True):
        if row[2] is not None:  # 工号 in column C (index 2)
            employee_id = str(row[2]).strip()
            att_date = row[11]  # 考勤日期 column L (index 11)
            work_hours = row[16]  # 工作时长 column Q (index 16)
            if att_date is not None:
                if isinstance(att_date, datetime):
                    att_date = att_date.date()
                if work_hours is None:
                    work_hours = 0.0
                else:
                    work_hours = float(work_hours)
                records.append({
                    'employee_id': employee_id,
                    'date': att_date,
                    'hours': work_hours,
                })
    return records


def classify_date(d, excluded_dates, special_workdays):
    """Classify a date into: 排除, 工作日, 普通周六, 周日."""
    if d in excluded_dates:
        return '排除'
    if d.weekday() < 5 or d in special_workdays:
        return '工作日'
    if d.weekday() == 5:
        return '普通周六'
    return '周日'


def calculate_working_days(start_date, end_date, excluded_dates, special_workdays):
    """Calculate the number of working days in the date range."""
    count = 0
    current = start_date
    while current <= end_date:
        if current not in excluded_dates:
            if current.weekday() < 5:
                count += 1
            elif current in special_workdays:
                count += 1
        current += timedelta(days=1)
    return count


def calculate_rankings(params, roster, records):
    """Calculate individual and department rankings."""
    start_date = params['start_date']
    end_date = params['end_date']
    threshold = params['threshold']
    excluded_dates = params['excluded_dates']
    special_workdays = params['special_workdays']

    workday_count = calculate_working_days(start_date, end_date, excluded_dates, special_workdays)

    # Build lookup: employee_id -> list of records
    records_by_id = {}
    for rec in records:
        eid = rec['employee_id']
        if eid not in records_by_id:
            records_by_id[eid] = []
        records_by_id[eid].append(rec)

    # Calculate per-person stats
    individual_results = []
    all_dept_names_zhineng = {d['name'] for d in params['zhineng_depts']}
    all_dept_names_xiaoshou = {d['name'] for d in params['xiaoshou_depts']}

    for person in roster:
        eid = person['employee_id']
        person_records = records_by_id.get(eid, [])

        workday_total = 0.0
        valid_days = 0
        saturday_total = 0.0

        for rec in person_records:
            d = rec['date']
            if d < start_date or d > end_date:
                continue
            date_type = classify_date(d, excluded_dates, special_workdays)
            if date_type == '排除':
                continue
            if date_type == '工作日':
                if rec['hours'] >= threshold:
                    workday_total += rec['hours']
                    valid_days += 1
            elif date_type == '普通周六':
                saturday_total += rec['hours']

        # Average calculation: matches the original Excel formula behavior.
        # workday_total is divided by valid_days (days actually worked), while
        # saturday_total is divided by workday_count (total working days in the
        # period) rather than by saturdays attended, spreading Saturday hours
        # across the full working-day denominator.
        if valid_days == 0 or workday_count == 0:
            average = 0.0
        else:
            average = (workday_total / valid_days) + (saturday_total / workday_count)

        # Determine department type
        dept = person['department']
        if dept in all_dept_names_zhineng:
            dept_type = '职能部门'
        elif dept in all_dept_names_xiaoshou:
            dept_type = '销售部门'
        else:
            dept_type = '未分类'

        # Anomaly notes
        notes = ''
        if person['is_counted'] == '不统计':
            notes = '不统计：参与个人排名/不计部门排名'
        elif valid_days == 0 and person['is_counted'] == '统计':
            notes = '无有效工作日记录'

        individual_results.append({
            'employee_id': eid,
            'department': dept,
            'dept_type': dept_type,
            'hrbp': person['hrbp'],
            'name': person['name'],
            'is_counted': person['is_counted'],
            'workday_total': round(workday_total, 2),
            'valid_days': valid_days,
            'saturday_total': round(saturday_total, 2),
            'workday_count': workday_count,
            'average': average,
            'notes': notes,
        })

    # Sort by average descending for ranking
    individual_results.sort(key=lambda x: x['average'], reverse=True)

    # Assign ranks (standard competition ranking)
    # Round averages to 10 decimal places before comparing to avoid
    # floating-point noise causing different ranks for effectively equal values.
    if individual_results:
        rank = 1
        individual_results[0]['rank'] = rank
        for i in range(1, len(individual_results)):
            if round(individual_results[i]['average'], 10) < round(individual_results[i - 1]['average'], 10):
                rank = i + 1
            individual_results[i]['rank'] = rank

    # Department ranking
    def calc_dept_ranking(dept_list):
        dept_results = []
        for dept_info in dept_list:
            dept_name = dept_info['name']
            members = [r for r in individual_results
                       if r['department'] == dept_name
                       and r['is_counted'] == '统计'
                       and r['average'] > 0]
            if members:
                dept_avg = sum(m['average'] for m in members) / len(members)
            else:
                dept_avg = 0.0
            dept_results.append({
                'name': dept_name,
                'leader': dept_info['leader'],
                'average': dept_avg,
                'member_count': len(members),
            })
        # Sort and rank
        dept_results.sort(key=lambda x: x['average'], reverse=True)
        if dept_results:
            r = 1
            dept_results[0]['rank'] = r
            for i in range(1, len(dept_results)):
                if dept_results[i]['average'] < dept_results[i - 1]['average']:
                    r = i + 1
                dept_results[i]['rank'] = r
        return dept_results

    zhineng_ranking = calc_dept_ranking(params['zhineng_depts'])
    xiaoshou_ranking = calc_dept_ranking(params['xiaoshou_depts'])

    # Count unmatched records
    roster_ids = {p['employee_id'] for p in roster}
    unmatched = sum(1 for rec in records if rec['employee_id'] not in roster_ids)

    return {
        'individual': individual_results,
        'zhineng': zhineng_ranking,
        'xiaoshou': xiaoshou_ranking,
        'workday_count': workday_count,
        'unmatched_records': unmatched,
        'total_records': len(records),
    }


def generate_output(params, results, output_path):
    """Generate the output Excel file with formatting and charts."""
    wb = openpyxl.Workbook()

    # Styles
    header_fill = PatternFill(start_color='1F4E79', end_color='1F4E79', fill_type='solid')
    header_font = Font(bold=True, color='FFFFFF', size=11)
    green_fill = PatternFill(start_color='C5ECC5', end_color='C5ECC5', fill_type='solid')
    red_fill = PatternFill(start_color='F4CCCC', end_color='F4CCCC', fill_type='solid')
    gray_fill = PatternFill(start_color='F2F2F2', end_color='F2F2F2', fill_type='solid')
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    # ---- Sheet 1: 个人排名 ----
    ws1 = wb.active
    ws1.title = '个人排名'
    headers = ['名次', '工号', '部门', '部门类型', 'HRBP', '姓名', '是否统计',
               '工作日总时长', '工作日有效天数', '普通周六总时长', '工作日天数', '平均时长', '异常提示']

    for col, h in enumerate(headers, 1):
        cell = ws1.cell(row=1, column=col, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = thin_border

    # Determine bottom 10 non-zero avg rows
    non_zero = [r for r in results['individual'] if r['average'] > 0]
    bottom_10_indices = set()
    if len(non_zero) > 10:
        bottom_10 = non_zero[-10:]
        bottom_10_ids = {(r['employee_id'], r['name']) for r in bottom_10}
    else:
        bottom_10_ids = set()

    for i, person in enumerate(results['individual']):
        row_num = i + 2
        values = [
            person['rank'],
            person['employee_id'],
            person['department'],
            person['dept_type'],
            person['hrbp'],
            person['name'],
            person['is_counted'],
            person['workday_total'],
            person['valid_days'],
            person['saturday_total'],
            person['workday_count'],
            round(person['average'], 2),
            person['notes'],
        ]
        for col, val in enumerate(values, 1):
            cell = ws1.cell(row=row_num, column=col, value=val)
            cell.border = thin_border
            cell.alignment = Alignment(horizontal='center', vertical='center')
            if col == 12:  # 平均时长
                cell.number_format = '0.00'

        # Conditional formatting
        is_in_bottom_10 = (person['employee_id'], person['name']) in bottom_10_ids
        if i < 10:
            # Top 10 green
            for col in range(1, 14):
                ws1.cell(row=row_num, column=col).fill = green_fill
        elif is_in_bottom_10:
            # Bottom 10 non-zero red
            for col in range(1, 14):
                ws1.cell(row=row_num, column=col).fill = red_fill
        elif row_num % 2 == 0:
            # Alternating gray
            for col in range(1, 14):
                ws1.cell(row=row_num, column=col).fill = gray_fill

    # Auto-fit column widths
    col_widths = [6, 10, 18, 10, 10, 10, 8, 14, 14, 14, 10, 10, 30]
    for i, w in enumerate(col_widths, 1):
        ws1.column_dimensions[get_column_letter(i)].width = w

    # ---- Sheet 2: 部门排名 ----
    ws2 = wb.create_sheet('部门排名')

    # 职能部门排名 (A1:D)
    zn_headers = ['部门', '一号位', '平均时长', '名次']
    for col, h in enumerate(zn_headers, 1):
        cell = ws2.cell(row=1, column=col, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = thin_border

    for i, dept in enumerate(results['zhineng']):
        row_num = i + 2
        ws2.cell(row=row_num, column=1, value=dept['name']).border = thin_border
        ws2.cell(row=row_num, column=2, value=dept['leader']).border = thin_border
        cell = ws2.cell(row=row_num, column=3, value=round(dept['average'], 2))
        cell.number_format = '0.00'
        cell.border = thin_border
        ws2.cell(row=row_num, column=4, value=dept['rank']).border = thin_border

    # 销售部门排名 (F1:I)
    xs_headers = ['部门', '一号位', '平均时长', '名次']
    for col, h in enumerate(xs_headers, 1):
        cell = ws2.cell(row=1, column=col + 5, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = thin_border

    for i, dept in enumerate(results['xiaoshou']):
        row_num = i + 2
        ws2.cell(row=row_num, column=6, value=dept['name']).border = thin_border
        ws2.cell(row=row_num, column=7, value=dept['leader']).border = thin_border
        cell = ws2.cell(row=row_num, column=8, value=round(dept['average'], 2))
        cell.number_format = '0.00'
        cell.border = thin_border
        ws2.cell(row=row_num, column=9, value=dept['rank']).border = thin_border

    # Column widths for dept sheet
    for col in [1, 6]:
        ws2.column_dimensions[get_column_letter(col)].width = 22
    for col in [2, 7]:
        ws2.column_dimensions[get_column_letter(col)].width = 14
    for col in [3, 8]:
        ws2.column_dimensions[get_column_letter(col)].width = 12
    for col in [4, 9]:
        ws2.column_dimensions[get_column_letter(col)].width = 8

    # Bar chart for 职能部门
    zn_chart = BarChart()
    zn_chart.type = 'col'
    zn_chart.title = '职能部门平均时长'
    zn_chart.y_axis.title = '平均时长(h)'
    zn_chart.x_axis.title = '部门'
    zn_count = len(results['zhineng'])
    data_ref = Reference(ws2, min_col=3, min_row=1, max_row=zn_count + 1)
    cats_ref = Reference(ws2, min_col=1, min_row=2, max_row=zn_count + 1)
    zn_chart.add_data(data_ref, titles_from_data=True)
    zn_chart.set_categories(cats_ref)
    zn_chart.shape = 4
    zn_chart.width = 15
    zn_chart.height = 10
    ws2.add_chart(zn_chart, 'A' + str(zn_count + 4))

    # Bar chart for 销售部门
    xs_chart = BarChart()
    xs_chart.type = 'col'
    xs_chart.title = '销售部门平均时长'
    xs_chart.y_axis.title = '平均时长(h)'
    xs_chart.x_axis.title = '部门'
    xs_count = len(results['xiaoshou'])
    data_ref2 = Reference(ws2, min_col=8, min_row=1, max_row=xs_count + 1)
    cats_ref2 = Reference(ws2, min_col=6, min_row=2, max_row=xs_count + 1)
    xs_chart.add_data(data_ref2, titles_from_data=True)
    xs_chart.set_categories(cats_ref2)
    xs_chart.shape = 4
    xs_chart.width = 15
    xs_chart.height = 10
    ws2.add_chart(xs_chart, 'F' + str(xs_count + 4))

    # ---- Sheet 3: 月度排名 ----
    ws3 = wb.create_sheet('月度排名')
    start_str = params['start_date'].strftime('%Y-%m-%d')
    end_str = params['end_date'].strftime('%Y-%m-%d')
    title = f"{start_str}~{end_str} 合肥基地氛围排名"

    title_cell = ws3.cell(row=1, column=1, value=title)
    title_cell.font = Font(bold=True, size=14)
    ws3.merge_cells('A1:J1')

    # 个人TOP10 (cols A-E)
    top10_headers = ['名次', '工号', '姓名', '部门', '平均时长']
    for col, h in enumerate(top10_headers, 1):
        cell = ws3.cell(row=3, column=col, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = thin_border

    top10 = results['individual'][:10]
    for i, person in enumerate(top10):
        row_num = i + 4
        ws3.cell(row=row_num, column=1, value=person['rank']).border = thin_border
        ws3.cell(row=row_num, column=2, value=person['employee_id']).border = thin_border
        ws3.cell(row=row_num, column=3, value=person['name']).border = thin_border
        ws3.cell(row=row_num, column=4, value=person['department']).border = thin_border
        cell = ws3.cell(row=row_num, column=5, value=round(person['average'], 2))
        cell.number_format = '0.00'
        cell.border = thin_border

    # 部门排名 (cols G-J)
    dept_headers = ['类别', '部门', '一号位', '平均时长']
    for col, h in enumerate(dept_headers, 1):
        cell = ws3.cell(row=3, column=col + 6, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = thin_border

    all_depts = []
    for d in results['zhineng']:
        all_depts.append({'category': '职能部门', **d})
    for d in results['xiaoshou']:
        all_depts.append({'category': '销售部门', **d})

    for i, dept in enumerate(all_depts):
        row_num = i + 4
        ws3.cell(row=row_num, column=7, value=dept['category']).border = thin_border
        ws3.cell(row=row_num, column=8, value=dept['name']).border = thin_border
        ws3.cell(row=row_num, column=9, value=dept['leader']).border = thin_border
        cell = ws3.cell(row=row_num, column=10, value=round(dept['average'], 2))
        cell.number_format = '0.00'
        cell.border = thin_border

    # Column widths
    for col in range(1, 6):
        ws3.column_dimensions[get_column_letter(col)].width = 12
    for col in range(7, 11):
        ws3.column_dimensions[get_column_letter(col)].width = 16

    # ---- Sheet 4: 检查项 ----
    ws4 = wb.create_sheet('检查项')
    check_headers = ['检查项', '结果', '建议/说明', '状态']
    for col, h in enumerate(check_headers, 1):
        cell = ws4.cell(row=1, column=col, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = thin_border

    start_str = params['start_date'].strftime('%Y-%m-%d')
    end_str = params['end_date'].strftime('%Y-%m-%d')
    total_staff = len(results['individual'])
    counted = sum(1 for r in results['individual'] if r['is_counted'] == '统计')
    not_counted = total_staff - counted
    special_count = len(params['special_workdays'])
    excluded_count = len(params['excluded_dates'])

    checks = [
        ['源数据日期范围', f'{start_str} ~ {end_str}', '参数设置中配置的统计周期', 'OK'],
        ['源数据记录数', str(results['total_records']), '源数据_粘贴 有效记录数', 'OK'],
        ['工作日天数', str(results['workday_count']), '根据日期范围和排除日计算', 'OK'],
        ['花名册总人数', str(total_staff), '名单_维护 中的全部人员', 'OK'],
        ['统计人数', str(counted), '是否统计=统计 的人员数', 'OK'],
        ['特殊工作日数', str(special_count), '周末但算工作日的天数', 'OK'],
        ['排除日期数', str(excluded_count), '法定假日等不计入的天数', 'OK'],
        ['未匹配记录数', str(results['unmatched_records']), '源数据中工号不在花名册的记录', '注意' if results['unmatched_records'] > 0 else 'OK'],
        ['不统计人员参与排名', str(not_counted), '不统计人员参与个人排名但不计入部门排名', 'OK'],
    ]

    for i, check in enumerate(checks):
        row_num = i + 2
        for col, val in enumerate(check, 1):
            cell = ws4.cell(row=row_num, column=col, value=val)
            cell.border = thin_border
            cell.alignment = Alignment(horizontal='center', vertical='center')

    # Column widths for checks
    ws4.column_dimensions['A'].width = 18
    ws4.column_dimensions['B'].width = 20
    ws4.column_dimensions['C'].width = 35
    ws4.column_dimensions['D'].width = 8

    # Save
    wb.save(output_path)
    return output_path


def run(input_path, output_path):
    """Main execution function."""
    print(f"[1/5] 加载工作簿: {input_path}")
    wb = openpyxl.load_workbook(input_path, data_only=True)

    print("[2/5] 读取参数设置...")
    params = read_parameters(wb)
    print(f"      统计周期: {params['start_date']} ~ {params['end_date']}")
    print(f"      工时阈值: {params['threshold']}h")
    print(f"      特殊工作日: {len(params['special_workdays'])} 天")
    print(f"      排除日期: {len(params['excluded_dates'])} 天")

    print("[3/5] 读取花名册和源数据...")
    roster = read_roster(wb)
    records = read_source_data(wb)
    print(f"      花名册: {len(roster)} 人")
    print(f"      源数据: {len(records)} 条记录")

    print("[4/5] 计算排名...")
    results = calculate_rankings(params, roster, records)
    print(f"      工作日天数: {results['workday_count']}")
    top = results['individual'][0]
    print(f"      个人第1名: {top['name']} ({top['department']}) 平均 {top['average']:.2f}h")
    print(f"      职能部门第1: {results['zhineng'][0]['name']} 平均 {results['zhineng'][0]['average']:.2f}h")
    print(f"      销售部门第1: {results['xiaoshou'][0]['name']} 平均 {results['xiaoshou'][0]['average']:.2f}h")

    print(f"[5/5] 生成输出文件: {output_path}")
    generate_output(params, results, output_path)
    print("完成!")

    return results


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description='合肥基地氛围排名自动化工具')
    parser.add_argument('-i', '--input', default='合肥基地氛围排名_严格排查修复_全名单个人排名.xlsx',
                        help='输入Excel文件路径')
    parser.add_argument('-o', '--output', default='合肥基地氛围排名_输出.xlsx',
                        help='输出Excel文件路径')
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"错误: 输入文件不存在: {args.input}")
        sys.exit(1)

    run(args.input, args.output)


if __name__ == '__main__':
    main()
