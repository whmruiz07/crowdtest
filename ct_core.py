
import re, random, math, json
import pandas as pd

def frac_ascii(s):
    if not s: return 0.0
    ascii_count = sum(1 for ch in s if ord(ch) < 128)
    return ascii_count / max(1, len(s))

def contains_chinese(s):
    return any('\u4e00' <= ch <= '\u9fff' for ch in s)

def has_hook(caption):
    patterns = [r'^\s*\d', r'\?|\？', r'攻略|懶人包|秘訣|教學', r'必收藏|收藏|Save|save',
                r'限時|優惠|折扣', r'親測|實測', r'你會|你有冇|點樣', r'一步一步|Step[-\s]?by[-\s]?step']
    return any(re.search(p, caption or "", flags=re.I) for p in patterns)

def has_cta(caption):
    patterns = [r'留言|Comment|comment', r'收藏|Save|save', r'分享|Share|share', r'Tag|tag|@朋友|@人']
    return any(re.search(p, caption or "", flags=re.I) for p in patterns)

def hashtag_list(s):
    if not s: return []
    tags = [t.strip('#').strip() for t in re.findall(r'#([^\s#]+)', s)]
    return [t.lower() for t in tags]

def interest_tag_overlap(interests, tags):
    mapping = {
        "美食": ["香港美食","hkfood","foodie","打卡","港式早餐","咖啡店","cafe","cafelife","hkfoodie"],
        "旅遊": ["旅遊","旅行","travel","hongkong","hk"],
        "咖啡店探店": ["咖啡店","cafe","coffeetime","latte"],
        "投資": ["投資","投資理財","stocks","hkstocks","bitcoin","crypto"],
        "教育": ["教育","學習日常","teacher","教學","edtech"],
        "科技": ["科技","ai","人工智能","tech"],
        "動漫": ["動漫","anime","pokemon","卡牌","tcg"],
        "卡牌": ["pokemon","卡牌","tcg","寶可夢"],
        "時尚": ["時尚","ootd","穿搭","fashion","hkstyle"],
        "美妝": ["美妝","makeup","skincare"],
        "搞笑": ["搞笑","meme","funny"],
        "親子": ["親子","親子活動","kids","family"]
    }
    tagset = set(tags)
    score = 0
    for it in interests:
        alts = mapping.get(it, [])
        for alt in alts:
            if alt.lower() in tagset:
                score += 1
                break
    return score / max(1, len(interests))

def thumb_attractiveness(desc):
    if not desc: return 0.5
    pos = ["明亮", "特寫", "乾淨背景", "構圖清晰", "人像眼神", "食物", "主體居中", "自然光", "高對比", "卡牌近拍"]
    neg = ["模糊", "陰暗", "雜亂", "背光", "低解析度"]
    score = 0.5 + 0.08*sum(1 for k in pos if k in desc) - 0.1*sum(1 for k in neg if k in desc)
    return min(0.95, max(0.05, score))

def caption_quality(caption):
    if not caption: return 0.4
    length = len(caption)
    ascii_frac = frac_ascii(caption)
    zh = contains_chinese(caption)
    hook = has_hook(caption)
    cta = has_cta(caption)
    len_score = 0.6 if 30 <= length <= 220 else (0.5 if length < 30 else 0.45)
    lang_score = 0.6 if zh else (0.55 if 0.3 < ascii_frac < 0.7 else 0.5)
    hook_score = 0.12 if hook else 0
    cta_score = 0.08 if cta else 0
    return min(0.95, max(0.1, len_score + lang_score - 0.5 + hook_score + cta_score))

def early_line_strength(caption):
    if not caption: return 0.4
    first125 = caption[:125]
    s = 0.4
    if has_hook(first125): s += 0.15
    if re.search(r'[\!\?！？]$', first125.strip()): s += 0.05
    return min(0.95, max(0.1, s))

def persona_vector(persona):
    age = persona.get("年齡段","19-25")
    age_map = {"13-18":0.55, "19-25":0.7, "26-35":0.65, "36+":0.5}
    base_engagement = age_map.get(age, 0.6)
    emoji_accept = float(persona.get("emoji接受度", 0.5))
    return base_engagement, emoji_accept

def emoji_bonus(caption, persona):
    emojis = re.findall(r'[\U0001F300-\U0001FAFF]', caption or "")
    if not emojis: return 0.0
    accept = float(persona.get("emoji接受度",0.5))
    count = min(5, len(emojis))
    return (accept - 0.5) * 0.15 * (count/3)

def time_slot_modifier(persona):
    slot = persona.get("使用時間段","晚上9點後")
    return 1.05 if slot in ["午餐時段","晚上9點後","放學後5點至8點","週末下午"] else 1.0

def value_anchor_bonus(caption, hashtags):
    text = f"{caption} {hashtags}".lower()
    cues = [("psa10", 0.08), ("總值", 0.06), ("$", 0.05), ("稀有", 0.06),
            ("限量", 0.05), ("保值", 0.05), ("保證", 0.04), ("抽中", 0.04)]
    score = 0.0; hits = []
    for cue, w in cues:
        if cue in text:
            score += float(w); hits.append((cue, float(w)))
    return min(0.15, score), hits

def simulate_interactions(post, persona, platform="IG"):
    caption = post.get("caption","")
    hashtags_str = post.get("hashtags","")
    hashtags = hashtag_list(hashtags_str)
    thumb_desc = post.get("thumb_desc","")

    base_eng, emoji_acc = persona_vector(persona)
    q_thumb = thumb_attractiveness(thumb_desc)
    q_caption = caption_quality(caption)
    q_first = early_line_strength(caption)
    overlap = interest_tag_overlap(persona.get("興趣",[]), hashtags)
    e_bonus = emoji_bonus(caption, persona)
    t_mod = time_slot_modifier(persona)
    v_bonus, v_hits = value_anchor_bonus(caption, hashtags_str)

    if platform.upper()=="IG":
        like_w, comment_w, save_w, share_w = 0.45, 0.2, 0.25, 0.10
        first_impression = 0.60*q_thumb + 0.40*q_first
    else:
        like_w, comment_w, save_w, share_w = 0.5, 0.3, 0.0, 0.2
        first_impression = 0.30*q_thumb + 0.70*q_first

    propensity = (
        0.30*first_impression + 0.30*q_caption + 0.20*overlap +
        0.10*base_eng + e_bonus + 0.10*v_bonus
    )
    propensity = min(0.97, max(0.03, propensity)) * t_mod

    like_p    = min(0.98, max(0.02, propensity * (1.00 + 0.06*random.gauss(0,0.6))))
    comment_p = min(0.90, max(0.01, propensity * (0.55 + 0.10*random.random())))
    share_p   = min(0.70, max(0.005,propensity * (0.40 + 0.15*random.random())))
    save_p    = min(0.85, max(0.01, propensity * (0.65 + 0.10*random.random()))) if platform.upper()=="IG" else 0.0

    like = 1 if random.random() < like_p else 0
    comment = 1 if random.random() < comment_p else 0
    share = 1 if random.random() < share_p else 0
    save = 1 if (platform.upper()=="IG" and random.random() < save_p) else 0

    vote_score = like_w*like_p + comment_w*comment_p + save_w*(save_p if platform.upper()=="IG" else 0) + share_w*share_p

    return {
        "like_p": like_p, "comment_p": comment_p, "share_p": share_p, "save_p": save_p,
        "like": like, "comment": comment, "share": share, "save": save,
        "vote_score": vote_score,
        "q_thumb": q_thumb, "q_caption": q_caption, "q_first": q_first, "overlap": overlap, "v_hits": v_hits
    }

def wilson_interval(phat, n, z=1.96):
    if n == 0: return (0.0, 1.0)
    low = (phat + z*z/(2*n) - z*math.sqrt((phat*(1-phat) + z*z/(4*n))/n)) / (1 + z*z/n)
    high = (phat + z*z/(2*n) + z*math.sqrt((phat*(1-phat) + z*z/(4*n))/n)) / (1 + z*z/n)
    return (low, high)

def run_simulation(postA, postB, platform, personas, rounds=3, seed=42):
    random.seed(seed)
    rows = []
    votes_A = votes_B = 0
    agg_A = {"like_p":0,"comment_p":0,"share_p":0,"save_p":0}
    agg_B = {"like_p":0,"comment_p":0,"share_p":0,"save_p":0}
    vmap = {"A":[], "B":[]}
    n_rows = 0

    for r in range(rounds):
        for p in personas:
            resA = simulate_interactions(postA, p, platform=platform)
            resB = simulate_interactions(postB, p, platform=platform)
            vote = "A" if resA["vote_score"] >= resB["vote_score"] else "B"
            if vote=="A": votes_A += 1
            else: votes_B += 1

            for k in agg_A.keys():
                agg_A[k] += resA[k]
                agg_B[k] += resB[k]
            vmap["A"].extend([x[0] for x in resA["v_hits"]])
            vmap["B"].extend([x[0] for x in resB["v_hits"]])
            n_rows += 1

            rows.append({
                "persona_id": p.get("id",""),
                "年齡段": p.get("年齡段",""),
                "興趣": ",".join(p.get("興趣",[])),
                "round": r+1,
                "vote": vote,
                "A_like_p": resA["like_p"], "A_comment_p": resA["comment_p"], "A_share_p": resA["share_p"], "A_save_p": resA["save_p"],
                "B_like_p": resB["like_p"], "B_comment_p": resB["comment_p"], "B_share_p": resB["share_p"], "B_save_p": resB["save_p"],
            })

    df = pd.DataFrame(rows)
    total = votes_A + votes_B
    a_ratio = votes_A / total if total>0 else 0.5
    b_ratio = 1 - a_ratio
    ci_low, ci_high = wilson_interval(a_ratio, total)

    # averages
    for k in agg_A.keys():
        agg_A[k] /= max(1,n_rows)
        agg_B[k] /= max(1,n_rows)

    # value cues top-5
    def top_cues(lst):
        from collections import Counter
        c = Counter(lst)
        return c.most_common(5)
    cues = {"A": top_cues(vmap["A"]), "B": top_cues(vmap["B"])}

    agg = {
        "votes_A": votes_A, "votes_B": votes_B,
        "vote_ratio_A": a_ratio, "vote_ratio_B": b_ratio,
        "wilson_95ci_A": [ci_low, ci_high],
        "platform": platform, "rounds": rounds, "personas": len(personas),
        "avg_A": agg_A, "avg_B": agg_B, "cues": cues
    }
    return df, agg
