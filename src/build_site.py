"""生成 docs/index.html。漏斗数字来自 src/funnel.py 的参数化模型（已标注为假设），
样本量与 MDE 来自 src/experiment.py 的真实统计计算，
合规拦截与路由分布来自项目一的实际运行。"""
from __future__ import annotations
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from funnel import funnel, biggest_drop, ASSUMPTIONS, load_real_signals
from experiment import sample_size, days_needed, mde_at
from business_case import model, verdict

D = pathlib.Path("docs"); D.mkdir(exist_ok=True)
CSS = (pathlib.Path(__file__).parent / "style.css").read_text(encoding="utf-8")


def build():
    rows = funnel(100_000)
    drop = biggest_drop(rows)
    real = load_real_signals()

    frows = ""
    for r in rows:
        w = r["累计转化率"] * 100
        step = "—" if r["环节转化率"] is None else f"{r['环节转化率']*100:.1f}%"
        hl = ' class="hl"' if r["环节"] == drop["环节"] else ""
        frows += (f'<tr{hl}><td>{r["环节"]}</td><td class="num">{r["人数"]:,}</td>'
                  f'<td class="num">{step}</td><td class="num">{w:.2f}%</td>'
                  f'<td style="width:180px"><div class="bar"><i style="width:{max(w,0.4)}%;'
                  f'background:var(--accent)"></i></div></td></tr>')

    srows = ""
    for mde in [-0.03, -0.05, -0.10, -0.15]:
        s = sample_size(0.12, mde)
        srows += (f'<tr><td class="num">{abs(mde)*100:.0f}%</td>'
                  f'<td class="num">{s["每组所需样本"]:,}</td>'
                  f'<td class="num">{s["合计样本"]:,}</td>'
                  f'<td class="num">{days_needed(s["合计样本"], 8000)} 天</td></tr>')

    mrows = "".join(f'<tr><td class="num">{n:,}</td>'
                    f'<td class="num">{mde_at(n,0.12)*100:.2f}%</td></tr>'
                    for n in [5_000, 20_000, 50_000, 100_000])

    arows = "".join(f'<tr><td>{k}</td><td class="num">{v["rate"]*100:.0f}%</td>'
                    f'<td>{v["依据"]}</td></tr>' for k, v in ASSUMPTIONS.items())

    real_block = "<p class='lede'>项目一的指标快照尚未同步，本节留空。</p>"
    if real:
        P = real["指标"]["方案"]
        rr = "".join(
            f'<tr><td>{k}</td><td class="num">{v["违规回答率"]*100:.1f}%</td>'
            f'<td class="num">{(v["幻觉率"] or 0)*100:.1f}%</td>'
            f'<td class="num">{v["总体准确率"]*100:.1f}%</td></tr>'
            for k, v in P.items())
        real_block = f"""<div class="scroll"><table><thead><tr><th>方案</th>
<th>违规回答率</th><th>幻觉率</th><th>总体准确率</th></tr></thead><tbody>{rr}</tbody></table></div>
<p class="lede">以上为<strong>真实运行数据</strong>，来自项目一 {real['指标']['运行信息']['总应答数']} 次实际应答。</p>"""

    page = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI 能力边界与增长实验设计</title><style>{CSS}
.calcbox{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px;
 background:var(--card);border:1px solid var(--line);border-radius:11px;padding:17px 18px;margin:18px 0}}
.calcbox label{{font-size:12.5px;color:var(--muted);display:flex;flex-direction:column;gap:6px}}
.calcbox input,.calcbox select{{padding:8px 10px;border:1px solid var(--line);border-radius:7px;
 background:var(--bg);color:var(--fg);font-size:14px;font-family:inherit;
 font-variant-numeric:tabular-nums}}
</style></head><body><div class="wrap">
<header>
<h1>AI 能力边界决策 × 增长实验设计</h1>
<p class="sub">三个问题：这件事该不该交给 AI？做了之后怎么衡量？
当合规要求和转化率冲突时，产品经理怎么决定？</p>
<div class="tags"><span>能力边界</span><span>埋点设计</span><span>A/B 实验</span>
<span>样本量计算</span><span>合规与增长冲突</span></div>
</header>

<h2>一、AI 能力边界决策表</h2>
<p class="lede">常见做法是分"能做 / 不能做"两档。金融场景不够用：
有些任务技术上做得到但监管不允许，有些能生成但必须有人签字。所以分四档。
完整 15 条见 <a href="https://github.com/aliyabb/fintech-ai-boundary/blob/main/docs/AI能力边界决策表.md">决策表全文</a>。</p>
<div class="scroll"><table><thead><tr><th>档位</th><th>含义</th><th>判定条件</th><th>本组示例</th></tr></thead><tbody>
<tr><td><strong>A</strong></td><td>AI 直接做</td><td>有原文可引，错误可追溯且代价可承受</td><td>条款检索、风险等级说明、界面结构组织</td></tr>
<tr><td><strong>B</strong></td><td>确定性代码</td><td>答案唯一；模型实测不可靠；错误直接造成用户损失</td><td>IRR 年化计算、还款计划、赎回费</td></tr>
<tr><td><strong>C</strong></td><td>AI 生成 + 人工审核</td><td>输出对外具有合规效力</td><td>风险揭示话术、营销文案、投诉分级</td></tr>
<tr><td><strong>D</strong></td><td>禁止</td><td>缺少资质，或行为本身被监管禁止</td><td>推荐产品、预测收益、个性化配置、判断买卖时点</td></tr>
</tbody></table></div>
<div class="note"><strong>顺序不能颠倒：先问资质，再问精度，最后才问体验。</strong>
第 11–14 条落在 D 档，不是因为模型做不好，而是因为没有投资顾问资质（F029）。
效果再好也不做——这是 AI 产品经理最容易被绕过的一条。</div>

<h2>二、来自实际运行的信号</h2>
{real_block}

<h2>三、AI 功能漏斗</h2>
<div class="note"><strong>这不是真实埋点数据。</strong>本项目没有线上流量，
各环节转化率是<strong>参数化假设</strong>，用途是回答"多大的效应能测出来、要跑多久",
而不是声称产品达到了这些数字。假设与依据全部列在下方，可在 <code>src/funnel.py</code> 中调整。</div>
<div class="scroll"><table><thead><tr><th>环节</th><th>人数</th><th>环节转化率</th><th>累计</th><th></th></tr></thead>
<tbody>{frows}</tbody></table></div>
<p class="lede">最弱环节：<strong>{drop["环节"]}</strong>（{drop["环节转化率"]*100:.1f}%）。
在假设成立的前提下，优化优先级应落在这里而不是入口曝光。</p>
<h3>假设来源</h3>
<div class="scroll"><table><thead><tr><th>环节</th><th>假设值</th><th>依据</th></tr></thead><tbody>{arows}</tbody></table></div>

<h2>四、实验：展示真实年化会不会打掉转化？</h2>
<p class="lede">分期入口现在展示"每期手续费 0.6%"。按 F030 口径应同时展示 IRR 实际年化——
12 期是 13.03%，3 期名义 1.65% 而实际 9.87%，相差 5.98 倍。
数字越透明，用户越可能不办。<strong>这是本组唯一一个商业指标与用户利益直接冲突的决策。</strong></p>

<h3>样本量（真实统计计算）</h3>
<div class="scroll"><table><thead><tr><th>想检出的相对降幅</th><th>每组样本</th><th>合计</th><th>按日均 8000 曝光</th></tr></thead>
<tbody>{srows}</tbody></table></div>
<div class="scroll"><table><thead><tr><th>每组样本</th><th>能检出的最小相对效应</th></tr></thead><tbody>{mrows}</tbody></table></div>
<p class="lede"><strong>这张表本身就是产品结论</strong>：只有两周，就只能检出 5% 以上的降幅。
小于 5% 的变化在统计上看不见，那么决策就不该建立在"降了 2%"这种读数上。</p>

<h3>决策规则（实验开始前写定）</h3>
<div class="scroll"><table><thead><tr><th>情形</th><th>决策</th></tr></thead><tbody>
<tr><td>降幅 &lt; 5%，护栏指标不恶化</td><td>全量上线</td></tr>
<tr><td>降幅 5%–15%，取消率与投诉率同时下降</td><td>上线，改展示形式为对比条</td></tr>
<tr><td>降幅 &gt; 15%</td><td>仍然上线，升级为定价专项</td></tr>
<tr><td>任一护栏指标恶化</td><td>回滚排查，优先怀疑展示引发误解</td></tr>
</tbody></table></div>
<div class="note">四行的共同点：<strong>没有一行是"不上线"</strong>。
F030 是披露义务，不是可选优化项。实验决定的是<strong>怎么展示</strong>，不是<strong>要不要展示</strong>。
这个前提不写清楚，实验就会变成为不合规找数据借口。
完整设计见 <a href="https://github.com/aliyabb/fintech-ai-boundary/blob/main/docs/实验设计_真实年化展示.md">实验设计文档</a>。</div>


<h2>五、样本量计算器</h2>
<p class="lede">上面的表是固定参数下的结果。这里可以换成你自己的数字——
这是 <code>src/experiment.py</code> 的浏览器端实现，同一套公式（双样本比例检验，双尾）。</p>
<div class="calcbox">
  <label>基线转化率 <input id="p1" type="number" value="12" step="0.1" min="0.1" max="99"> %</label>
  <label>想检出的相对降幅 <input id="mde" type="number" value="5" step="0.5" min="0.5" max="90"> %</label>
  <label>日均曝光 <input id="traf" type="number" value="8000" step="500" min="100"></label>
  <label>统计功效 <select id="pw"><option value="0.8" selected>80%</option>
    <option value="0.9">90%</option></select></label>
</div>
<div class="kpis" id="out"></div>
<p class="lede" id="verdict"></p>


<h2>六、商业论证：透明化能不能被抵消</h2>
<div class="note"><strong>先说方法。</strong>常见写法是"假设转化提升 2%，客单价 5 万 → 收益 1 亿"。
问题是 2% 从哪来——被追问就答不上来，而且一个编造的数字会连累旁边所有真实测出来的数字。
<br><br>换一个问法：<strong>不猜收益，而是算"要抵消损失，需要什么条件成立"，
再判断这个条件是否可信。</strong>未知量从假设变成结论。</div>
<p class="lede">展示真实年化会让一部分用户放弃分期（收入减少），
但更知情的用户投诉更少、逾期更少（成本减少）。
问题因此变成：<strong>投诉率和逾期率要降多少，才能把转化的损失抵回来？</strong></p>
<div class="calcbox">
  <label>月曝光 <input id="bexp" type="number" value="100000" step="10000" min="1000"></label>
  <label>分期转化率 <input id="bconv" type="number" value="12" step="0.5" min="0.1"> %</label>
  <label>转化相对降幅 <input id="bdrop" type="number" value="5" step="0.5" min="0.1"> %</label>
  <label>平均本金 <input id="bprin" type="number" value="12000" step="1000" min="600"></label>
  <label>基线投诉率 <input id="bcr" type="number" value="1.5" step="0.1" min="0.01"> %</label>
  <label>单笔投诉成本 <input id="bcc" type="number" value="180" step="10" min="1"></label>
  <label>基线首期逾期率 <input id="bdr" type="number" value="3.0" step="0.1" min="0.01"> %</label>
  <label>单笔逾期损失 <input id="bdc" type="number" value="900" step="50" min="1"></label>
</div>
<div class="kpis" id="bout"></div>
<p class="lede" id="bverdict"></p>
<p class="lede">完整推导与敏感性分析见
<a href="https://github.com/aliyabb/fintech-ai-boundary/blob/main/docs/商业论证_盈亏平衡.md">商业论证文档</a>。
所有参数均为假设值，非真实业务数据。</p>

<footer>漏斗为参数化假设模型；样本量与 MDE 为真实统计计算（<code>src/experiment.py</code>）；
第二节数据来自项目一实际评测运行。本页由 <code>src/build_site.py</code> 生成。</footer>
</div>
<script>
/* Acklam 有理逼近求标准正态分位数，与 src/experiment.py 的实现一致 */
function z(p){{
  const a=[-3.969683028665376e+01,2.209460984245205e+02,-2.759285104469687e+02,
           1.383577518672690e+02,-3.066479806614716e+01,2.506628277459239e+00],
        b=[-5.447609879822406e+01,1.615858368580409e+02,-1.556989798598866e+02,
           6.680131188771972e+01,-1.328068155288572e+01],
        c=[-7.784894002430293e-03,-3.223964580411365e-01,-2.400758277161838e+00,
           -2.549732539343734e+00,4.374664141464968e+00,2.938163982698783e+00],
        d=[7.784695709041462e-03,3.224671290700398e-01,2.445134137142996e+00,
           3.754408661907416e+00], pl=0.02425;
  let q,r;
  if(p<pl){{q=Math.sqrt(-2*Math.log(p));
    return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5])/((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1);}}
  if(p>1-pl){{q=Math.sqrt(-2*Math.log(1-p));
    return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5])/((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1);}}
  q=p-0.5; r=q*q;
  return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q/
         (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1);
}}
function calc(){{
  const p1=+p1El.value/100, rel=-(+mdeEl.value/100), traf=+trafEl.value, pw=+pwEl.value;
  const p2=p1*(1+rel), pbar=(p1+p2)/2, za=z(0.975), zb=z(pw);
  const n=Math.ceil(2*Math.pow(za+zb,2)*pbar*(1-pbar)/Math.pow(p1-p2,2));
  const days=(2*n)/traf;
  const fmt=x=>x.toLocaleString("en-US");
  out.innerHTML=
    '<div class="kpi"><div class="n">'+fmt(n)+'</div><div class="l">每组所需样本</div></div>'+
    '<div class="kpi"><div class="n">'+fmt(2*n)+'</div><div class="l">合计样本</div></div>'+
    '<div class="kpi"><div class="n '+(days>21?"bad":days>14?"warn":"good")+'">'+
      days.toFixed(1)+' 天</div><div class="l">按当前曝光需要跑</div></div>'+
    '<div class="kpi"><div class="n">'+(p2*100).toFixed(2)+'%</div>'+
      '<div class="l">实验组预期转化率</div><div class="d">对照组 '+(p1*100).toFixed(2)+'%</div></div>';
  verdict.innerHTML = days>28
    ? "<strong>超过四周。</strong>要么接受更大的最小可检测效应，要么提高曝光量——"+
      "否则这个实验读不出结论，只会读出噪声。"
    : days>14
    ? "两到四周。可以做，但要提前写好决策规则，避免中途看数据反复改判断标准。"
    : "<strong>两周内可完成。</strong>注意：能快速跑完，往往意味着只能检出较大的效应，"+
      "小幅变化仍然看不见。";
}}
const p1El=document.getElementById("p1"), mdeEl=document.getElementById("mde"),
      trafEl=document.getElementById("traf"), pwEl=document.getElementById("pw"),
      out=document.getElementById("out"), verdict=document.getElementById("verdict");
[p1El,mdeEl,trafEl,pwEl].forEach(e=>e.addEventListener("input",calc));
calc();
</script>
<script src="business.js"></script></body></html>"""
    (D / "index.html").write_text(page, encoding="utf-8")
    print(f"docs/index.html 已生成（{len(page)} 字节）")


if __name__ == "__main__":
    build()
