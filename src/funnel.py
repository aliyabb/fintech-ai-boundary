"""AI 功能漏斗模型。

⚠️ 重要声明：本模块**不是真实埋点数据**。
本项目没有线上流量，因此漏斗各环节的转化率是**参数化假设**，
用途是回答实验设计问题（多大的效应能测出来、要跑多久），
而不是声称"我们的产品达到了这些数字"。

真实数据只有一处：合规拦截率与意图路由分布，来自项目一的实际评测运行，
在 load_real_signals() 中读取。
"""
from __future__ import annotations
import json, pathlib

# ── 参数化假设（可调，用于敏感性分析）────────────────────
ASSUMPTIONS = {
    "曝光→提问":  {"rate": 0.34, "依据": "行业内 AI 入口首次点击率通常在 25%~40%"},
    "提问→有效应答": {"rate": 0.88, "依据": "由项目一 C 方案准确率给出上界"},
    "有效应答→采纳": {"rate": 0.46, "依据": "假设：用户认可并继续操作"},
    "采纳→查看产品详情": {"rate": 0.26, "依据": "假设：商业转化环节"},
    "查看详情→7日复用": {"rate": 0.19, "依据": "假设：留存"},
}
STAGES = list(ASSUMPTIONS)


def funnel(exposure: int = 100_000, overrides: dict | None = None) -> list[dict]:
    o = overrides or {}
    n = exposure
    out = [{"环节": "曝光", "人数": n, "环节转化率": None, "累计转化率": 1.0}]
    for s in STAGES:
        r = o.get(s, ASSUMPTIONS[s]["rate"])
        n = int(round(n * r))
        out.append({"环节": s.split("→")[1], "人数": n, "环节转化率": round(r, 4),
                    "累计转化率": round(n / exposure, 5)})
    return out


def biggest_drop(rows: list[dict]) -> dict:
    cand = [r for r in rows if r["环节转化率"] is not None]
    return min(cand, key=lambda r: r["环节转化率"])


UPSTREAM = pathlib.Path("results/upstream_metrics.json")
SIBLING = pathlib.Path("../fintech-qa-compliance-eval/results/metrics.json")


def sync_upstream() -> bool:
    """把项目一的指标快照到本仓库，使本项目可独立克隆运行。"""
    if SIBLING.exists():
        UPSTREAM.parent.mkdir(exist_ok=True)
        UPSTREAM.write_text(SIBLING.read_text(encoding="utf-8"), encoding="utf-8")
        return True
    return False


def load_real_signals() -> dict | None:
    """项目一的真实运行信号。优先用本仓库快照，保证独立可用。"""
    sync_upstream()
    if not UPSTREAM.exists():
        return None
    m = json.loads(UPSTREAM.read_text(encoding="utf-8"))
    return {"来源": "项目一实际评测运行（快照于 results/upstream_metrics.json）", "指标": m}
