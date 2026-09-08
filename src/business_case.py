"""透明化的盈亏平衡模型。

**为什么不直接算"能带来多少收入"。**
常见写法是"假设转化提升 2%，客单价 5 万，月曝光 10 万 → 收益 1 亿"。
问题在于 2% 是凭空来的：面试时被问"这个 2% 从哪来"就答不上来，
而且一旦这个数字被质疑，旁边真实测出来的数字也会跟着被怀疑。

这里换一个问法：**不猜收益，而是算"要抵消损失，需要什么条件成立"，
再判断这个条件是否可信。** 未知量从假设变成了结论。

具体到本场景：展示 IRR 真实年化会让一部分用户放弃分期（收入减少），
但更知情的用户投诉更少、逾期更少（成本减少）。
问题因此变成：**投诉率和逾期率要降多少，才能把转化的损失抵回来？**

所有参数都是假设值，来源写在 ASSUMPTIONS 里，可以改了看敏感性。
本模块不声称任何一个数字是真实业务数据。
"""
from __future__ import annotations

ASSUMPTIONS = {
    "月曝光人数":     (100_000, "分期入口的月度曝光量"),
    "分期转化率":     (0.12,    "曝光到成功办理分期的转化率"),
    "平均分期本金":   (12_000,  "与语料中的算例一致"),
    "平均期数":       (12,      "12 期为最常见选择"),
    "每期手续费率":   (0.006,   "语料 F001 现行费率"),
    "转化相对降幅":   (0.05,    "展示真实年化后的转化下降，待实验测定"),
    "单笔投诉处理成本": (180,    "人工处理与回访的综合成本"),
    "基线投诉率":     (0.015,   "分期业务的客户投诉率"),
    "单笔逾期损失":   (900,     "催收成本与拨备的综合估计"),
    "基线首期逾期率": (0.030,   "首期账单逾期比例"),
}


def _v(o: dict | None, k: str):
    return (o or {}).get(k, ASSUMPTIONS[k][0])


def model(overrides: dict | None = None) -> dict:
    exposure = _v(overrides, "月曝光人数")
    conv = _v(overrides, "分期转化率")
    principal = _v(overrides, "平均分期本金")
    periods = _v(overrides, "平均期数")
    fee_rate = _v(overrides, "每期手续费率")
    drop_rel = _v(overrides, "转化相对降幅")
    complaint_cost = _v(overrides, "单笔投诉处理成本")
    complaint_rate = _v(overrides, "基线投诉率")
    default_cost = _v(overrides, "单笔逾期损失")
    default_rate = _v(overrides, "基线首期逾期率")

    orders = exposure * conv
    fee_per_order = principal * fee_rate * periods       # 单笔手续费收入
    lost_orders = orders * drop_rel
    revenue_loss = lost_orders * fee_per_order

    # 抵消侧：留下来的订单更知情，投诉与逾期减少
    remaining = orders - lost_orders
    complaint_base = remaining * complaint_rate * complaint_cost
    default_base = remaining * default_rate * default_cost

    return {
        "月订单数": round(orders),
        "单笔手续费收入": round(fee_per_order, 2),
        "流失订单数": round(lost_orders),
        "月手续费收入损失": round(revenue_loss),
        "剩余订单的月投诉成本": round(complaint_base),
        "剩余订单的月逾期损失": round(default_base),
        # 盈亏平衡：只靠一个渠道抵消时，各自需要的相对降幅
        "仅靠投诉下降需降": (round(revenue_loss / complaint_base, 4)
                       if complaint_base else None),
        "仅靠逾期下降需降": (round(revenue_loss / default_base, 4)
                       if default_base else None),
        "两者各承担一半需各降": (round(revenue_loss / 2 / complaint_base, 4)
                          if complaint_base else None,
                          round(revenue_loss / 2 / default_base, 4)
                          if default_base else None),
    }


def verdict(m: dict) -> str:
    a = m["仅靠投诉下降需降"]
    b = m["仅靠逾期下降需降"]
    if a is None or b is None:
        return "参数不足。"
    if a > 1 or b > 1:
        need = min(a, b)
        if need > 1:
            return ("两个渠道单独都抵不平——需要的降幅超过 100%，不可能达成。"
                    "结论不是'不要做'：披露是义务。结论是**不要用收入口径为它辩护**，"
                    "而应按合规成本口径立项，把转化损失作为已知代价申报。")
    if min(a, b) < 0.20:
        return ("抵消所需的降幅在 20% 以内，属于可能达成的范围——"
                "但必须在实验中同时测量投诉率与逾期率，否则这只是一个假设。")
    return ("抵消所需的降幅偏大，落在'需要证据才敢主张'的区间。"
            "建议先做小流量实验测出真实的转化降幅，再重算这张表。")


if __name__ == "__main__":
    m = model()
    for k, v in m.items():
        print(f"{k:24s} {v}")
    print()
    print(verdict(m))
