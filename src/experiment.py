"""A/B 实验的样本量与功效计算。

这是真实统计计算，不是示意。用于回答产品决策中最先该问的问题：
"以我们的流量，多久才能测出一个值得关心的差异？"
"""
from __future__ import annotations
import math

def _z(p: float) -> float:
    """标准正态分位数（Acklam 有理逼近）。"""
    a=[-3.969683028665376e+01,2.209460984245205e+02,-2.759285104469687e+02,
       1.383577518672690e+02,-3.066479806614716e+01,2.506628277459239e+00]
    b=[-5.447609879822406e+01,1.615858368580409e+02,-1.556989798598866e+02,
       6.680131188771972e+01,-1.328068155288572e+01]
    c=[-7.784894002430293e-03,-3.223964580411365e-01,-2.400758277161838e+00,
       -2.549732539343734e+00,4.374664141464968e+00,2.938163982698783e+00]
    d=[7.784695709041462e-03,3.224671290700398e-01,2.445134137142996e+00,
       3.754408661907416e+00]
    pl, ph = 0.02425, 1-0.02425
    if p < pl:
        q=math.sqrt(-2*math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5])/((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p > ph:
        q=math.sqrt(-2*math.log(1-p))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5])/((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q=p-0.5; r=q*q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q/(((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)


def sample_size(p1: float, mde_rel: float, alpha: float = 0.05,
                power: float = 0.8) -> dict:
    """双样本比例检验，双尾。mde_rel 为相对变化，如 -0.05 表示转化率下降5%。"""
    p2 = p1 * (1 + mde_rel)
    pbar = (p1 + p2) / 2
    za, zb = _z(1 - alpha / 2), _z(power)
    n = 2 * (za + zb) ** 2 * pbar * (1 - pbar) / (p1 - p2) ** 2
    return {"基线转化率": round(p1, 4), "相对最小可检测效应": mde_rel,
            "对照组预期": round(p1, 4), "实验组预期": round(p2, 4),
            "显著性水平": alpha, "统计功效": power,
            "每组所需样本": math.ceil(n), "合计样本": math.ceil(n) * 2}


def days_needed(n_total: int, daily_traffic: int, exposure: float = 1.0) -> float:
    return round(n_total / (daily_traffic * exposure), 1)


def mde_at(n_per_arm: int, p1: float, alpha: float = 0.05,
           power: float = 0.8) -> float:
    """给定样本量，能检出的最小相对效应。"""
    za, zb = _z(1 - alpha / 2), _z(power)
    lo, hi = 1e-6, 0.999
    for _ in range(200):
        mid = (lo + hi) / 2
        p2 = p1 * (1 - mid); pbar = (p1 + p2) / 2
        n = 2 * (za + zb) ** 2 * pbar * (1 - pbar) / (p1 - p2) ** 2
        if n > n_per_arm: lo = mid
        else: hi = mid
    return round((lo + hi) / 2, 4)
