import os, io, re, json, time, math, random, subprocess, functools
import requests
from PIL import Image, ImageDraw, ImageFont

# main.py থেকে আপলোড, কণ্ঠ ও সাধারণ ফাংশনগুলো ধার নেওয়া হচ্ছে (main.py বদলাতে হবে না)
_src = open("main.py", encoding="utf-8").read().rsplit("\nmain()", 1)[0]
B = {"__name__": "base_main"}
exec(compile(_src, "main.py", "exec"), B)

CHANNEL_NAME = "মহাবিশ্বের রহস্য ০.১"   # এখানে আপনার চ্যানেলের নাম লিখুন (শেষের কার্ডে ও ছবির পেছনে বসবে)
MAX_BODY = 78      # মূল অংশ সর্বোচ্চ কত সেকেন্ড (শেষ কার্ডসহ মোট প্রায় ৮৫ সেকেন্ডের মধ্যে থাকবে)
W, H, FPS = 720, 1280, 15
WORK = "cwork"
UA = {"User-Agent": "BanglaCompareVideoBot/1.0 (educational project; GitHub Actions)"}
CATEGORIES = ["বিজ্ঞান", "প্রযুক্তি ও কম্পিউটার", "প্রাণী ও পাখি", "উদ্ভিদ ও ফল", "মহাকাশ", "ইতিহাস",
              "দেশ ও শহর", "স্বাস্থ্য ও খাবার", "ইসলামি জ্ঞান (শুধু সুনির্দিষ্ট ও নিশ্চিত তথ্য)",
              "অর্থ ও ব্যবসার সহজ ধারণা", "খেলাধুলা", "ভাষা ও সাহিত্য", "যানবাহন ও যন্ত্র",
              "প্রকৃতি ও আবহাওয়া"]


def has_channel():
    return bool(CHANNEL_NAME) and "আপনার" not in CHANNEL_NAME


def has_telegram():
    t = B["https://t.me/Online_Income_Tips001"]
    return bool(t) and "আপনার" not in t


# ---------- ফন্ট ও লেখা ----------
@functools.lru_cache(None)
def bn_font(size):
    path = os.environ.get("FONT_PATH") or subprocess.run(
        ["fc-match", "-f", "%{file}", "Noto Sans Bengali"], capture_output=True, text=True).stdout.strip()
    return ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM)


_d0 = ImageDraw.Draw(Image.new("RGB", (4, 4)))


def wrap(text, font, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if _d0.textlength(t, font=font) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_lines(d, lines, font, cx, top, fill, lh, stroke=0, stroke_fill=None):
    for i, l in enumerate(lines):
        w = _d0.textlength(l, font=font)
        d.text((cx - w / 2, top + i * lh), l, font=font, fill=fill,
               stroke_width=stroke, stroke_fill=stroke_fill)


def fit_font(text, maxw, start, minsize=22):
    s = start
    while s > minsize and _d0.textlength(text, font=bn_font(s)) > maxw:
        s -= 2
    return bn_font(s)


# ---------- স্টিকম্যান শিক্ষক (নিজস্ব আঁকা) ----------
@functools.lru_cache(None)
def stick_sprite(pose, mouth):
    S = 2
    im = Image.new("RGBA", (400 * S, 640 * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    K = (25, 25, 25, 255)
    LW = 9 * S
    def P(x, y): return (x * S, y * S)
    def line(pts, w=LW): d.line([P(*p) for p in pts], fill=K, width=w, joint="curve")
    def hand(x, y):
        d.ellipse([P(x - 11, y - 11), P(x + 11, y + 11)], fill=(255, 255, 255, 255), outline=K, width=5 * S)
    # পা
    line([(200, 380), (150, 610)]); line([(200, 380), (250, 610)])
    d.ellipse([P(118, 598), P(176, 632)], fill=K); d.ellipse([P(224, 598), P(282, 632)], fill=K)
    # শরীর, টাই
    d.polygon([P(165, 208), P(235, 208), P(228, 380), P(172, 380)], fill=(255, 255, 255, 255), outline=K, width=6 * S)
    d.polygon([P(200, 214), P(189, 240), P(200, 294), P(211, 240)], fill=(37, 99, 235, 255), outline=K)
    line([(200, 208), (184, 223)], 4 * S); line([(200, 208), (216, 223)], 4 * S)
    # মাথা
    d.ellipse([P(130, 50), P(270, 190)], fill=(255, 255, 255, 255), outline=K, width=LW)
    for a, b in (((190, 54), (172, 30)), ((204, 52), (214, 26)), ((220, 56), (244, 38))):
        line([a, b], 6 * S)
    for cx in (172, 228):
        d.ellipse([P(cx - 21, 97), P(cx + 21, 139)], outline=K, width=5 * S)
        d.ellipse([P(cx - 5, 113), P(cx + 5, 123)], fill=K)
    line([(193, 118), (207, 118)], 4 * S)
    if mouth:
        d.ellipse([P(184, 146), P(216, 172)], fill=(40, 40, 40, 255))
        d.ellipse([P(192, 160), P(208, 172)], fill=(220, 80, 90, 255))
    else:
        d.arc([P(178, 136), P(222, 168)], 20, 160, fill=K, width=5 * S)
    # হাত ও বই
    BOOK = (234, 122, 36, 255)
    if pose == 0:   # ডান হাতে পয়েন্টার, বাঁ হাতে বই
        line([(230, 225), (285, 245), (318, 180)]); hand(318, 180)
        d.line([P(318, 180), P(372, 112)], fill=(120, 80, 40, 255), width=5 * S)
        for a, b in (((380, 96), (392, 80)), ((384, 112), (398, 108)), ((372, 96), (374, 78))):
            line([a, b], 4 * S)
        line([(170, 225), (120, 262), (96, 300)])
        d.polygon([P(40, 262), P(100, 248), P(128, 318), P(66, 332)], fill=BOOK, outline=K, width=5 * S)
        hand(96, 300)
    elif pose == 1:  # দুই হাতে বুকের কাছে বই
        line([(170, 225), (150, 285), (185, 318)]); line([(230, 225), (250, 285), (215, 318)])
        d.rectangle([P(150, 288), P(250, 348)], fill=BOOK, outline=K, width=5 * S)
        line([(200, 288), (200, 348)], 4 * S)
        hand(185, 318); hand(215, 318)
    else:            # ভাবনার ভঙ্গি
        line([(230, 225), (268, 240), (238, 186)]); hand(238, 186)
        line([(170, 225), (135, 285), (120, 340)]); hand(120, 340)
        d.polygon([P(66, 336), P(132, 326), P(140, 388), P(74, 398)], fill=BOOK, outline=K, width=5 * S)
        for (x, y, s) in ((300, 40, 1.0), (345, 95, 0.7)):
            d.arc([P(x, y), P(x + 50 * s, y + 50 * s)], 200, 70, fill=K, width=int(7 * S * s))
            line([(x + 25 * s, y + 46 * s), (x + 25 * s, y + 62 * s)], int(7 * s))
            d.ellipse([P(x + 20 * s, y + 72 * s), P(x + 32 * s, y + 84 * s)], fill=K)
    return im.resize((400, 640), Image.LANCZOS)


@functools.lru_cache(None)
def small_sprite(pose, mouth):
    return stick_sprite(pose, mouth).resize((280, 448), Image.LANCZOS)


# ---------- ছবি সংগ্রহ ----------
def ok_license(s):
    s = (s or "").lower()
    if re.search(r"-(sa|nc|nd)\b", s) or "gfdl" in s or "fair" in s:
        return False
    return "public domain" in s or s.startswith("pd") or "cc0" in s or s.startswith("cc by") or "cc-by" in s


def commons_photo(query):
    try:
        r = requests.get("https://commons.wikimedia.org/w/api.php", headers=UA, timeout=30, params={
            "action": "query", "format": "json", "generator": "search",
            "gsrsearch": query + " filetype:bitmap", "gsrnamespace": 6, "gsrlimit": 20,
            "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata", "iiurlwidth": 800}).json()
        pages = list((r.get("query") or {}).get("pages", {}).values())
        random.shuffle(pages)
        for pg in pages:
            ii = (pg.get("imageinfo") or [None])[0]
            if not ii or ii.get("mime") not in ("image/jpeg", "image/png") or ii.get("width", 0) < 500:
                continue
            md = ii.get("extmetadata", {})
            lic = md.get("LicenseShortName", {}).get("value", "")
            if not ok_license(lic):
                continue
            data = requests.get(ii.get("thumburl") or ii["url"], headers=UA, timeout=60).content
            img = Image.open(io.BytesIO(data)).convert("RGB")
            artist = re.sub(r"<[^>]+>", "", md.get("Artist", {}).get("value", "")).strip()[:60]
            title = pg.get("title", "").replace("File:", "")[:60]
            return img, f"{title} — {artist or 'অজানা'} ({lic}), Wikimedia Commons"
    except Exception as e:
        print("Commons error:", e)
    return None, ""


def pixabay_photo(query):
    try:
        r = requests.get("https://pixabay.com/api/", timeout=30, params={
            "key": B["env"]("PIXABAY_API_KEY"), "q": query, "image_type": "photo",
            "safesearch": "true", "per_page": 20}).json()
        hits = r.get("hits", [])
        random.shuffle(hits)
        for h in hits:
            u = h.get("webformatURL")
            if u:
                img = Image.open(io.BytesIO(requests.get(u, timeout=60).content)).convert("RGB")
                return img, ""
    except Exception as e:
        print("Pixabay error:", e)
    return None, ""


def get_image(query):
    for fn in (commons_photo, pixabay_photo):
        img, credit = fn(query)
        if img:
            return img, credit
    return None, ""


def tile(img, name, w, h, color):
    if img is None:
        t = Image.new("RGB", (w, h), color)
        d = ImageDraw.Draw(t)
        f = fit_font(name, w - 30, 44)
        draw_lines(d, wrap(name, f, w - 30), f, w / 2, h / 2 - 30, (255, 255, 255), 60)
        return t
    iw, ih = img.size
    s = max(w / iw, h / ih)
    img = img.resize((int(iw * s) + 1, int(ih * s) + 1), Image.LANCZOS)
    x, y = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((x, y, x + w, y + h))


# ---------- ছবির কাঠামো ----------
def make_bg(nameA, nameB, imgA, imgB):
    f = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(f)
    if has_channel():
        wf = fit_font(CHANNEL_NAME, 560, 78)
        draw_lines(d, wrap(CHANNEL_NAME, wf, 560), wf, W / 2, 800, (238, 238, 243), 100)
    for cx, name in ((184, nameA), (536, nameB)):
        lf = fit_font(name, 336, 46)
        draw_lines(d, [name], lf, cx, 96, (255, 214, 0), 60, stroke=4, stroke_fill=(0, 0, 0))
    f.paste(tile(imgA, nameA, 350, 300, (30, 120, 90)), (8, 160))
    f.paste(tile(imgB, nameB, 350, 300, (150, 60, 60)), (362, 160))
    d.ellipse([320, 280, 400, 340], fill=(220, 30, 60), outline=(255, 255, 255), width=4)
    vf = bn_font(34)
    d.text((360 - _d0.textlength("VS", font=vf) / 2, 285), "VS", font=vf, fill=(255, 255, 255), stroke_width=1, stroke_fill=(255, 255, 255))
    return f


def seg_base(bg, text):
    f = bg.copy()
    d = ImageDraw.Draw(f)
    font = bn_font(42)
    lines = wrap(text, font, 650)
    lh = 58
    top = 560 - len(lines) * lh / 2
    draw_lines(d, lines, font, W / 2, top, (20, 20, 20), lh, stroke=1, stroke_fill=(20, 20, 20))
    return f


def end_base():
    f = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(f)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(250 - 30 * t), int(245 - 40 * t), int(255 - 10 * t)))
    d.rounded_rectangle([40, 120, W - 40, 560], 40, fill=(255, 255, 255), outline=(30, 30, 60), width=5)
    f1, f2 = bn_font(50), bn_font(62)
    draw_lines(d, ["এমন আরও"], f1, W / 2, 170, (30, 30, 60), 70, stroke=1, stroke_fill=(30, 30, 60))
    draw_lines(d, ["তথ্য জানতে"], f2, W / 2, 245, (230, 40, 70), 80, stroke=2, stroke_fill=(230, 40, 70))
    draw_lines(d, ["আমাদের সাথেই থাকুন"], f1, W / 2, 335, (30, 30, 60), 70, stroke=1, stroke_fill=(30, 30, 60))
    d.rounded_rectangle([210, 440, 510, 520], 40, fill=(230, 40, 70))
    ff = bn_font(40)
    draw_lines(d, ["Follow"], ff, W / 2, 455, (255, 255, 255), 56, stroke=1, stroke_fill=(255, 255, 255))
    sf = bn_font(34)
    draw_lines(d, ["লাইক  •  সাবস্ক্রাইব  •  শেয়ার"], sf, W / 2, 590, (60, 60, 90), 48)
    if has_channel():
        nf = fit_font(CHANNEL_NAME, 340, 50)
        draw_lines(d, wrap(CHANNEL_NAME, nf, 340), nf, 530, 860, (30, 30, 60), 64, stroke=1, stroke_fill=(30, 30, 60))
    if has_telegram():
        tf = bn_font(26)
        draw_lines(d, wrap("টেলিগ্রাম: " + B["TELEGRAM_LINK"], tf, 340), tf, 530, 1040, (60, 60, 90), 38)
    return f


# ---------- স্ক্রিপ্ট ----------
def ask_gemini(prompt):
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json"}}
    for rnd in range(3):
        for m in B["MODELS"]:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={B['env']('GEMINI_API_KEY')}"
            try:
                r = requests.post(url, json=body, timeout=120)
                if r.status_code == 200:
                    text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                    j = json.loads(text.strip().strip("`").replace("json\n", "", 1))
                    print("Model used:", m)
                    return j
                print("Gemini error", m, r.status_code, r.text[:200])
            except Exception as e:
                print("Gemini problem", m, e)
        time.sleep(45)
    return None


def get_plan():
    cat = random.choice(CATEGORIES)
    old = "\n".join(B["used_titles"]()[-50:]) or "নেই"
    prompt = f"""তুমি বাংলা শিক্ষামূলক "পার্থক্য" ভিডিওর স্ক্রিপ্টরাইটার। ভিডিওতে দুটো জিনিসের তুলনা হবে, দুই পাশে দুটো ছবি থাকবে। বিভাগ: {cat}।
নিয়ম:
- এমন দুটো জিনিস বাছো যেগুলোর ছবি ইন্টারনেটে সহজে পাওয়া যায় এবং যাদের মধ্যে সত্যিকারের পার্থক্য আছে।
- তথ্য সঠিক ও যাচাইযোগ্য হতে হবে, নিশ্চিত না হলে সংখ্যা বা তারিখ বানাবে না।
- রাজনৈতিক, সাম্প্রদায়িক, মাজহাবি বা বিতর্কিত তুলনা দেবে না। অস্ত্র বানানোর কোনো তথ্য দেবে না। স্বাস্থ্য বিষয়ে ব্যক্তিগত চিকিৎসা-পরামর্শ দেবে না।
- নিচের শিরোনামগুলোর মতো বা একই জুটি দেবে না:
{old}
শুধু JSON দাও:
{{"a":"প্রথম জিনিসের বাংলা নাম (২-৪ শব্দ)","b":"দ্বিতীয় জিনিসের বাংলা নাম","qa":"ছবি খোঁজার ইংরেজি শব্দ (প্রথম জিনিস)","qb":"ছবি খোঁজার ইংরেজি শব্দ (দ্বিতীয় জিনিস)","title":"বাংলা শিরোনাম, যেমন 'A ও B-এর পার্থক্য কী?' (৭০ অক্ষরের মধ্যে)","description":"২-৩ লাইনের বাংলা বর্ণনা","tags":["ট্যাগ১","ট্যাগ২"],"sentences":["..."]}}
sentences-এ ১৪ থেকে ১৮টা ছোট বাক্য দাও, প্রতিটা ৭০ অক্ষরের মধ্যে, সহজ বাংলায়, ক্রম এরকম:
১) কৌতূহল জাগানো ভূমিকা যেখানে দুটো নামই আছে, ২) প্রথম জিনিসটা কী, ৩) দ্বিতীয় জিনিসটা কী, ৪) তারপর ছয় থেকে আটটা পার্থক্য (সংজ্ঞা, গঠন বা উপাদান, কাজ বা ব্যবহার, সুবিধা-অসুবিধা, উদাহরণ ইত্যাদি), প্রতিটা এক বাক্যে 'প্রথমটায় ..., কিন্তু দ্বিতীয়টায় ...' ধাঁচে, নাম ধরে বলবে, ৫) শেষ বাক্য সারকথা।
শেষ বাক্যে লাইক বা সাবস্ক্রাইবের কথা বলবে না, সেটা আলাদা যোগ হবে।"""
    j = ask_gemini(prompt)
    if not j or not j.get("sentences") or not j.get("a") or not j.get("b"):
        raise SystemExit("Gemini থেকে স্ক্রিপ্ট পাওয়া যায়নি")
    return j


# ---------- ভিডিও বানানো ----------
def make_compare():
    os.makedirs(WORK, exist_ok=True)
    plan = get_plan()
    print("Title:", plan["title"])
    sentences = [s.strip() for s in plan["sentences"] if isinstance(s, str) and s.strip()][:20]
    imgA, credA = get_image(plan.get("qa") or plan["a"])
    imgB, credB = get_image(plan.get("qb") or plan["b"])
    print("ছবি পাওয়া গেছে:", imgA is not None, imgB is not None)
    segs = []
    for i, s in enumerate(sentences):
        mp, wav = f"{WORK}/s{i}.mp3", f"{WORK}/s{i}.wav"
        B["make_voice"](s, mp)
        B["sh"](["ffmpeg", "-y", "-i", mp, "-af", "apad=pad_dur=0.35", "-ar", "48000", "-ac", "2", wav])
        total = B["duration"](wav)
        segs.append({"text": s, "wav": wav, "dur": total, "speech": max(0.5, total - 0.35), "end": False})
    while sum(s["dur"] for s in segs) > MAX_BODY and len(segs) > 8:
        segs.pop(len(segs) // 2)      # মাঝখান থেকে একটা বাক্য বাদ
    mp, wav = f"{WORK}/end.mp3", f"{WORK}/end.wav"
    B["make_voice"](B["CTA"], mp)
    B["sh"](["ffmpeg", "-y", "-i", mp, "-af", "apad=pad_dur=1.2", "-ar", "48000", "-ac", "2", wav])
    total = B["duration"](wav)
    segs.append({"text": B["CTA"], "wav": wav, "dur": total, "speech": max(0.5, total - 1.2), "end": True})
    with open(f"{WORK}/alist.txt", "w") as f:
        f.write("\n".join(f"file '{os.path.basename(s['wav'])}'" for s in segs))
    B["sh"](["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", f"{WORK}/alist.txt", "-c", "copy", f"{WORK}/full.wav"])

    bg = make_bg(plan["a"], plan["b"], imgA, imgB)
    bases = [end_base() if s["end"] else seg_base(bg, s["text"]) for s in segs]
    final = f"{WORK}/final.mp4"
    cmd = ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", f"{WORK}/full.wav", "-vf", "fps=30", "-c:v", "libx264", "-preset", "veryfast",
           "-crf", "22", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
           "-shortest", "-movflags", "+faststart", final]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=open(f"{WORK}/ffmpeg.log", "w"))
    frame_no, cum = 0, 0.0
    for si, seg in enumerate(segs):
        start_t = cum
        cum += seg["dur"]
        end_frame = int(round(cum * FPS))
        while frame_no < end_frame:
            t = frame_no / FPS - start_t
            mouth = 1 if (t < seg["speech"] and (frame_no // 2) % 2 == 0) else 0
            pose = 1 if seg["end"] else (2 if si == 0 else si % 3)
            fr = bases[si].copy()
            bob = int(5 * math.sin(frame_no / FPS * 2 * math.pi * 0.8))
            if seg["end"]:
                spr = small_sprite(pose, mouth)
                fr.paste(spr, (30, 800 + bob), spr)
            else:
                spr = stick_sprite(pose, mouth)
                fr.paste(spr, (160, 640 + bob), spr)
            p.stdin.write(fr.tobytes())
            frame_no += 1
    p.stdin.close()
    p.wait()
    if p.returncode != 0:
        print(open(f"{WORK}/ffmpeg.log").read()[-1500:])
        raise SystemExit("ভিডিও রেন্ডার ব্যর্থ")

    desc = plan.get("description", "") + "\n\nভিডিওটা ভালো লাগলে লাইক করুন ও চ্যানেল সাবস্ক্রাইব করুন।"
    if has_telegram():
        desc += "\n\nআমাদের টেলিগ্রাম চ্যানেলে জয়েন করুন: " + B["TELEGRAM_LINK"]
    credits = [c for c in (credA, credB) if c]
    if credits:
        desc += "\n\nছবির সূত্র:\n" + "\n".join(credits)
    return final, {"title": plan["title"], "description": desc, "tags": plan.get("tags", []),
                   "category": "27", "ai": True}


def main():
    final, data = make_compare()
    yt_ok = False
    try:
        B["upload"](final, data)
        yt_ok = True
    except (Exception, SystemExit) as e:
        print("YouTube আপলোড ব্যর্থ:", e)
    fb_ok = None
    try:
        fb_ok = B["upload_facebook"](final, data)
    except Exception as e:
        print("Facebook আপলোড ব্যর্থ:", e)
        fb_ok = False
    ig_ok = None
    try:
        ig_ok = B["upload_instagram"](final, data)
    except Exception as e:
        print("Instagram আপলোড ব্যর্থ:", e)
        ig_ok = False
    print("ফলাফল -> YouTube:", yt_ok, "| Facebook:", fb_ok, "| Instagram:", ig_ok)
    if not (yt_ok or fb_ok or ig_ok):
        raise SystemExit("কোথাও আপলোড হয়নি")
    with open(B["USED"], "a", encoding="utf-8") as f:
        f.write(data["title"].replace("\n", " ") + "\n")


if __name__ == "__main__":
    main()
