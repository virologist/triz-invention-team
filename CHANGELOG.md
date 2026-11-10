# Changelog

All notable changes to the **TRIZ Invention Team** will be documented here. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.13.0] - 2026-11-11

> **CYCLE-1 · 第 8 轮（宿主缺陷复核轮）**。
> 上一轮（2.12.0）清偿了版本漂移与退出码假绿。本轮把 **S-E76 的修复真正落到
> 真实宿主**（`~/.workbuddy/bin/release-sync.sh`），并在落地过程中实测暴露
> **修复器自身 4 个缺陷**——其中一个是判据假绿：修复块在位就判通过，
> 即使代码已被人工回滚。全部当场清偿。

### P0
- **S-E76 宿主 `release-sync.sh` 推送失败检测整段失效（假绿）**：
  宿主 shebang 为 **zsh**，却用 **bash 数组**语法 `PUSH_RC=${PIPESTATUS[0]}`；
  宿主顶部 `set -euo pipefail` → `${PIPESTATUS[0]}` 触发
  「parameter not set」→ 脚本在**判断推送结果之前**就中止。
  后果：git push 明确失败（如 OAuth App 缺 workflow scope）时，
  「推送失败检测」整段永不执行，脚本仍以退出码 0 收场，
  台账会记「已推送」而实际没推上去——**比缺功能更危险**。
  修复：`if 管道; then RC=0; else RC=$?; fi`——在 if **内部**捕获退出码，
  不依赖任何 shell 特有数组，zsh / bash 通用（配合宿主 `set -o pipefail`）。
  实测关键事实：zsh 下换成 `${pipestatus[1]}` 在 if 之后仍取到 0
  （zsh 的 pipestatus 在 if 条件求值后被重置），**只换变量名修不好**。
  修复以**第二类 marker 块**（`triz-hostfix`）版本化进 `install_gate_hooks.py`，
  与门禁块 marker 区分（两类块并存不再互相误判 drifted），换机/新 clone 可复现。
  真实宿主已安装并复验：`hostfix:release-sync installed`（兼容写法 2 处），
  `zsh -n` / `bash -n` 双语法通过；新旧写法对照实测——
  旧写法 `parameter not set` 立即中止，新写法正确取到 `PUSH_RC=1` 并报失败。

### P1
- **S-E77 修复器自身 4 个缺陷（本轮实测暴露并当场清偿）**：
  ① **判据假绿**：`check_hostfix_one` 只看 marker 块在不在就判 installed，
     不校验代码是否被回滚 → 人工把代码改回 `${PIPESTATUS[0]}` 仍判通过。
     新增 `regressed` 状态：块在位但代码回归 → 判失败（verify 整体失败）。
  ② **幂等粒度过粗**：`_rewrite_push_rc` 开头「文件含 `_triz_push_rc=` 就早退」
     → 真实宿主有**两处**推送结构，只回滚其中一处时，另一处已修好的会
     挡住这处的修复 → re-install 无法自愈。现把幂等下沉到**正则层**
     （逐结构判定），局部回滚可自愈。
  ③ **锚点自毁**：注入锚点依赖注释文本，而同一轮又要改写那段注释
     → 锚点自毁、且与措辞强耦合（换个人改写措辞就找不到 → 静默跳过）。
     现改为**结构性定位**（回溯到脆弱赋值所属的管道 if，与措辞解耦）。
  ④ **过时注释误导**：改写后宿主原注释仍写着「用 PIPESTATUS[0] 取退出码」
     → 成为**过时且误导**的文档（注释错比代码错更隐蔽）。改写时同步替换。
- **S-E78 版本门禁盲区**：v2.13.0 bump 时实测发现
  `.claude-plugin/marketplace.json` 的 `metadata.description` 里
  **硬编码 `(v2.11.2)`**——4 个 version 字段全对，描述文字里落后两轮。
  说明「版本号」不止存在于 version 字段。现把描述内嵌版本号纳入
  `version_consistency.py`（**4 位 → 5 位**），并补对应变异自测用例。

### 验证（全量闭环）
- `self_gate.py` **17/17 通过** · `self_gate.py --self-test` 全通过
  （15 门禁清单 + 2 基线 + 2 项元判别力 + 宿主接入自检）
- 清单双向差集 **13/13 为空**（无漏挂、无幽灵执行点）
- `install_gate_hooks.py --self-test` **13 项全通过**
  （新增：回归检出 · 回归后自愈 · 多处脆弱写法全改 · 过时注释清理）
- `version_consistency.py --self-test` **5 项全通过**（新增：描述内嵌版本号漂移）
- `harness.py --self-test` **8 项** · `boundary_guard.py --self-test` 22 用例
- `contract_enforce.py --self-test` 变异测试通过（真实判定短路后探针失去判别力）
- 三用例回归**零回退**：a01 **7/7** · b01 **7/8 + 1 INFO** · c01 **8/8**
- `preflight_check.py` RC=0 · `install_gate_hooks.py --verify` → `hostfix:release-sync installed`
- 真实宿主双语法检查：`zsh -n` ✅ / `bash -n` ✅
- 版本一致性：**5 个版本位全部 2.13.0**

### 尚未验证（明确不宣称）
- 真实 git push 失败场景的**端到端**验证尚未在本轮执行（仅以等价的
  zsh 管道失败片段完成对照实测）；下次实际推送前仍需观察宿主脚本的真实行为。

## [2.12.0] - 2026-11-11

> **CYCLE-1 · 第 7 轮（工作系统改造后的复核轮）**。
> 上一轮（2026-11-10）把专家团从「散文操作说明」升级为「结构化工作地图 + 统一入口
> `harness.py` + 反馈闭环」。本轮**不重构，只复核**：全量回归零回退的前提下，
> 用实测找出并清偿 3 项真实缺陷——其中 2 项属「假绿」类，会让不完美的产出冒充通过。

### P0
- **S-E73 版本号三处漂移且无任何门禁拦截**：实测发现 `.codebuddy-plugin/marketplace.json`
  的 version 停在 **2.10.0**，而 `.codebuddy-plugin/plugin.json` 与
  `.claude-plugin/marketplace.json` 已是 **2.11.2**——**已连续漂移两轮**。
  根因有二：① 历次 bump 提交（如 `1b41fe1`）只改 `.claude-plugin/marketplace.json` 两处
  + `plugin.json` 一处，**漏掉 `.codebuddy-plugin/marketplace.json`**；
  ② `preflight_check.py` 与 `self_gate.py` **均无版本一致性判据**，漏改不会被拦下。
  新增 **`scripts/version_consistency.py`**：校验 **4 个版本位**（WorkBuddy 插件清单 ·
  WorkBuddy 市场清单插件项 · Claude 市场清单 metadata · Claude 市场清单插件项）必须相等，
  缺字段/文件缺失一律 fail loud（RC=1，禁止发布）；带 `--self-test` 判别力自测
  （单点改小→检出漂移 · 缺字段→报缺字段 · 文件缺失→报缺失）。
  已挂进 `self_gate.py` 的 `GATES`（清单 15→**16 项**，汇总 16→**17 项**），
  并补入 `docs/OPERATIONS.md` 工具表（双向差集实测 13/13 为空，无幽灵）。
- **S-E74 认可样例存在退出码假绿**：`harness.py verify --sample` 在样例含
  `UNVERIFIED:` 断言时**仍返回 RC=0**，与本包自身「退出码 3 = 无 FAIL 但存在
  UNVERIFIED，禁止宣称验证通过」的契约直接冲突——即真实运行产出未落盘时，
  工具却对外报「通过」。已修为：含未验证项 → **RC=3**；有 FAIL → RC=1；
  全通过 → RC=0。与 `verify --run-dir` 语义统一。补 2 条自测用例锁死
  （样例含 UNVERIFIED→RC=3 / 全命中→RC=0），变异测试 **2/2 零逃逸**。

### P1
- **S-E75 样例输出标签重复**：未验证项输出为 `UNVERIFIED UNVERIFIED: ...`
  （正文已含 `UNVERIFIED:` 前缀又叠加状态标签），改为剥离前缀后输出。
- **self_gate 自测汇总的基线数改为动态**（取自 `BASELINE_SUBDIRS` 唯一真源），
  根治「增删基线目录即漂移」的手抄数字隐患（S-E72 同型）。
- `docs/WORK_MAP.md` §四 补**退出码契约表**（0/1/2/3 与「能否宣称验证通过」），
  `docs/DELIVERY_WORK_SYSTEM.md` §四/§六 同步新退出码语义与自测项数。

### 验证（全量闭环）
- `self_gate` **17/17**（清单 16 项 + 2 基线 + 2 项元判别力 + 宿主接入）·
  `self_gate --self-test` 全通过（双向差集 13/13 为空）
- `harness.py --self-test` **8 项**全通过（新增 2 条样例退出码判别力）
- `version_consistency.py --self-test` 全通过 · **变异 2/2 零逃逸**（临时副本）
- 三用例回归 a 7/7 · b 7/8+1INFO · c 8/8 全 RC=0（零回退）
- benchmark L1 **1.000** · preflight RC=0 · CI 门禁 100% 合规 · 契约 RC=0
- 版本号 4 个版本位一致（2.12.0）

### 尚未验证（如实标注，不得当作通过）
- 2026-11-10 真实运行的产出与 `state.json` 本机仍未检索到 → 认可样例第 5 条
  恒为 `UNVERIFIED`（`verify --sample` 因此返回 RC=3，**这是正确行为**）；
  G1-G5 真值检查在基线目录上同样为 `UNVERIFIED`。
- 未发起新的真实端到端业务任务，本轮全部验证基于既有基线 + 真实运行记录回归。

## [2.11.2] - 2026-11-10

> **CYCLE-1 · 第 6 轮（终局复核发现真实遗留 → 修复 → 收敛）**。
> 起始动作是「独立终态核验，不采信历史结论」——上轮结论「无遗留」被
> 实测推翻：第 5 轮的宿主门禁改动**不在仓库内**，换机即失效。新增 **3 项**
> S-E70…S-E72 全部清偿。

### P0
- **S-E70 宿主门禁改动未版本化（换机即失效）**：第 5 轮 S-E62 把 `self_gate.py`
  挂进 `~/.workbuddy/git-hooks/pre-commit` 与 `~/.workbuddy/bin/release-sync.sh`，
  但这两个文件**不在本仓库**。实测干净 `git clone . /tmp/fresh-clone` 后
  `grep -rln "git-hooks/pre-commit|release-sync"` 零命中，仓库内既无安装器、
  无快照、也无安装指引 → 换机/重装/新同事 clone 后门禁链退回 3 gate，
  `boundary_guard` 与 9 个判别力自测重新变成幽灵执行点。
  新增 **`scripts/install_gate_hooks.py`**：宿主接入代码块作为唯一真源内置
  （marker 包裹，可检测手改漂移）；`--verify` 只读检查 / `--install` 幂等注入
  （自动备份、不破坏宿主其余内容、注入前校验锚点，找不到锚点 fail loud）/
  `--self-test` 在临时目录模拟新机器；`--host-root` 可参数化。
  端到端实测：干净工作树拷贝 → 自检 RC=1 → 安装器接入 → 自检 RC=0，
  宿主 `bash -n` 语法完好；真实宿主已从 legacy 手写块迁移为可校验 marker 块。
- **S-E71 `self_gate --self-test` 对此假绿**：干净 clone 里报「✅ 自测全通过」，
  但它只校验仓库内清单，从不检查「自己是否会被调用」——与 S-E62 同型。
  现消费 `install_gate_hooks.verify_host()` **同一判据**，未接入/漂移即自测失败；
  CI 环境可设 `TRIZ_GATE_SKIP_HOST_CHECK=1` 显式跳过（打印留痕，不静默）。
  另加 `TRIZ_GATE_BASELINE_ROOT` 参数化，让「基线目录缺失」分支有可触发的
  判别力场景（变异 S4 靶点）。

### P1
- **S-E72 文档缺首次部署步骤**：`docs/OPERATIONS.md` 补「换机/新 clone 后
  首次部署（必做）」三条命令 + 宿主不在仓库内的风险说明 + CI 跳过开关；
  工具表补 `install_gate_hooks.py`；顺手**删掉上轮又写死的「14 项」**
  （新增安装器后实际 15 项）——根治文档手抄数字。

### 验证（全量闭环）
- `self_gate` **15/15** + `--self-test`（13 门禁清单 + 2 基线 +
  2 项元判别力 + 宿主接入）；双向差集为空；工具表 22/22 零遗漏零幽灵
- 三用例回归零回退 · preflight RC=0 · CI 门禁 · 契约全员 · 18 JSON
  · 22 脚本 `--help` 零异常 · 台账 verify · 宿主 release-sync **4/4 gate**
- **变异 10/10 零逃逸**（临时副本上跑，工作树零风险；4 种环境：
  宿主已接入 / 未接入 / CI 跳过 / 基线缺失；含 canary 触发漏挂场景）
- 调试中修正 3 个自测自身缺陷：双重缩进导致漂移误判、锚点缺失时拒绝
  安装（补 fallback 锚点）、变异脚本直接改工作树导致 SIGTERM 污染源码
  （改为全程临时副本）——方法论已沉淀

### 宿主环境改动（不在本仓库）
`~/.workbuddy/git-hooks/pre-commit`、`~/.workbuddy/bin/release-sync.sh`
—— 已由安装器归一为可校验 marker 形态；备份 `.triz-gate.bak` 保留。

## [2.11.1] - 2026-11-09

> **CYCLE-1 · 第 5 轮（全面排查 → 诊断 → 修复 → 测试 → 再诊断 → 收敛）**。
> 历史结论一律作废，全部从代码与实测重新取证。新增 **8 项** S-E62…S-E69，
> 其中 **3 项 P0**（幽灵执行点 / fail-open / 自测假绿）、**4 项 P1/P2**、
> **1 项 C4 再诊断新增**。两路子智能体审计超时失效，改由主线程独立取证。

### P0（假放行 / 假绿）
- **S-E62 判别力门禁无机械执行点**：全仓 grep 显示 `boundary_guard.py` 仅命中
  文档与脚本自身；`~/.workbuddy/git-hooks/pre-commit` 四层门禁、
  `~/.workbuddy/bin/release-sync.sh` 三 gate **均未调用**，
  且 10 个带 `--self-test` 的脚本只有 `agent_ci_gate` 被覆盖
  → `OPERATIONS.md`「每次 VERIFY 收产出前」是幽灵条款（形态 A）。
  新增 **`scripts/self_gate.py` 门禁汇总唯一入口**（12 脚本自测 +
  2 真实基线越界复核 = 14 项），pre-commit 与 release-sync 条件式接入
  （仅自带该文件的包生效，其余 5 包零影响）。
  端到端实测：short-circuit `c3_should_trigger` → 门禁 1/4 未通过 → 禁止推送。
- **S-E63 `boundary_guard` 空集 / 不可判定 fail-open**：实测目录有产出但
  文件名不匹配 `T-*__*.md` → 打印警告后 **RC=0**；产出全为 `unknown_role`
  → 打印「不可判定 1 份」后 **RC=0**，与脚本自身第 18 行「无法判定 ≠ 放过」
  直接矛盾。新增 `judge_exit_code()` 唯一真源、默认 fail-closed
  （空集/不可判定 → RC=2；越界 → 1；全 clean → 0），
  `--allow-undetermined` 为显式人工确认逃生阀（打印留痕）。
  顺带消除逻辑双份（`main()` 的「越界→return 1」第二份判定移除）。
- **S-E64 `evolution_log.py self-test` 恒 RC=1 + 探针假绿**：四个探针共用
  固定时间戳 `2026-11-09T00:00:00`，台账末行 `14:06:52` → 全部触发「时间倒序」：
  合规样本被误判为违规，另三个违规探针**全靠时间倒序被检出**、
  没测到各自声称的判据。更深层根因：`probe()` 复刻了一份判定逻辑、
  从未调用真实 `cmd_verify`（形态 C 自指模拟）。
  抽出 `validate_rows()` 唯一真源，探针改纯内存构造 + 动态时间戳 +
  逐条校验**特定判据关键词**；补 7 类判据探针。变异 8/8 全捕获
  （含原缺陷回归靶点 V8）。

### P1 / P2
- **S-E65 `threat_grade.scan_member_grades` unreadable 被 determined 覆盖**：
  实测 1 份不可读 + 1 份正常 → `verdict=determined`，损坏产出被静默吞掉。
  改严重度优先（unreadable 锁死不可覆盖）+ 落 `detail["unreadable_files"]`。
- **S-E66 `OPERATIONS.md:68-74` 四个幽灵 self-test 条目**：
  `diagnosis_trigger` / `evolution_log` / `verify_triz_data` /
  `query_triz_matrix` 实测全部 `RC=2 unrecognized arguments: --self-test`。
- **S-E68 文档数字漂移（根治）**：文档写 `boundary_guard 20 用例`（实 22）、
  `patent_knowledge 17 断言`（实 25 ✅ 行）。根因是文档手抄用例数 = 第二份真源。
  **彻底删除手抄数字**，只指向 `self_gate.py:GATES`；工具表补 `self_gate.py`
  （21/21 覆盖，零遗漏零幽灵）。
- **S-E69（C4 再诊断新增）`self_gate` 清单单向校验**：注入一个带
  `--self-test` 的 canary 脚本后自测仍 RC=0、输出不提 canary → 漏挂不会被发现。
  与 S-E54 同型，解法同为**双向差集**：新增 `discover_selftest_scripts()`
  机械发现全仓自测脚本，漏挂/陈旧任一非空即 FAIL；顺带修掉子命令形态
  条目跳过参数校验的缺口（`verify_triz_data --strict` 列为显式例外）。

### 验证（全量闭环，全部实测）
- `self_gate.py` **14/14** + `--self-test` 双向差集为空
- 三用例回归零回退：a-01 7/7 · b-01 7/8+1INFO · c-01 8/8；benchmark RC=0
- preflight RC=0（C3 X=5 正确触发）· CI 门禁 · 契约全员 · 18 JSON
  · 21 脚本 `--help` 零异常
- **全套变异 32/32 零逃逸**（evolution_log 8 + boundary_guard fail-closed 8
  + threat_grade/boundary_guard 关键真源 16）
- 宿主门禁链：pre-commit 与 release-sync 均升为 **4 gate**（第 4 项=self_gate）

### 宿主环境改动（不在本仓库）
`~/.workbuddy/git-hooks/pre-commit`、`~/.workbuddy/bin/release-sync.sh`
—— 条件式接入 `self_gate.py`，仅对自带该文件的包生效。

## [2.11.0] - 2026-11-09

> **CYCLE-1 · 第 4 轮（AI agent 开发/测试工程师视角全面排查 + 修复与 debug）**。
> 新增 **9 项** S-E53…S-E61，全部清偿。核心成果：X/E 级威胁判定**唯一真源化**、
> 越界红线**验收侧机械拦截**、全部关键脚本补**判别力自测**（变异测试靶点）。

### Added（新工具）
- **S-E59 `scripts/boundary_guard.py` 成员产出越界红线机械拦截**：S-E11 只把
  `forbidden_boundary` 下沉到下发侧（task_payload schema），验收侧零机械校验。
  现 5 信号（B1 申请文件正文 / B2 肯定性授权断言 / B3 自我评价 / B4 越权改写方案 /
  B5 非职责角色出具三性评级）按 `docs/architecture.md` §二 角色矩阵判定；
  判据基于产出结构而非成员自述；verdict 四态（clean/violation/unknown_role/unreadable，
  **不可判定 ≠ 放过**）；引用语境按句级豁免（B5）、断言句式不豁免（B2）。
  自测 20 用例 + 7 成员角色矩阵；**变异测试 19/19 全捕获**
- **S-E53 `scripts/threat_grade.py` X/E 级威胁判定唯一真源**：此前 preflight 宽松正则
  `X\s*[\W_]*\s*(\d+)` 对 7 个真实场景误判 4 例（最严重「本产出无 X 级威胁」被判 1 条 →
  假触发 C3 阻断），且与 patent_knowledge 构成契约双源漂移。现只认结构载体
  （JSON `xyape_grades` 数组+字符串两形态 / Markdown 分级表节）+ 专利号正则 +
  否定值过滤 + 跨载体按专利号去重（同批文献 JSON+表格双载体 → 10 实为 5）

### Fixed（缺陷清偿 · S-E54…S-E61）
- **S-E54/S-E55 task_id pattern 第三份手抄清偿**：`token_budget_check.FILENAME_RE`
  为全仓**第三份**手抄（schema 改了不跟随 → 静默漂移）；现改为从
  `result_envelope.schema.json` 读 pattern **派生**，读不到 schema 直接抛错（fail loud）；
  `agent-protocol/SKILL.md` 文档真源同步（旧 pattern 漏 A01 形态 `T-20261015-A01`）；
  preflight 第 15 项扩为**五处判据**（pattern 一致 + 基线样本全匹配 + 消费方清单 +
  SKILL.md 同步 + 全仓零手抄）。变异 P1/P2/N1/N2 全捕获
- **S-E56 benchmark 退出码语义化**：此前恒 `return 0`（有 FAIL 也绿）→
  现语义化 `0`=全过 / `1`=有 FAIL（gate 未通过）/ `2`=用法或环境错误；
  变异 Q1（退回恒 0）首轮未被捕获 → 补「实跑 main() 读真实退出码」用例后捕获
- **S-E57 benchmark `split` 死参数清偿**：定义后从未被读取，任何 split 返回同一任务
  列表 → A-Evolve 按 split 划分训练/评测集会**数据泄漏**；现校验 `train|holdout`
  二值，holdout 只保留 L2 用例；用例基线分离（b-01 用 l1 目录，不再共用 l2 求值目录，
  L1 综合分 0.750 → 1.000）
- **S-E58a 回归报告可移植 + 求值不污染**：run_dir 原样写入报告（换机不可复现）→
  包内路径改相对；`--no-report-write` 开关让求值不写基线目录（工作树干净）
- **S-E58b 6 脚本补 `--self-test` 判别力自测**：check_claim_scope(13)/cost_profile(18)/
  failure_memory(18)/patent_knowledge(17)/spawn_watchdog(15)/triz_benchmark(19)。
  自测过程暴露并修复真缺陷：**cost_profile P90 非标准 nearest-rank**
  （`round(p/100×(n+1))-1` 系统性高估一位 → 改 `math.ceil(p/100×n)-1`）；
  spawn_watchdog 抽 `_judge()` 纯函数消除判定逻辑双份。变异 R1-R5 全捕获
- **S-E60 threat_grade 多轮产出聚合（假放行防线）**：查新是多轮迭代（首轮带完整
  分级载体，复检轮只引用首轮结论），原 `latest_scout_output` 只取最新一份 →
  复检轮存在时首轮 X 级**完全不被计数** → C3 不触发 → **假放行**。假放行比假阻断
  危险（阻断是流程摩擦，放行是带着 X 级威胁进撰写）。现 `scan_member_grades()`
  聚合全部产出 + 跨文件专利号去重；preflight 第 8 项改消费聚合结果
  （实测基线 A01 X=5 正确触发 C3）
- **S-E61 专利号形态全覆盖（漏计防线）**：原 `PAT_NO_RE` 只支持字母尾码 →
  申请号形态 `CN202311321256.8`（中国发明专利申请号标准形态：12 位数字 + 小数点
  校验码）全漏计（真实基线实测 13 处）。新正则
  `(CN|US|EP|WO|JP|KR)[0-9]{7,14}(?:\.[0-9]|[A-Z][0-9]?)`——尾码与校验码
  **二者必居其一**，纯数字号段不计（非任何法域标准形态）；
  patent_knowledge 同步显式化消费方过滤义务（申请号不入族谱库——真源管「怎么解析」，
  本模块管「收什么」，与 S-E59 等级过滤同型）
- **S-E59 收尾审计中的判别力补强**：「引用上游评级不算越界」用例原为**假绿**
  （文本形态不匹配 `_VERDICT_QUOTE_RE`，从未经过引用排除分支——变异 M2 逃逸暴露）；
  `_sentence_of` 只取匹配点前 60 字符（后置引用线索「（详见 A01）」看不到）→
  改为句级上下文；`_SPEC_SEC_RE` 与 `_CLAIM_HEAD_RE` 分支重叠 → 互斥拆分

### Changed（文档）
- `docs/OPERATIONS.md`：工具清单补 `threat_grade` / `boundary_guard` 两行 + 带
  `--self-test` 脚本索引；preflight 第 15 项描述「三处一致」→「五处一致」
- `docs/CONTRACT_ENFORCEMENT.md`：维护节补 S-E59 / S-E53/S-E60/S-E61 机械拦截说明

## [Unreleased]

> 本段内容为 **2026-11-08 工作区整理 + 残留全清偿**（11 个 commit：8285208…b43d2de），
> 时间早于 `[2.9.0]`（2026-11-09），但当时未单独 bump 版本号，故滞留于 Unreleased。
> 版本号待下次统一 bump 时归并（S-E41：原标题带日期 `2026-11-08`，与下方 2026-11-09
> 形成日期倒序，已按 Keep a Changelog 规范改为不带日期的 `[Unreleased]`）。

### Changed（工作区整理）
- **基线资产归位**：包根游离 `darwin-results.tsv` 按 CHANGELOG 2.2.0 声明补迁移至 `docs/evolution-log.tsv`（该声明当时未实际执行，README.zh.md 引用悬空至今）
- **回归基线归档**：`outputs/regression-*` → `tests/baselines/{l2-full-a01, l1-analyst-b01, 20261014-p0-2, _pre-fix-b01}` + spawn 文案打包 `_archive/`；新增 baselines/README 导航；outputs/ 目录整体移除
- **10 个活跃引用点同步**（contract_enforce 自测2 / check_claim_scope --l2 / 5 脚本示例 / 3 文档）；工具清单 13 项
- OPERATIONS §一 settings.json 判据记载订正（5.9.3 缓存版仍带判据=误报，以 register 成功为准）

### Fixed（残留清偿 8 项）
- **C01 A6 法25 断言根因修复（d4bee57）**：member_files() 对同名成员多轮产出只留最后文件（A03 复检覆盖 A01 首轮）曾致永久误判——check_required_regex 新增 `any_member` 模式，C01 首次 8/8 全 PASS
- **U3 outdated 子命令（b0dddf9）**：失效标注/query ⚫显示/stats 计数，兑现 scout MD「失效反馈机制」承诺
- **D3-1 仲裁链订正 + D1 坍缩表（50d51ed）**：confidence 降为末位参考信号（不得单独裁定）；7 视角补 17 个 TRIZ 参数映射（权威 CSV 校验零越界）
- **spawn_watchdog 简版（e47a525 + b43d2de 补齐）**：四态判定（OK/WATCH/STALL/TIMEOUT）+ H4 处置建议，P2-15 债务关闭
- routing-log 单表化 + R-004 缺号登记；diagnosis-protocol 报告存放位置澄清；benchmark/cost_profile 示例改精确子目录

### Evaluated（评估后不实施）
- D4-2 himmpat 登录态探测：运行时状态不可预判，scout L2→L3 降档规则已覆盖——不实施
- 48h 回检窗口关闭：窗口内多轮门禁复跑全绿，唯一新发现（benchmark 传参混扫）非修复引入

## [2.10.0] - 2026-11-09

> **CYCLE-1 · 第 3 轮（全面排查 + 契约漂移根因整治）**——用户授权推送 GitHub 后的全量复检。
> 排查范围：死代码 / 契约漂移 / 幽灵验证项 / 幽灵契约 / 安装路径 / 版本口径。
> 新增 **8 项** S-E44…S-E52，preflight 检查项 **13 → 15**。

### Fixed（缺陷清偿 · S-E44…S-E47）
- **S-E44 [P1] `agent_ci_gate` schema 路径二次手抄**：`ENVELOPE_SCHEMA_PATH` / `PAYLOAD_SCHEMA_PATH`
  定义后从未被引用，`main()` 在下方**重新手拼**一遍同名路径 → 同一路径两处定义，改一处必漂移另一处。
  现改为唯一真源常量，`main()` 直接消费；`run_regression.load_task_id_pattern()` 的
  **全仓第三处手抄**同步改为消费 `agent_ci_gate.ENVELOPE_SCHEMA_PATH`（与本脚本既有的
  `import state_store as SS` 复用先例一致）。判别力实测：把常量指向坏路径 → 落到保底字面量 → 还原恢复。
- **S-E45 [P1] `patent_knowledge.GRADE_SEC_RE` 死常量**：常量定义后从未被引用，而
  `parse_scout_output()` 另写了一条功能等价的正则 → 两条正则可各自漂移（如一条支持
  「### 4.1 X 类」编号在前、另一条不支持），导致「常量看起来是规范、正则却各写各的」。
  现把**切分实现下沉到常量**，解析处直接消费。等价性实测 6/6 用例新旧行为完全一致。
- **S-E46 [P2] 死变量清理**：`skill_test_runner.RESULTS`（统计实际走返回值累加）·
  `state_store.PKG`（与其它脚本同名但语义不同，保留会误用）→ 均移除。
- **S-E47 [P1] Claude Code 单仓安装路径失效（推送阻塞项）**：`.gitignore` 整目录排除
  `.claude-plugin/` → GitHub 上**完全没有** Claude marketplace 定义 → `/plugin marketplace add`
  根本读不到插件清单（官方要求 marketplace 定义必须在 `<市场根>/.claude-plugin/marketplace.json`
  且**必须提交到 git**）；同时双 `marketplace.json` 的 `source` 指向**不存在**的
  `./plugins/triz-invention-team`（本仓 git 根为平铺布局，无 `plugins/` 嵌套层）。
  - 修复：`.gitignore` 改为 `.claude-plugin/*` + `!.claude-plugin/marketplace.json`（排除内容但强制保留清单）；
    双 `marketplace.json` 的 `source` 改为 `"./"`（根目录插件写法，相对**市场根**而非 `.claude-plugin/`）。
  - 依据三重权威证据：① Claude Code 官方文档 ② 本地 6 个已工作的同类单仓 marketplace
    （`agricidaniel-claude-obsidian` / `claude-scholar` / `science-superpowers-dev` /
    `anthropic-agent-skills` 等，**全部**用 `source: "./"` 且 `.claude-plugin/` 全部入库）
    ③ `git clone` 远端端到端实测确认远端确实缺 `.claude-plugin/`。
  - 连带修 `README.zh.md` 结构图（preflight 第 11 项**正确阻断**了「结构图缺 `.claude-plugin`」）+ 注 1 说明订正。
  - 不影响宿主：宿主实际生效的市场索引在 `my-experts/.codebuddy-plugin/marketplace.json`
    （独立文件，`source: "./plugins/triz-invention-team"`，已是自动生成）→ 本仓
    `.codebuddy-plugin/marketplace.json` 是插件包内元数据（单仓自描述），两者语义各自正确、互不冲突。

### Added（新增机械能力 · S-E48/S-E49）
- **S-E48 [P1] `preflight_check.py` 第 14 项 · routing-log 列契约一致性机械校验（根因整治）**：
  落盘表在**三处手抄**（头部「字段：」声明 / Markdown 表头 / 实际数据行）且无机械校验。
  **实测事故**：表头只声明 7 列，而 R-20261108-001（**已入库于 7b6ffb8**）与 R-20261108-002
  两行均含 `rationale_class` 尾列共 8 列 → Markdown 渲染时该列**溢出表头**，
  读者按表头解读会误判第 6 列「结果」实为「理由」→ **本表唯一可复盘字段失效**。
  现落地第 14 项：表头列数 == 全部数据行列数 == 头部「字段：」声明字段数，三者逐位对齐，
  否则 BLOCK。历史 25 条旧 7 列行按 append-only 原则**只补不改**（末列填
  `—（旧格式无此字段）`），分隔行同步补列。
  - 变异测试（判别力验证）：删数据行一列 → BLOCK；表头删一列 → BLOCK；
    头部声明与表头逐位错位 → BLOCK；还原 → PASS。
  - 口径澄清：SOP `RoutingDecision` JSON 有 8 字段，但 SOP「强制落盘规则」只要求
    「decision_id + target + confidence + 简述」→ 落盘表是**精简投影**，
    故对齐真源是**头部「字段：」行**，不是 SOP JSON 全字段。
- **S-E49 [P1] `preflight_check.py` 第 15 项 · task_id 契约三处一致性 + 反幽灵契约（根因整治）**：
  `task_id` 格式在**三处手抄**（信封 schema / 任务包 schema / 文档示例）且无机械校验。
  **实测事故**：信封 schema = `^T-[0-9]{8}-[A-Za-z0-9]{1,8}$`（允许字母后缀），
  任务包 schema = `^T-[0-9]{8}-[0-9]{3,}$`（**只允许纯数字**），文档示例写 `T-YYYYMMDD-NNN`
  （纯数字口径）；而**实测基线全部采用字母后缀**（`T-20261015-A01`…`A07`，7 份成员信封 +
  9 份 spawn 文档）→ 主理人按实测形态派单时，**若下游按任务包 schema 校验必被拒**；
  而任务包 schema **全仓零代码消费**（幽灵契约）→ 该冲突从未被任何门禁暴露。
  - 修复：任务包 schema 的 `task_id.pattern` 与信封 schema **字面统一**；主理人 MD 与
    `docs/architecture.md` 补「task_id 格式（NNN|字母数字后缀）」说明。
  - 反幽灵契约：`agent_ci_gate` 新增 `_load_schema()` 单一真源载入器，并新增
    **task_payload schema 自测**（合规 payload `T-20261015-A01` 通过 / 缺 `instruction` 检出）。
  - 变异测试：改回纯数字 → BLOCK（preflight + ci_gate 自测**双重检出**）；
    任务包 schema 零消费 → BLOCK；还原 → PASS。
  - **判别力自查修正**：判据 3「至少被一处代码消费」最初把 `preflight_check.py` **自身**也算作
    消费方 → 本脚本「自己给自己作证」（假绿）。已改为**排除自身**，只认其它脚本的真实消费。

### Fixed（续 · S-E50…S-E52）
- **S-E50 [P2] `state_store.HERE` 死变量**：定义后从未被引用 → 移除（与 S-E46 的 `PKG` 同批清理）。
- **S-E51 [P2] `run_regression` 保底字面量是 schema pattern 的第二份真源**：
  `load_task_id_pattern()` 读不到 schema 时**静默回退**到字面量
  `^T-[0-9]{8}-[A-Za-z0-9]{1,8}$` → schema 改了不跟随，契约漂移**静默**发生
  （当前恰好相同，纯属巧合）。现改为读不到即**抛错**（fail loud，不静默降级）。
  实测：常量指向坏路径 → `FileNotFoundError`（不再静默返回字面量）。
- **S-E52 [P1] `--scaffold` 全线崩溃（层级误读 · 预先存在）**：`cmd_scaffold` 写 `exp["expect"]`，
  但 `expect` 是**断言层**字段（每条 assertion 自带 expect），顶层无此键 →
  用例 A（`target_member=full-team`）必然 `KeyError: 'expect'`。
  **用 HEAD 版本复现，确认非本轮引入**。真实成员清单位于断言 `all_members_landed`（A2）的 expect。
  现按断言层读取；无成员清单时显式报错，不静默产出空成员 state。
  实测：`--case workflow-a-01 --scaffold` → 正常产出 `RUN_INFO.md` + `state.json`
  （`retry_counts` 含 6 成员）。

### Changed（口径同步）
- **版本收口 2.9.0 → 2.10.0**：三处版本号统一（`plugin.json` / 双 `marketplace.json`）+
  `README.zh.md` 三处（标题/导语/落款）+ `docs/OPERATIONS.md` 工具清单版本号。
- **preflight 项数 13 → 15**：`docs/OPERATIONS.md` 工具清单行同步（补第 14/15 项）；
  `preflight_check.py` docstring 检查项清单同步。
- **`docs/routing-log.md` 列契约订正**：表头补 `rationale_class` 列 + 头部「字段：」声明同步为
  8 字段 + 历史 25 行补列 + 分隔行补列。

### 验收证据（机械实测）
- **9 项门禁全绿**：`verify_triz_data --strict` · `agent_ci_gate --strict` · `agent_ci_gate --self-test` ·
  `contract_enforce --self-test` · `state_store self-test` · `preflight_check` ·
  `skill_test_runner` · `evolution_log verify` · `token_budget_check`（全部 rc=0）
- **三用例回归零回退**：A 7/7 PASS · B 7/8 PASS + 1 INFO · C 8/8 PASS
- **18 脚本 `--help` 零异常** · **全仓 JSON 零非法**
- **变异测试 7 例全过**：第 14 项（A 删数据行列 / B 删表头列 / C 头部逐位错位）·
  第 15 项（D 改 pattern / F schema 缺失 / G 零消费）+ S-E51（schema 路径坏 → fail loud）
- **端到端安装实测**：`git clone` 远端 → 确认 `.claude-plugin/marketplace.json` 已入库

## [2.9.0] - 2026-11-09

> **CYCLE-1 · 可持续迭代引擎（墨衡）**——针对本专家团的独立诊断 → 构建 → 测试&debug → 再诊断循环。
> 共 7 个批次 commit（3812043 → P1-4），19 项 S-E01…S-E19 首诊短板 + 第2轮交叉验证 19 条确证问题全部清偿。

### Added（新增机械能力）
- **`preflight_check.py` 第 12 项 · Workflow D 入口前置闸机械校验（S-E02）**：主理人 MD:359 曾声称
  「由 preflight 第9项机械校验」，实测 preflight 全文不含 G1/G2/G3/search_3rounds/trinity 任一字符串——
  该校验**从未存在**（幽灵验证项）。现落地真实实现：真源 = `state_store.GATE_ALIASES`，
  G1/G2/G3 全关 ∧ `state.evidence` 的查新/裁决落盘文件真实存在才放行，否则 BLOCK。新增 `--state-path` 参数。
- **`contract_enforce.py` 自测4 · DRIFT_PROBE 三源漂移反向验证（S-E21）**：CONTRACT_ENFORCEMENT.md:116
  曾声称「注入 DRIFT_PROBE → exit 1」，实测全仓仅该文档行命中、脚本内无此探针。落地真实探针：
  基线一致 → 注入 `DRIFT_PROBE_CANARY` 检出漂移（期望 exit 1）→ 镜像同步后无漂移（期望 exit 0，
  证明探针有判别力、非恒真）。
- **`agent_ci_gate.py` fallback 扫描（S-E22）**：此前只扫 `*-results.json`，全仓该类文件实测为 **0**
  → 扫描恒空、门禁恒返回 0、**从未真正校验过任何信封**（pre-commit hook ① 因此空转）。
  现回退扫基线 markdown 中的成员产出信封（`T-*__<member>.md`，排除下划线前缀的负例/归档区）。
  实测：扫描 10 个信封，合规率 100%。
- **`preflight_check.py` 第 10/11 项（S-E05/S-E09）**：诊断登记表结构完整性（断表/列数检测）·
  README 结构图与实际目录一致（按 `.gitignore` 解析后比对，对齐 git 实际入库口径）。
- **`contract_enforce.py` 自测1b（S-E11）**：`forbidden_boundary` 契约字段与角色矩阵一致性
  （schema 含该字段 · 矩阵覆盖 6 成员 · 禁止边界非空 · 角色归类一致）。
- **`agent_ci_gate.check_wall_clock()`（S-E12）**：墙钟双轨制 WARN 校验（metrics 缺
  `duration_ms_wall` / `duration_source` 非法）——不阻断，供主理人回填。
- **`evolution_log.py` 台账单源化（S-E08）**：自进化台账唯一写入口，含
  `append / backfill / verify / tail / self-test` 五子命令 + commit 确定性校验（禁 HEAD 等非确定标识）。
- **`state_store.py` `evidence` 键（S-E02）**：Workflow D 前置闸的落盘证据路径
  （`search_report` + `verdict_report`）——文件缺失 = 视为未查新。
- **`task_payload.schema.json` `forbidden_boundary` 字段（S-E11）**：下行任务的禁止边界清单
  （非 required，不破历史信封；凡下发即须填）。

### Fixed（缺陷清偿）
- **C4 再诊断新增 4 条 🔴（S-E28…S-E31）**：C4 派独立子智能体从零视角审计本轮全部改动，
  产出 14 条新增问题（🔴4 · 🟡6 · 🟢4），4 条 🔴 已全部清偿——
  S-E28 `contract_enforce` 自测4 改为调用**真实三源判定函数**（抽出 `check_three_source_drift()`
  单一真源，自测1/自测4 共用）并新增**变异测试**（短路真实判定 → 探针必须失去判别力，
  证明非自指模拟）· S-E29 `verify_triz_data` 的 `warn()` 零调用 → `--strict` 语义空转（第二个死参数），
  新增 `check_soft_invariants()` 落地 3 个真实 warn 产出点 · S-E30 `agent_ci_gate` fallback 路径
  `sender = agent_id` → `agent_mismatch` 恒 False → 未知 agent_id 直接 PASS（假绿），
  改为 sender 由**文件名** `T-*__<member>.md` 推导，与 agent_id 独立可比 ·
  S-E31 主理人 MD「phase=3 进 R2」与 `state_store.PHASE_NEXT[3]` 互斥（双语义），
  订正为「phase 是阶段号不是轮次号，R2/R3 轮次由 `search_rounds` 记录」。
- **幽灵验证项 3 处（S-E21）**：preflight 第9项「门禁机械校验」· CONTRACT_ENFORCEMENT 的
  `DRIFT_PROBE` 反向验证 · `verify_triz_data.py --strict` 死参数（解析后从未被读取；现显式语义：
  strict 下 warn 也阻断，默认 warn 不阻断）。
- **门禁键名双轨（S-E01）**：`GATE_ALIASES` 别名归一（写入 `gates.G1` 自动落语义键）+ G2
  `trinity_verdict_pass` 补齐 + `run_regression.check_gates` 改精确读取（原按 dict 插入序取前 N 值
  → 假阴性 → Phase5 永远卡死）。
- **契约 fail-open（S-E15）**：违规默认即 `exit 1`，无需 `--exit-on-fail`。
- **preflight 假绿（S-E16）**：`checked=0` 时不再输出「全部存在」。
- **单字禁词误伤（S-E20）**：`可能` / `估计` 等单字在否定与风险语境误伤合法技术表述 → 豁免词限定。
- **回流硬闸（S-E10/S-E18）**：`reset_for_rework` 重置门禁 + `loopback_count` 累计（上限 2，超限升级 L4）。
- **Phase 2.5 状态节点（S-E19）**：汇聚校准纳入 `PHASE_NEXT` 状态机。

### Changed（口径同步）
- **架构文档四方位对齐（S-E24/S-E25/S-E26/S-E27）**：§3.2 state 模板补全至 5 gates +
  4 metrics 字段 + `evidence` 键（对齐 `state_store.py` 单一权威）；§3.5 改为墙钟双轨制
  （`duration_ms` 成员自报 / `duration_ms_wall` 主理人实测，禁止互相覆盖）；§6.2 L3 仲裁链
  confidence 降为末位参考信号（同步 D3-1 订正，2026-11-08 只落到 MD 未同步架构文档）；
  §4.1 task_payload 示例补 `forbidden_boundary`（schema `additionalProperties:false` → 按原示例
  下发会被拒）。
- **工具清单口径**：OPERATIONS §三 10 → 18 个脚本（补 `diagnosis_trigger.py` / `evolution_log.py`
  两行）；preflight 项数 8 → 10 → **12**（README.md 与 OPERATIONS.md 曾互相矛盾且都落后）。
- **门禁报告输出位置**：`agent_ci_gate` 报告从 `tests/baselines/` 迁至 `outputs/`
  （基线目录是只读真源，门禁产物属派生数据）。
- **README 口径**：阶段标题 6 阶段 → **7 阶段节点**；成员数统一「7 名智能体 = 1 主理人 + 6 成员」；
  结构图按实测重绘（补 `.gitignore` / `knowledge/` / `vendor/` / `.learnings/` / `tests/{cases,baselines}`）。
- **失效引用修正**：`outputs/` → `tests/baselines/`；`plugins/triz-invention-team/*` → 仓库根相对路径；
  删除不存在的 `scripts/register_expert.py` 与技能包名 `triz-patent-toolkit`（实际 4 个技能包）。
- **双 marketplace.json description 版本同步**：v2.6 / v2.7 → v2.9（version 字段本已是 2.8.0）。

### Changed（口径同步 · C4 再诊断 S-E32…S-E41）
- **S-E32 版本收口**：README.zh.md 三处 v2.8 → v2.9 + `plugin.json` description 版本文案同步。
- **S-E33 OPERATIONS 失效引用**：`agent_ci_gate.py:294-296` 行号引用失效 → 订正为 `351-353`；
  同条 L89「基线目录无该类文件」描述已过期（fallback 落地后实测扫 10 个信封）→ 同步订正。
- **S-E34 preflight docstring**：检查项清单仍只列 7 项 → 补全至**实际 12 项**（含第 10/11/12 项）。
- **S-E35 幽灵门禁残留入口**：`agent_ci_gate` 零覆盖时 `--strict` 仍 exit 0（假绿）→
  strict 模式下零覆盖**阻断**（exit 1），默认 warn-only 保持 exit 0。实测：空目录 strict → rc=1 / 默认 → rc=0。
- **S-E36 诊断登记表**：`diagnosis-protocol.md` §六「已修复」列仍写「P1-5（待提交）」→ 补全至实际 commit hash。
- **S-E37 自进化台账**：`docs/evolution-log.tsv` 补录本轮 CYCLE-1 全部批次 commit。
- **S-E38 报告名不符**：README.zh.md 注2 写 `agent_ci_gate_report.json` → 实际产物名 `ci_gate_report.json`。
- **S-E39 成员数口径**：preflight 第 6 项「成员白名单 6 个」显式标注「= 6 执行成员，不含主理人；
  全仓 7 = 1 主理人 + 6 成员」，消除并列歧义。
- **S-E40 死代码**：`LEGACY_CUTOFF` / `is_legacy` 仅在 results.json 路径生效（该路径实测扫描数为 0）
  → 死代码。抽出 `_is_legacy_name()` 单一真源函数，results.json 与 markdown fallback 两路径共用，
  并真正用上 `LEGACY_CUTOFF`（fallback 路径此前完全无 legacy 概念）。
- **S-E41 CHANGELOG 排序**：`[Unreleased]` 段带日期 `2026-11-08` 排在 `[2.9.0]`（2026-11-09）之前形成日期倒序
  → 按 Keep a Changelog 规范改为不带日期的 `[Unreleased]`。

### Fixed（C4 闭环复查新发现 · S-E42/S-E43）
- **S-E42 [P1] 主理人 MD 两处 state 口径漂移**：C4 闭环机械复查（14 条逐条 grep 实测）时发现——
  MD:98 的状态对象快照字段列表以 `...` 省略 gates 后半段，且**完全遗漏** `evidence`（Workflow D
  前置闸证据源）· `conditions`（二审对账源）· `trinity_verdict_pass`（G2 语义键）·
  `total_duration_ms_wall` / `duration_source` / `loopback_count`；MD:576 的状态块模板写
  `metrics: {duration_ms, agent_calls}`——**漏掉 `duration_ms_wall` + `duration_source`**，
  即 S-E25「墙钟双轨制」**未真正下沉到 SOP**，只在架构文档里存在 → 成员照此输出 → 墙钟永远缺失 →
  `agent_ci_gate.check_wall_clock()` 只能永远发 WARN，收不到回填后的墙钟。
  现两处均按 `docs/architecture.md` §3.2（单一权威）补全，并标注**字段层级**：
  成员层 = 单次调用口径（`duration_ms`/`duration_ms_wall`/`duration_source`），
  state 层 = 累计口径（`total_duration_ms`/`total_duration_ms_wall`），两层字段名故意不同、禁止混用。
- **S-E43 [P1] preflight 第 13 项 · state 模板三处真源一致性机械校验（根因整治）**：
  上述漂移的**根因**是 state 模板在**三处手抄**（`state_store.STATE_TEMPLATE` 代码真源 ·
  `architecture.md` §3.2 文档真源 · 主理人 MD 状态块模板 SOP 真源）且**无任何机械校验** → 任一处漏字段都静默漂移。
  现落地第 13 项：机械比对三处的 gates/evidence/metrics 键集合，**双向差集必须为空**，否则 BLOCK
  （契约漂移属阻断项，非文档整洁度问题）。判据：以**代码真源**为准修文档/SOP，不得反向放宽真源。
  - 变异测试（判别力验证）：SOP 删 `total_duration_ms_wall` → BLOCK；architecture 删 `evidence` 段 → BLOCK；还原 → PASS。
  - 实现要点：架构文档模板含 `"phase": 0-5` 等示意值（非法 JSON）→ 文档侧改用**括号配平 + 正则提键**，
    不依赖 `json.loads`；SOP 侧同理（正则 `\{[^}]*\}` 会在内层 `}` 处截断 → 必须配平）。

### Evaluated（评估后不实施）
- `marketplace.json` 的 `source: "./plugins/triz-invention-team"`：本仓 git 根为平铺布局（无 `plugins/`
  嵌套层）。本地安装（`my-experts` 市场根含 `plugins/`）正常；**单仓 GitHub 安装**会指向不存在目录。
  C4 再诊断登记为待办项，本轮不擅自改动发布路径语义。

### 验收证据（机械实测）
- 9 项门禁全绿：`verify_triz_data --strict` · `agent_ci_gate --strict` · `agent_ci_gate --self-test` ·
  `contract_enforce --self-test` · `state_store self-test` · `test_vendor_core` · `preflight_check` ·
  `skill_test_runner` · `evolution_log verify`
- 三用例回归零回退：A 7/7 PASS · B 7/8 PASS + 1 INFO · C 8/8 PASS
- preflight 第 12 项三分支实测：门禁未关 → BLOCK(exit 1) · 证据缺失 → BLOCK · 全关+证据齐 → PASS(exit 0)
- 交叉验证 2 轮：第 1 轮 18 脚本 `--help` 无崩溃 + 13 JSON 合法；第 2 轮从零视角复读产出 19 条确证问题
  （🔴 8 · 🟡 7 · 🟢 4），本轮全部清偿

## [2.8.0] - 2026-11-07

> 第三轮独立诊断（triz-team-diagnosis-independent-20261107-r3.md · 11 维度从零基准）R1-R5 修复 + U1-U3 升维（用户 11-07 确认全量执行）。

### Fixed（R1-R5 · 14 项短板）
- **契约豁免机制重建（R1 · D7-1 高危）**：3 成员 frontmatter 的 `.*?(?!...)` 负向前瞻豁免
  经实测全部为死代码（`.*?` 匹配空串时前瞻恒成立，豁免从未生效）——删除前瞻、禁词纯净化，
  豁免职能收敛到 `contract_enforce.py` 新增 CONTEXT_EXEMPT 上下文窗口豁免表（基本X搭配/
  效果词附证据/约束约定节约复合词/估计否定语境）；`--self-test` 自测3 六组双向断言
  （豁免样本放行 ∧ 违规样本命中）；历史产出回归 exit=0 零误伤
- **路由落盘提醒回链（R2 · D2-1 高危）**：CHANGELOG 2.3.0 声明的 RoutingDecision 提醒在
  v2.4.0 下沉联邦时丢失（联邦真源 0 处该字样）——联邦 core assemble() 尾部注入提醒行 +
  主理人 MD 双保险 + 5 包 vendor 同步（sha 3c3648f1）V1-V6 全 PASS
- **预算口径统一（R3 · D4-1）**：主理人 MD H3.5 注释改「弹性上限120K / L2实测基线84K」
  与 preflight 同口径；**routing-log 单表化（R3 · D2-2）**：断表合并 + R-20260930-004
  缺号登记（无据不编造）+ R-20261015 系列 13 行结果列按证据回填
- **禁词第三源归一（R4 · D7-2）**：run_regression forbidden_regex 支持
  `patterns_source=frontmatter` 动态读真源 + 清洗/豁免与 contract_enforce 同构
  （import 复用 _clean_for_forbidden_scan + EXEMPT_WORDS + _context_exempt——
  B01 首跑 4 处误命中正是两套工具行为漂移的实证，同构后 PASS）
- **登记表回检列（R4 · D6-1）**：诊断登记表增设「48h 回检」列；历史回填教训——
  v2.4.0 联邦下沉丢路由提醒正是缺回检的代价
- **.learnings 启用（R4 · D6-2）**：首两条（BSD grep 假阴性 high + 前瞻豁免死代码 critical）
- **SUMMARY 日期豁免（R5 · D5-1）**：早于 20261015 规范生效日的产出豁免格式告警；
  **resume 路由行规范（R5 · D10-1）**：中断续接须补 task_type=resume 决策行

### Added（U1-U3 · 升维三项）
- **成本感知调度（U1）**：`scripts/cost_profile.py`——metrics.jsonl 聚合成员成本画像
  （n/成功率/tokens 均值·中位·P90/墙钟均值·P90/覆盖率 + ΣP90 预算对照）；主理人路由协议
  增成本因子提示（P90 做预算线/重成员谨慎派/n<3 标样本不足）
- **语义禁词两级门禁（U2）**：`contract_enforce.py --llm-review`——机械层负责「抓」
  （秒级零成本），主理人 LLM 层负责「判」（复核清单：命中行+上下文+复核问题）；
  承认正则无法表达语义边界，判定权交还语义引擎
- **专利族谱记忆（U3）**：`scripts/patent_knowledge.py`——scout 产出 X/Y 威胁机械提取入库
  （幂等去重 patent_no+domain）+ 域/关键词召回（X级排前）+ 失效反馈机制；
  a01 产出初始化 16 条（X5/Y11）；召回=已知雷区先验**不替代三轮查新**；
  Phase 3 前召回预热 + 查新后沉淀——一次性查新升维为积累式查新记忆

### 残留（诚实登记）
- workflow-c-01「法25」断言 FAIL 为历史基线问题（断言按三轮独立产出设计 vs a01 紧凑模式单文件），待用例适配
- spawn_watchdog（P2-15）未建，H4 人工规则顶替
- 联邦 3 包 vendor 已同步含 R2 提醒但各自仓库未提交（提交权留各包活跃会话）
- U3 修复过程自曝并修正 2 处提取正则缺陷（节标题编号在前/专利号尾码 U 漏配）——已入库验证

## [2.7.0] - 2026-11-07

> 独立再诊断 Batch 4-5：检索源改造 + 升维两项（用户 11-07 确认）。

### Added
- **检索源冗余降档（Batch4）**：主源 Google Patents + himmpat（Chrome 登录态），
  L1→L4 逐级降档链（每级登记降档原因 + confidence 折减 L2-5/L3-10/L4-15）；
  凭记忆红线不因降档豁免；scout 新契约「检索渠道显式」（生效日 2026-11-07，
  `_scoped` 日期作用域不追溯——历史归档基线稳定）
- **A-Evolve benchmark 适配（Batch5B）**：`scripts/triz_benchmark.py`——tests/cases 三用例
  → `TrizBenchmark`（get_tasks/evaluate 鸭子类型接口，不硬依赖 a-evolve 包）；
  独立求值模式可直接算分（score=断言通过率，success 线 0.75）；演化闭环打通
- **包内 .learnings/ 三件套**（Batch3）：self-improving-agent 规范（LEARNINGS/ERRORS/FEATURE_REQUESTS）
- **诊断协议固化（Batch3）**：`docs/diagnosis-protocol.md`——触发器 T1-T4 / 10+1 维清单 /
  证据纪律 / 批次修复纪律 / 诊断登记表

### Fixed（Batch5A · 联邦层）
- **shared-core vendor 态 expert_dir 反推死路**：`resolve_expert_dir` 在 core 位于
  `<pkg>/vendor/shared-core/` 时反推到 `vendor/`（无 agents/）→ exit 3。
  修复：用 `__file__.parts` 匹配相邻 vendor/shared-core 段上跳到包根
  （注意 `parent.parent` 后 parts 里已无 shared-core 段——初版修复即栽在此，调试脚本实证）。
  联邦真源 + 4 包 vendor 副本 + VENDOR.json 清单全量同步，V1-V6 6/6 PASS
- **run_regression 三处断言锚点**（Batch3）：gates 语义匹配（旧版只查字面 G1-G5，
  A01 实际用语义表述 → 假阴性）/ abstract 摘要正文段优先锚点 / subprocess 导入缺失
- **L2 断言首次机械全跑 7/7 PASS**（含新 A7 conditions_closed 条件对账）

### Changed（Batch1-3）
- 契约禁词单源化：唯一真源=成员 frontmatter `forbidden_phrases`（脚本启动解析）；
  CONTRACT_ENFORCEMENT.md 全验证项标注 `[机械已实现]`/`[暂缓·人工执行]`
- TASK_STATE 持久化：`scripts/state_store.py`（init/update/show/resume）+ scaffold 自动初始化
  + 主理人 SOP H2 落盘硬规则；envelope schema v1.2.0 增可选 `verdicts{result,score}`
- 预算经验值按 L2 实测校准 111K→84K（92%→70% 预警消除）；H3 软终止评分机械分优先

## [2.6.0] - 2026-11-07

> 独立再诊断（11 维度·11-07）Batch 1：契约单源化 + 文档对齐。含此前未入账的 3 个 commit。

### Added
- **契约禁词单源化（S-Q1）**：`contract_enforce.py` 启动时解析各成员 frontmatter
  `forbidden_phrases` 为唯一真源（删除脚本自维护副本）；`--self-test` 新增三源一致性检查；
  解析失败显式告警不静默
- **验证项实现状态标注（S-Q2）**：`CONTRACT_ENFORCEMENT.md` 全部验证项标注
  `[机械已实现]` / `[暂缓·人工执行]`，消除幽灵验证项；scout「应用号」笔误修正为「申请号」

### Changed
- **架构文档编排对齐（S-C1）**：`architecture.md` §五任务分配表标注编排权威=主理人 SOP
  P2-10 白名单（W1/W2），删除已被取代的"Phase1-2‖Phase3 泛并行"旧实例
- **routing-log 表格修复（S-C3）**：R-004 起断裂在"复盘笔记"后的表格行归位到表结构
- 6 成员 frontmatter 禁词表归一（含新增 `(显著|大幅|明显|高效).*?(?!附实测|附数据)` 等）
- anti-pattern 豁免链补 3 条实测漏配（"而非凭记忆/无一处凭记忆/红线："），L2 全量 13/13 PASS

## [2.5.4] - 2026-10-30 ~ 11-04（补录）

> 此前未入 CHANGELOG 的 3 个 commit（S-Q5）。

- `623a19e` vendor 同步：shared-core B21 升级（check_task_package_v5 结构化校验，联邦真源 1809085da349）
- `91be1a1` fix: 移除 settings.json（宿主 ExpertPluginService 删除判据命中）
- `90d04bd` fix: 订正 settings.json 恢复playbook（宿主删除机制）+ vendor 清单基线刷新
  （详见 `docs/OPERATIONS.md` §二 · failure-005 结案记录）

## [2.5.3] - 2026-10-15

> 独立诊断（triz-team-diagnosis-independent-20261015.md）P0 三项 + 两项遗留债清偿。

### Added（P0）
- **S4-1 五包 vendor 兜底**：viral-evo-lab / research-orchestration-team / smart-textbook-team /
  vet-med-ppt-team 各自获得 vendor/shared-core 三件套 + 防漂移门禁（V1-V5 PASS）；
  分发工具沉淀至 `shared-core/scripts/distribute_vendor.py`
- **S1-1 六成员契约化**：6 成员 frontmatter 增 5 字段（schema_version/contract_owner/
  verified_at/forbidden_phrases/must_verify）；`docs/CONTRACT_ENFORCEMENT.md` +
  `scripts/contract_enforce.py` 门禁（L2 八阶段产物 10/10 PASS，含豁免链：
  元数据标记/通用豁免词/反例引用/学术表达）
- **S3-1 C3 自动触发**：preflight 7→8 项（`--after-search/--outputs-dir/--c3-confirmation-path`）；
  X 级出现且无确认件 → 阻断（3 场景实测）

### Fixed（遗留债）
- pre-commit 钩子增第④层：契约门禁（touches 成员产物时自动跑 contract_enforce）
- `distribute_vendor.py` 入库 shared-core（新增包接入联邦一条命令）

## [2.5.1] - 2026-10-15

> L1 回归（workflow-b-01）首跑暴露的契约一致性缺陷修复（failure-008）。

### Fixed
- **task_id 契约漂移（failure-008）**：`run_regression.py` scaffold 曾生成违约 ID（`T-<date>-REG-B01`，
  第三段含连字符，违反 `result_envelope.schema.json`）→ ①改为合规 ID（`T-<date>-B01`）②新增自校验：
  读取 schema pattern，违约即 exit 2 拒绝生成（fail fast）
- **`token_budget_check.py` FILENAME_RE 过窄**：仅接受 `\d{3}` 数字后缀，比 schema 契约更窄 →
  合法字母数字 ID 被 `--meter` 静默跳过（表现为计量 0 行）。已放宽为与 schema 对齐的 `[A-Za-z0-9]{1,8}`
- **`agent_ci_gate.py` 重复 `extract_envelopes` 定义**：删除死代码（1505 字符），保留版加来源注释；`--self-test` 复验通过

### Added
- **L1 回归首跑通过**（`tests/baselines/l1-analyst-b01/`）：7/8 断言 PASS（1 INFO）；机械计量
  20,018 字符 / ≈10.8k out-tokens / 墙钟 321s（lead_measured）；`_VERIFY.md` 含完整证据链
- `tests/baselines/_pre-fix-b01/`：首跑违约 ID 产物归档 + NOTE 说明（缺陷发现即价值）

## [2.5.0] - 2026-10-15

> 完成 2026-10-14 五维诊断的 P2 全项（P2-9~P2-12）+ 补 commit 级门禁。
> 上游 P0-1~P0-3、P1-4~P1-8 见 [2.4.0]。

### Added
- **`scripts/run_regression.py` + `tests/` 回归测试集（P2-9）**：3 个固定用例
  （workflow-a-01 全链路 L2 / workflow-b-01 analyst L1 / workflow-c-01 scout L1）+
  12 种断言引擎（任务包四要素 / 信封 6 必填（栈平衡提取）/ 模糊词零命中（自动剔除
  代码块与自检行防 failure-006 假阳性）/ 摘要机械计量 / 门禁登记 / 预算汇总等）。
  用法 `--list | --scaffold | --case X --dir <run>`，报告落盘 `regression_report__*.json` 可跨轮对比。
- **`scripts/failure_memory.py`（P2-12）**：episodic 失败记忆注入器——按「本次派单成员 +
  任务域关键词」从 `~/.workbuddy/expert-failures/` 运行时筛出 learned_rule 摘要，
  供主理人追加到 spawn 文案（永远最新，替代静态抄写）。
- **`~/.workbuddy/git-hooks/pre-commit`（P1-6 补全 · commit 级门禁）**：三层快速校验——
  ① `agent_ci_gate.py --strict` ② `scripts/*.py` 语法 ③ 装配链 `--list-members` 冒烟
  （防 shared-core 断链类事故）；硬失败阻断提交。与既有 push 级门禁（release-sync.sh
  `run_gates` 三闸）构成 commit→push 双层防护。
- **并行与预装配协议（P2-10 · 主理人 MD）**：① 预装配流水线强制（等待窗口完成下一
  成员的装配/预读，重叠开销）② 并行白名单 W1 独立咨询 / W2 盲态双审（默认关闭，
  启用须登记对账段）③ 禁用清单（有依赖的串行对禁止假并行）④ routing-log 记录义务。

### Changed
- **主理人 MD 人设注入协议：强制三步 → 强制四步**（新增第 2 步「失败记忆注入」）
- **Phase 3 查新并行化评估结论（P2-11）**：三轮串行为设计约束不做轮间并行；
  新增可选「紧凑模式」（R2+R3 合并为单次 spawn，省 ≈3-4 分钟；须满足区别特征
  明确 + 时间紧迫两条件，默认不启用）

### Fixed
- 回归用例 workflow-b-01 首次冒烟即捕获 1 处「快速」模糊词违规（既有产出），
  验证断言引擎有效（非回归引入）

## [2.4.0] - 2026-10-14

### Added
- **耗时指标双轨制**：`result_envelope` schema v1.0.0 → v1.1.0，新增 `metrics.duration_ms_wall`（主理人实测墙钟）与 `metrics.duration_source`（`self_report|lead_measured|estimated`）
- **`scripts/preflight_check.py`**：团队启动前检查脚本化（7 项：失败索引命中 / routing-log 可写 / 预算估算 / Phase0 五参数 / 权威数据 / 装配器可用 / skills 路径存在），退出码 0=可启动、1=阻断
- **`scripts/verify_triz_data.py`**：TRIZ 权威数据自检（A 矩阵1521交叉点 B 参数39行 C 中文表译名不重复 D 权威锚点复算）
- **路由日志「结果」列**：13 行回填，无据行显式标注「—（无据未补）」禁止凭印象编造
- **发布门禁接入 release-sync.sh**：推送前必跑门禁，不过即阻断（逃生阀 `RELEASE_SYNC_SKIP_GATE=1`）

### Fixed
- **39 参数中文表 #34/#35 译名错位**（failure-007）：#34 Ease of repair 曾误作「装置复杂性」、#35 误作「监控与测试的复杂性」。因查询器把译名拼进输出，错误直接注入成员上下文 → 已改「可维修性」「适应性及多用性」
- **耗时失真规则假阳性**：自报 0 + issues 注明「无法自估」原被判失真 → 改为「未自报」豁免分支（规则若惩罚诚实，下一步就是逼出编造）
- **manifest 版本漂移**：`.codebuddy-plugin` 2.3.0 / `.claude-plugin` 2.2.0 → 三处统一 2.4.0

### Changed
- `assemble_spawn_prompt.py` 下沉 shared-core 联邦共享件（369 行 → 45 行 shim，4 包共用一份真源）；6 成员装配输出 md5 新旧逐一一致，零回归

## [2.3.0] - 2026-09-30

### Added
- **v2.3 装配链**：`RoutingDecision → assemble_spawn_prompt.py → Agent spawn → 落盘验收 → VERIFY`，派单必经脚本
- **H4 平台级错误类**：429/配额耗尽 → 停派同批后续成员 + 三选一降级
- **H3.5 全局预算**：≤120K token / ≤45min / 单成员重试≤4 / 429 最多等 1 次重置
- **团队启动前检查清单 + Phase 0 工程实施参数清单**（安装方式/改造成本/维护频次/失效容忍度/已有部件）
- **路由决策协议**（RoutingDecision JSON + 三档置信度策略 + 强制落盘 routing-log）
- **12 条 RoutingDecision 真实记录**（协议上线后首批，此前为零）

### Fixed
- **triz-matrix 数据准确性灾难**（failure-001 根治）：12 条速查表经核对 0/12 与权威矩阵相符 → 废弃，改为 1521 交叉点权威 CSV + 确定性查询器 `query_triz_matrix.py`，覆盖率 0.8% → 82.1%
- **ACP 双协议跨团队根治**（failure-003）：research / smart-textbook 共 12 成员统一 `result_envelope` v2.4
- **摘要长度门禁被突破**（failure-006）：自评 281 字 vs 实测 371 字符 → 重写 240 字符 + CI gate 机械校验
- **同阶段 handoff 协议冲突**：9-18「有限放开」与 9-29「横直连禁止」矛盾 → 统一为同阶段接力也经主理人中转

## [2.2.0] - 2026-09-10

### Added
- **`agent-protocol` skill**: JSON Schema formalization of `result_envelope` (member → lead) and `task_payload` (lead → member) contracts. Schema files: `skills/agent-protocol/result_envelope.schema.json` + `task_payload.schema.json`
- **CI gate script** (`scripts/agent_ci_gate.py`): Stack-balanced JSON extraction, manual fallback validation (no `jsonschema` library required), legacy archive whitelist, `--strict` mode, `--self-test` mode
- **Token budget checker** (`scripts/token_budget_check.py`): Validates H1 context assembly budget (≤20K tokens) per member
- **`docs/OPERATIONS.md`**: Cross-session recovery playbook (cat> heredoc, settings.json timing-issue workarounds)
- **Dual plugin manifest**: Both `.claude-plugin/` (Claude Code / GitHub Copilot CLI) and `.codebuddy-plugin/` (WorkBuddy) coexist inside `plugins/triz-invention-team/`
- **Single-plugin marketplace layout**: repo root carries the two `marketplace.json` descriptors, the plugin lives self-contained under `plugins/triz-invention-team/` — installable straight from GitHub on Claude Code, GitHub Copilot CLI, and WorkBuddy (`/plugin marketplace add virologist/triz-invention-team`)
- **Bilingual README**: English (`README.md`) + Chinese (`README.zh.md`)
- **`.gitignore`** covering OS / editor / Python / backup / secrets artifacts
- **`docs/evolution-log.tsv`**: self-evolution score history (previously a stray root-level TSV)
- **Apache-2.0 LICENSE** with explicit patent grant
- **CI gate documentation** with typical pitfalls A-D (spawn context stickiness, member no-reply, validate timing, TeamCreate re-spawn)

### Changed
- **Adaptive interaction mode** added to lead agent (interactive vs. autonomous execution)
- **Phase 2.5 fan-in calibration** explicit: search round-1 results must recalibrate analyst directions before round-2
- **Patent portfolio strategy** (core / peripheral / alternative) required at Phase 2 output
- **Embodiment range design hard rule**: numeric ranges require ≥3 data points (end×2 + middle×1) per CN Patent Law Art. 26.3-26.4
- **Tier-break interest-conflict boundary** added: when second-opinion is itself a disputant, escalate L4 directly with conditional-merged verdict (avoids deadlock)
- **Member MD hard constraint** for `result_envelope` (single-point definition in `agent-protocol` SKILL.md; members only reference)

### Fixed
- **B-001** (contract duplication): 6-member MD hard-constraint block (135 chars × 6) replaced with single-point reference + authoritative definition in `agent-protocol/SKILL.md`
- **Validator message format** now uses stack-balanced JSON extraction (handles nested envelopes correctly; was failing on 11/20 archives with regex-based extraction)

### Quality
- CI gate compliance rate: **100%** (24/24 post-v2.2 archives; 5 legacy pre-v2.0 archives exempt by design)
- RedTeam 5-focus diagnosis (responsibility conflict / chain breakage / resource waste / context loss / tool errors): **0 critical bugs**
- All 6 member MDs confirmed boundary compliance via spawn testing
- 2 members (attorney + disclosure) correctly return `status: blocked` on empty upstream input

## [2.0.0] - 2026-08-29

### Added
- Harness 5-layer architecture (H1-H5): Context Assembler, State Store, Loop Controller, Error Recovery, Observability
- Interface contract: result_envelope JSON + task_payload JSON
- Failure index mechanism (12-Factor XII) → `~/.workbuddy/expert-failures/`
- State machine (SOP 6-phase)
- L1-L4 conflict arbitration priority chain
- Member contract: role / capabilities / boundary / output verification

## [1.5.0] - 2026-08-28

### Added
- TRIZ matrix skill (39 parameters, 40 principles, ARIZ-85C, 76 standard solutions)
- Patent law skill (CN Patent Law Art. 22.2/22.3/22.4)
- Claims drafting skill
- Mock examination (严三性) + second-opinion review (审外审)
- Disclosure architect five-element structure
- Patent attorney writer self-check (no ambiguous words, claim dependencies, ≤300-char abstract)

## [1.0.0] - 2026-08-15

### Added
- Initial 7-member team scaffold (lead + analyst + scout + examiner + disclosure + attorney + second-opinion)
- Basic 6-phase SOP
- Single workflow (workflow A)
