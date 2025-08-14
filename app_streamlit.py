
import json
import streamlit as st
import pandas as pd
from ct_core import run_simulation

st.set_page_config(page_title="HK IG/Threads CrowdTest‑lite", page_icon="🇭🇰")
st.title("🇭🇰 HK IG/Threads CrowdTest‑lite")
st.caption("輸入兩個版本的貼文（A/B），模擬香港 IG／Threads 受眾的互動反應。")

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

if st.button("🚀 開始模擬"):
    postA = {"thumb_desc": a_thumb, "caption": a_caption, "hashtags": a_hashtags}
    postB = {"thumb_desc": b_thumb, "caption": b_caption, "hashtags": b_hashtags}
    df, agg = run_simulation(postA, postB, platform=platform, personas=personas, rounds=rounds, seed=seed)

    st.success("模擬完成！")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("A 贏面", f"{agg['vote_ratio_A']*100:.2f}%")
        st.write(f"95%信賴區間（A）: {agg['wilson_95ci_A'][0]*100:.2f}% ~ {agg['wilson_95ci_A'][1]*100:.2f}%")
    with col2:
        st.metric("B 贏面", f"{agg['vote_ratio_B']*100:.2f}%")
        st.write(f"樣本：{agg['personas']} persona × {agg['rounds']} 輪｜平台：{agg['platform']}")

    st.subheader("Persona 細項結果（可下載 CSV）")
    st.dataframe(df, use_container_width=True)
    st.download_button("下載 CSV", data=df.to_csv(index=False).encode("utf-8-sig"), file_name="hk_ig_threads_sim_result.csv", mime="text/csv")

    st.subheader("聚合統計（JSON）")
    st.json(agg)

st.markdown("---")
st.caption("注意：此模擬基於文字與縮圖描述的啟發式與隨機化行為，非平台真實演算法；請搭配實際 A/B 測試微調。")
