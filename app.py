
import json
import streamlit as st
import pandas as pd
import altair as alt
from ct_core import run_simulation

st.set_page_config(page_title="HK IG/Threads CrowdTest‑lite · Dashboard", page_icon="📊", layout="wide")
st.title("📊 HK IG/Threads CrowdTest‑lite（Dashboard）")
st.caption("只顯示圖表與關鍵指標，不提供 CSV 下載。")

with st.sidebar:
    st.header("設定")
    platform = st.selectbox("平台", ["IG", "Threads"], index=0)
    rounds = st.slider("模擬輪數", 1, 10, 3)
    seed = st.number_input("隨機種子", value=42, step=1)

    st.markdown("---")
    st.subheader("Persona 資料")
    persona_file = st.file_uploader("上傳 persona JSON（留空則使用預設）", type=["json"])
    if persona_file:
        personas = json.load(persona_file)
    else:
        with open("hk_personas_ig_threads.json","r",encoding="utf-8") as f:
            personas = json.load(f)
    st.write(f"已載入 persona 數量：**{len(personas)}**")

st.subheader("貼文 A")
a_thumb = st.text_input("A：縮圖一句描述", "明亮自然光下的 PSA10 卡牌近拍，背景是整齊擺放的福袋盒")
a_caption = st.text_area("A：Caption（前 125 字重點）", "【限量 30 袋】⚡PSA10 寶可夢福袋回歸！每袋保證 1 張 PSA10 + 兩包卡包，今次仲有驚喜皮卡超等你開！🔥數量有限，快啲 DM 留名！")
a_hashtags = st.text_input("A：Hashtags", "#香港卡牌 #寶可夢 #PSA10 #香港福袋 #pokemonhk #卡牌收藏 #tcghk")

st.subheader("貼文 B")
b_thumb = st.text_input("B：縮圖一句描述", "桌面平拍 5 張 PSA10 卡牌疊在一起，旁邊擺有福袋與放大鏡")
b_caption = st.text_area("B：Caption（前 125 字重點）", "PSA10 福袋登場🎉 1 袋入手 1 張 PSA10（保值收藏）+ 兩包卡包，總值高達 $700！💎 今次連稀有皮卡超都有機會抽中～")
b_hashtags = st.text_input("B：Hashtags", "#寶可夢卡 #香港卡牌 #PSA10 #tcg #香港寶可夢 #卡牌投資 #pokemonhk")

if st.button("🚀 生成 Dashboard"):
    postA = {"thumb_desc": a_thumb, "caption": a_caption, "hashtags": a_hashtags}
    postB = {"thumb_desc": b_thumb, "caption": b_caption, "hashtags": b_hashtags}
    df, agg = run_simulation(postA, postB, platform=platform, personas=personas, rounds=rounds, seed=seed)

    # --- KPI Row ---
    kpi1, kpi2, kpi3 = st.columns(3)
    with kpi1:
        st.metric("A 贏面", f"{agg['vote_ratio_A']*100:.2f}%")
        st.caption(f"95% CI: {agg['wilson_95ci_A'][0]*100:.1f}% ~ {agg['wilson_95ci_A'][1]*100:.1f}%")
    with kpi2:
        st.metric("B 贏面", f"{agg['vote_ratio_B']*100:.2f}%")
        st.caption(f"樣本：{agg['personas']} persona × {agg['rounds']} 輪")
    with kpi3:
        st.metric("平台", agg["platform"])
        st.caption("IG 偏視覺、Threads 偏文字；已自動調整權重")

    st.markdown("### 互動機率（平均值）")
    avg = pd.DataFrame([
        {"版本":"A","Like":agg["avg_A"]["like_p"],"Comment":agg["avg_A"]["comment_p"],"Share":agg["avg_A"]["share_p"],"Save":agg["avg_A"]["save_p"]},
        {"版本":"B","Like":agg["avg_B"]["like_p"],"Comment":agg["avg_B"]["comment_p"],"Share":agg["avg_B"]["share_p"],"Save":agg["avg_B"]["save_p"]},
    ])
    avg_melt = avg.melt(id_vars=["版本"], var_name="互動", value_name="機率")
    bar = alt.Chart(avg_melt).mark_bar().encode(
        x=alt.X('互動:N', title=None),
        y=alt.Y('機率:Q', axis=alt.Axis(format='%')),
        color='版本:N',
        column=alt.Column('版本:N', title=None)
    ).properties(height=220)
    st.altair_chart(bar, use_container_width=True)

    st.markdown("### 價值錨點（Top-5 命中關鍵字）")
    cuesA = pd.DataFrame(agg['cues']['A'], columns=["關鍵字","次數"]); cuesA["版本"]="A"
    cuesB = pd.DataFrame(agg['cues']['B'], columns=["關鍵字","次數"]); cuesB["版本"]="B"
    cues = pd.concat([cuesA, cuesB], ignore_index=True)
    if len(cues):
        chart = alt.Chart(cues).mark_bar().encode(
            x='關鍵字:N', y='次數:Q', color='版本:N', column='版本:N'
        ).properties(height=220)
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("沒有命中任何價值錨點（如：PSA10 / 總值 / 限量 / 稀有 / 保值 / 抽中）。")

    st.markdown("### 受眾段別投票（摘要）")
    seg = df.copy()
    seg["count"] = 1
    seg_age = seg.groupby(["年齡段","vote"])["count"].sum().reset_index()
    pivot_age = seg_age.pivot(index="年齡段", columns="vote", values="count").fillna(0)
    pivot_age["A比例"] = (pivot_age.get("A",0) / (pivot_age.get("A",0)+pivot_age.get("B",0))).fillna(0)
    st.dataframe(pivot_age.style.format({"A比例": "{:.0%}"}), use_container_width=True)

    st.markdown("### 智能建議")
    bullet = []
    if agg["avg_B"]["like_p"] > agg["avg_A"]["like_p"]:
        bullet.append("把 B 的價值錨點（如『總值』『保值』『稀有』）前置到 A 的首 125 字。")
    if agg["avg_A"]["save_p"] > agg["avg_B"]["save_p"]:
        bullet.append("保留 A 的收藏導向句（如『必收藏』『攻略』），因為它提升 Save 機率。")
    if agg["avg_A"]["share_p"] + agg["avg_B"]["share_p"] < 0.2:
        bullet.append("加入『@朋友/轉發抽獎』等 CTA，提升 Share/Repost。")
    if platform=="IG" and agg["avg_A"]["like_p"] < agg["avg_B"]["like_p"]:
        bullet.append("IG 側重縮圖：嘗試用『明亮／特寫／乾淨背景』的畫面，替換較暗或雜亂的縮圖描述。")
    if not bullet:
        bullet.append("兩版表現接近，可把勝出要素合併成第三版再測一輪。")
    st.write("\n".join([f"- {b}" for b in bullet]))
