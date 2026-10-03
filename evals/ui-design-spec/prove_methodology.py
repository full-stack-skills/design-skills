"""Reproduce a scoped specification delivery and fault injections, without rendering."""
import argparse
import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / 'skills/ui-design-spec/scripts'
sys.path.insert(0, str(SCRIPTS))
from validate_functional_design import validate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path, help='New evidence directory; existing directories are refused')
    args = parser.parse_args()
    root = args.output.resolve()
    if root.exists():
        parser.error('Output already exists; choose a new directory to preserve evidence')
    package = root / 'package'
    (package / 'pages').mkdir(parents=True)
    def write(name, value):
        (package / name).write_text(value, encoding='utf-8', newline='\n')
    def write_json(name, value):
        write(name, json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    surface_rows = [('P01-01', 'screen', None, '订单列表'),
                    ('P01-02', 'drawer', 'P01-01', '导出范围'),
                    ('P01-A01', 'action', 'P01-01', '打开导出'),
                    ('P01-A02', 'action', 'P01-02', '提交导出'),
                    ('P01-S01', 'loading', 'P01-02', '处理与结果核对'),
                    ('P01-E01', 'error', 'P01-02', '已确认失败'),
                    ('P01-R01', 'result', 'P01-01', '导出结果')]
    actions = [dict(id='P01-A01', name='打开导出', precondition='订单读取权限且列表已加载',
                    effect='只打开范围抽屉，不生成文件', source='P01-01', target='P01-02', cancel='P01-01'),
               dict(id='P01-A02', name='提交导出', precondition='导出权限、范围有效、无重复提交',
                    effect='创建导出任务；确认完成后展示结果', source='P01-02', target='P01-R01', cancel='P01-02')]
    page = dict(id='P01', name='订单与导出', scope='当前组织', nav='订单', phase='Draft',
                purpose='定位订单并导出明确范围', entry='订单菜单',
                layout='筛选工具栏、订单表格、导出范围抽屉', fields='订单号、状态、金额、更新时间；导出范围',
                validation='组织与范围一致；权限有效；提交中禁止重复触发',
                state='加载、空列表、只读、执行中、结果未知',
                error='已确认失败保留范围；未知结果先核对请求状态', result='下载结果和任务标识',
                requirements='演示合同，不是生产业务实现或批准',
                views=[{'id':'P01-01','name':'订单列表'}, {'id':'P01-02','name':'导出范围'}], actions=actions)
    tasks, units = [], []
    acceptance = {
        'P01-01': '显示订单号、状态、金额和更新时间；空列表保留筛选入口；返回保持组织与筛选',
        'P01-02': '范围不可跨组织；抽屉打开不重排底图；取消保留列表位置并恢复导出按钮焦点',
        'P01-A01': '具备读取权限才能打开；打开/取消不创建导出任务；无权限显示原因和返回入口',
        'P01-A02': '具备导出权限且范围有效才能提交；进行中禁止重复触发；确认完成后才进入结果面',
        'P01-S01': '展示请求标识和当前任务状态；超时标为结果未知；先核对状态再决定继续等待或重试',
        'P01-E01': '已确认失败才进入本面；显示原因并保留范围；修复入口回到原范围，不能宣称未知写入已回滚',
        'P01-R01': '显示已完成任务标识、导出范围与下载入口；下载失败保留结果并提供重新获取入口',
    }
    for i, (sid, kind, parent, title) in enumerate(surface_rows, 1):
        tid, uid = f'T{i:02}', f'DU{i:02}'
        parent_i = next((j for j, s in enumerate(surface_rows, 1) if s[0] == parent), None)
        parent_task = f'T{parent_i:02}' if parent_i else None
        tasks.append(dict(id=tid, source='MASTER-PLAN.md', marker=f'## {tid} {title}',
                          feature_ids=['F01'], surface_ids=[sid], depends_on=[parent_task] if parent_task else []))
        units.append(dict(id=uid, task_id=tid, surface_ids=[sid],
                          mode='NEW_SCREEN' if not parent else 'OVERLAY_PARENT' if kind == 'drawer' else 'ACTION_HIGHLIGHT' if kind == 'action' else 'EDIT_PARENT',
                          parent_unit_id=f'DU{parent_i:02}' if parent_i else None,
                          baseline_ref=f'planned:DU{parent_i:02}@v1; approval pending' if parent_i else None,
                          frozen_regions=['导航', '页面外壳'], allowed_regions=[title + '业务区'],
                          acceptance=[acceptance[sid], '冻结导航和外壳保持一致'],
                          outputs=[f'assets/{uid}-{sid}.png'], source='MASTER-PLAN.md#' + tid))
    method = dict(schema_version=1,
        objects=[dict(id='O01', name='Order', owner='订单服务', source='pages/P01.md'),
                 dict(id='O02', name='ExportJob', owner='导出服务', source='pages/P01.md')],
        features=[dict(id='F01', page_ids=['P01'], object_ids=['O01','O02'], upstream_ids=[], downstream_ids=[], source='FUNCTION-CATALOG.md')],
        menus=[dict(id='M01', label='订单', parent_id=None, page_ids=['P01'], default_page_id='P01', feature_ids=['F01'], object_ids=['O01','O02'])],
        page_details=[dict(page_id='P01', menu_id='M01', actors=['订单分析员'], permissions=['订单读取','订单导出'],
                           feature_ids=['F01'], object_ids=['O01','O02'], core_question='找到哪些订单、要导出哪个范围？',
                           layout_archetype='过滤列表与范围抽屉', source='pages/P01.md')],
        surface_details=[dict(surface_id=s, kind=k, parent_surface_id=p, source='SCREEN-REGISTRY.md') for s,k,p,_ in surface_rows],
        transitions=[dict(id='FLOW01', action_id=actions[0]['id'], kind='local', source='P01-01', success='P01-02', failure='P01-E01', cancel='P01-01',
                          precondition=actions[0]['precondition'], state_change=actions[0]['effect'], recovery='保留列表筛选，刷新权限后重开', permission='订单读取', source_ref='USER-FLOWS.md'),
                     dict(id='FLOW02', action_id=actions[1]['id'], kind='command', source='P01-02', success='P01-R01', failure='P01-E01', cancel='P01-02',
                          precondition=actions[1]['precondition'], state_change=actions[1]['effect'], recovery='保留范围；超时进入 P01-S01 先查询请求状态，核实未创建后才能重试', permission='订单导出', source_ref='USER-FLOWS.md')],
        design_units=units)
    data = dict(version='proof-v1', status='Draft', pages=[page], globals=[], methodology=method)
    coverage = dict(schema_version=1, features=['F01'], surfaces=[s[0] for s in surface_rows], tasks=tasks)
    write('README.md', '# 演示范围\n\n一个订单导出功能，覆盖七个设计单元。所有母版引用是规划，尚未生成或批准。状态核对能力是演示合同，未实现后端。\n')
    write('FUNCTION-CATALOG.md', '# 功能\n\n| ID | 功能 | 业务对象 | 页面 | 上下游 |\n| --- | --- | --- | --- | --- |\n| F01 | 定位订单并导出当前组织的有效范围 | O01/O02 | [P01](pages/P01.md) | 读取订单→创建导出任务→获取结果 |\n')
    write('NAVIGATION.md', '# 导航\n\n订单 M01 → P01；抽屉不是左侧菜单。打开/关闭保留筛选、组织和焦点。\n')
    write('UI-STRUCTURE.md', '# 页面结构\n\n保持导航/外壳。主区先筛选再表格；导出操作在工具栏，范围字段在抽屉。空列表替换表格但保留筛选；错误保留输入；结果含任务标识与下载。宽度由目标视口确定。\n')
    write('pages/P01.md', '# P01 订单与导出\n\n使用者：订单分析员。核心问题：定位订单，确认导出范围。\n\n布局：顶部组织/标题/导出入口，主区筛选和表格，抽屉选择范围。\n\n字段：订单号用于定位，状态用于筛选，金额与更新时间用于核实；导出范围必填且不可跨组织。\n\n权限：读取与导出分开；只读时说明导出禁用原因。\n\n状态：加载保留外壳；空列表提供改筛选；处理中保留范围；失败保留输入；未知结果先对账，关闭抽屉不取消后台任务。\n\n验收：打开/取消不创建任务；重复点击不重复创建；确认成功才展示下载；连接超时不能直接显示回滚或安全重试。\n')
    write('USER-FLOWS.md', '# 流程\n\n```mermaid\nflowchart LR\n List[订单列表] -->|打开导出| Scope[范围抽屉]\n Scope -->|权限与范围校验后提交| Running[处理中]\n Running -->|确认成功| Result[下载结果]\n Running -->|确认失败| Error[保留范围并修复]\n Running -->|超时| Unknown[结果未知，核对请求]\n Unknown -->|确认已创建| Running\n Unknown -->|确认未创建| Scope\n```\n\n取消返回当前列表/范围并恢复焦点；关闭页面不代表取消任务。演示要求幂等请求标识和状态查询，实际接入前验证后端支持。\n')
    write('GLOBAL-SURFACES.md', '# 全局面\n\n本范围复用既有外壳，没有新全局面。\n')
    write('SCREEN-REGISTRY.md', '# Surface Registry\n\n| ID | 类型 | 父面 | 名称 |\n| --- | --- | --- | --- |\n' + ''.join(f'| {s} | {k} | {p or "根面"} | {n} |\n' for s,k,p,n in surface_rows))
    write('MASTER-PLAN.md', '# 独立设计任务\n\n' + '\n'.join(f"{t['marker']}\n\nSurface: {u['surface_ids'][0]}；模式 {u['mode']}；父单元 {u['parent_unit_id']}；母版 {u['baseline_ref']}。\n冻结：导航、页面外壳。允许：{u['allowed_regions'][0]}。\n输入：P01、USER-FLOWS、Registry 与父任务合同。交付：{u['outputs'][0]}。\n验收：{u['acceptance'][0]}。原件尚未生成，母版批准前不执行继承视觉任务。\n" for t,u in zip(tasks,units)))
    write('DESIGN-EXECUTION.md', '# 执行合同\n\n列表母版→导出抽屉→动作/状态。原任务是 MASTER-PLAN；初始页可以准备候选，继承单元必须核实父资产批准、hash 和尺寸。每项只改变自身业务区，不能重画导航。\n')
    write('STATUS.md', '# 状态\n\n规格为演示 Draft；结构验证见 ../results.json。视觉、批准、实现、运行验收均未完成。本目录没有 PNG，仅声明预期输出。\n')
    write_json('registry.json', data)
    write_json('task-coverage.json', coverage)
    errors = validate(package, require_task_coverage=True, require_methodology=True)
    if errors:
        raise RuntimeError(errors)
    generator = SCRIPTS / 'generate_design_maps.py'
    calls=[]
    for mode in ('--write', '--check'):
        cmd=[sys.executable,'-X','utf8',str(generator),str(package),mode,'--format','json']
        run=subprocess.run(cmd,capture_output=True,text=True)
        calls.append(dict(command=cmd, exit_code=run.returncode, stdout=run.stdout, stderr=run.stderr))
        if run.returncode:
            raise RuntimeError(run.stderr)
    faults=[('不存在的菜单默认页', lambda d: d['methodology']['menus'][0].update(default_page_id='MISSING')),
            ('不存在的失败去向', lambda d: d['methodology']['transitions'][1].update(failure='MISSING')),
            ('修改冻结导航', lambda d: d['methodology']['design_units'][1].update(allowed_regions=['导航'])),
            ('继承单元没有母版', lambda d: d['methodology']['design_units'][1].update(baseline_ref=None)),
            ('两个单元覆盖同一产物', lambda d: d['methodology']['design_units'][1].update(outputs=['assets/DU01-P01-01.png']))]
    evidence=[]
    for name, mutate in faults:
        with tempfile.TemporaryDirectory() as temp:
            bad=Path(temp)/'package'
            shutil.copytree(package,bad)
            altered=copy.deepcopy(data)
            mutate(altered)
            (bad/'registry.json').write_text(json.dumps(altered,ensure_ascii=False),encoding='utf-8')
            found=validate(bad,require_task_coverage=True,require_methodology=True)
            evidence.append(dict(case=name,rejected=bool(found),errors=found))
    with tempfile.TemporaryDirectory() as temp:
        bad=Path(temp)/'package'; shutil.copytree(package,bad)
        (bad/'USER-FLOWS.md').write_text('Changed source',encoding='utf-8')
        found=validate(bad,require_task_coverage=True,require_methodology=True)
        evidence.append(dict(case='来源变化但地图未重建',rejected=bool(found),errors=found))
    result=dict(scope='Synthetic order export; specifications and relationships only',
                counts=dict(menus=1,pages=1,surfaces=7,actions=2,independent_tasks=7,design_units=7),
                valid_contract_errors=errors,generation=calls,faults=evidence,
                artifacts_rendered=0,approved_assets=0,production_runtime_verified=False)
    (root/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if all(e['rejected'] for e in evidence) else 1


if __name__ == '__main__':
    raise SystemExit(main())
