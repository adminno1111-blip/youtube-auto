import os, json, time, random, asyncio, subprocess, datetime
import requests, edge_tts
from PIL import Image, ImageDraw, ImageFont

THEME = "শিক্ষামূলক ভিডিও — ইসলামিক ও সাধারণ জ্ঞান"
ISLAMIC_SHARE = 0.5   # ০.৫ মানে অর্ধেক ভিডিও ইসলামিক, অর্ধেক সাধারণ শিক্ষামূলক (০ থেকে ১ এর মধ্যে বদলাতে পারেন)
ISLAMIC_TOPICS = ["ইসলামের ইতিহাসের শিক্ষণীয় ঘটনা", "নবী-রাসূলদের জীবনের শিক্ষা",
                  "সাহাবীদের জীবনের অনুপ্রেরণামূলক ঘটনা", "রমজান ও রোজার উপকারিতা",
                  "ইসলামি আদব ও আখলাক", "মুসলিম বিজ্ঞানীদের অবদান",
                  "পবিত্র কুরআনের পরিচিতি ও ইতিহাস", "মসজিদ ও ইসলামি স্থাপত্য",
                  "হজ্জ ও ওমরাহর পরিচিতি", "ইসলামে জ্ঞান অর্জনের গুরুত্ব",
                  "ইসলামের স্বর্ণযুগ", "দৈনন্দিন জীবনে ভালো অভ্যাস"]
GENERAL_TOPICS = ["মহাকাশ", "মানবদেহ", "প্রাণীজগৎ", "ইতিহাসের আশ্চর্য ঘটনা", "পৃথিবীর ভূগোল",
                  "বিজ্ঞানের আবিষ্কার", "স্বাস্থ্য সচেতনতা", "প্রযুক্তি", "ইংরেজি শব্দ ও ভাষা শেখা",
                  "পরিবেশ ও প্রকৃতি", "মস্তিষ্ক ও মনোবিজ্ঞান", "বিখ্যাত মানুষদের শিক্ষণীয় জীবন",
                  "সময় ব্যবস্থাপনা ও পড়াশোনার কৌশল", "সাধারণ জ্ঞান"]
CTA = "ভিডিওটা ভালো লাগলে একটা লাইক দিন, আর চ্যানেলটা সাবস্ক্রাইব করে আমাদের পাশে থাকুন।"
TELEGRAM_LINK = "https://t.me/Online_Income_Tips001"   # এখানে আপনার টেলিগ্রাম চ্যানেলের লিংক বসান (কোটেশনের ভেতরে)
VOICE = "bn-BD-NabanitaNeural"
MODELS = ["gemini-3.8-flash", "gemini-flash-latest", "gemini-flash-lite-latest"]
PRIVACY = "public"
USED = "used_titles.txt"
W, H = 1080, 1920
WORK = "work"


def env(k):
    return os.environ[k]


def sh(cmd):
    try:
        return subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print((e.stderr or "")[-1500:])
        raise


def used_titles():
    open(USED, "a").close()
    with open(USED, encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip()]


def get_script():
    today = datetime.date.today().isoformat()
    islamic = random.random() < ISLAMIC_SHARE
    sub = random.choice(ISLAMIC_TOPICS if islamic else GENERAL_TOPICS)
    old = "\n".join(used_titles()[-40:]) or "নেই"
    if islamic:
        rules = """বিশেষ নিয়ম (ইসলামিক ভিডিও):
- কুরআনের আয়াত বা হাদিস নিজে বানিয়ে লিখবে না। উল্লেখ করতে হলে শুধু সুপরিচিত ও নিশ্চিত হলে লেখো এবং সূত্র (সূরার নাম ও আয়াত নম্বর বা হাদিসের গ্রন্থ) বলো। নিশ্চিত না হলে উদ্ধৃতি না দিয়ে ভাবার্থ ও ইতিহাস বলো।
- ফতোয়া, হালাল-হারামের রায় বা মাজহাব নিয়ে বিতর্ক দেবে না।
- নবী-রাসূল বা সাহাবীদের চেহারা বা ছবির বর্ণনা দেবে না।
- আরবি হরফ ব্যবহার করবে না, সব বাংলা হরফে লেখো।
- প্রথম দৃশ্য আসসালামু আলাইকুম দিয়ে শুরু করতে পারো।
- keyword এমন দেবে যাতে মসজিদ, কাবা, মরুভূমি, প্রকৃতি, আকাশ, বই, ক্যালিগ্রাফি ধরনের ছবি আসে (যেমন mosque architecture, kaaba, desert sunrise, old books)। মানুষের ছবি আসে এমন keyword দেবে না।"""
    else:
        rules = """বিশেষ নিয়ম (সাধারণ শিক্ষামূলক ভিডিও):
- তথ্য যাচাইযোগ্য ও সঠিক হতে হবে, নিশ্চিত না হলে সংখ্যা বা তারিখ বানাবে না।
- চিকিৎসা বা আর্থিক বিষয়ে সাধারণ সচেতনতামূলক তথ্য দেবে, ব্যক্তিগত পরামর্শ বা নিশ্চিত ফলের দাবি নয়।"""
    prompt = f"""তুমি একজন ইউটিউব শর্টস স্ক্রিপ্টরাইটার। ভিডিওটা স্থির ছবির স্লাইডশো, তাই প্রতিটা দৃশ্যের keyword এমন দেবে যাতে ভালো স্টক ছবি পাওয়া যায়। চ্যানেলের বিষয়: {THEME}। আজকের উপবিষয়: {sub}। তারিখ {today}।
এই উপবিষয়ে একটা একদম নতুন ও আকর্ষণীয় আইডিয়া বেছে সহজ বাংলায় ৪৫ সেকেন্ডের শিক্ষামূলক ভিডিও স্ক্রিপ্ট লেখো।
{rules}
নিচের শিরোনামগুলোর মতো বা একই বিষয়ের আইডিয়া দেবে না:
{old}
শুধু JSON দাও, এই ফরম্যাটে:
{{"title":"বাংলা শিরোনাম (৭০ অক্ষরের মধ্যে)","description":"২-৩ লাইনের বাংলা বর্ণনা","tags":["ট্যাগ১","ট্যাগ২"],"scenes":[{{"text":"১-২ ছোট বাক্যের বাংলা বর্ণনা","keyword":"english stock photo search words, 1-3 words"}}]}}
৬টা দৃশ্য দাও। প্রথম দৃশ্যে কৌতূহল জাগানো হুক। শেষ দৃশ্যে লাইক বা সাবস্ক্রাইবের কথা বলবে না, সেটা আলাদাভাবে যোগ হবে। শেষ দৃশ্য হবে মূল শিক্ষাটার সারকথা।"""
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json"}}
    for rnd in range(3):
        for m in MODELS:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={env('GEMINI_API_KEY')}"
            try:
                r = requests.post(url, json=body, timeout=120)
            except Exception as e:
                print("Request error", m, e)
                continue
            if r.status_code == 200:
                try:
                    text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                    text = text.strip().strip("`").replace("json\n", "", 1)
                    print("Model used:", m)
                    result = json.loads(text)
                    result["islamic"] = islamic
                    return result
                except Exception as e:
                    print("Parse error", m, e)
                    continue
            print("Gemini error", m, r.status_code, r.text[:200])
        time.sleep(45)
    raise SystemExit("Gemini failed")


async def tts(text, path):
    await edge_tts.Communicate(text, VOICE).save(path)


def make_voice(text, path):
    for _ in range(4):
        try:
            asyncio.run(tts(text, path))
            return
        except Exception as e:
            print("TTS error", e)
            time.sleep(5)
    raise SystemExit("TTS failed")


def duration(path):
    r = sh(["ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "csv=p=0", path])
    return float(r.stdout.strip())


def font_path():
    r = subprocess.run(["fc-match", "-f", "%{file}", "Noto Sans Bengali"],
                       capture_output=True, text=True)
    return r.stdout.strip()


def make_caption(text, path):
    font = ImageFont.truetype(font_path(), 64, layout_engine=ImageFont.Layout.RAQM)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= 900:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    lh = 100
    y0 = 1250
    d.rounded_rectangle([60, y0 - 30, W - 60, y0 + lh * len(lines) + 10], 30,
                        fill=(0, 0, 0, 160))
    for i, line in enumerate(lines):
        x = (W - d.textlength(line, font=font)) / 2
        d.text((x, y0 + i * lh), line, font=font, fill="white")
    img.save(path)


USED_PHOTOS = set()


def get_photo(keyword, idx):
    for q in (keyword, "nature"):
        try:
            r = requests.get("https://pixabay.com/api/",
                             params={"key": env("PIXABAY_API_KEY"), "q": q, "image_type": "photo",
                                     "orientation": "vertical", "safesearch": "true",
                                     "per_page": 20, "min_width": 720},
                             timeout=30).json()
            hits = r.get("hits", [])
            random.shuffle(hits)
            for h in hits:
                u = h.get("largeImageURL") or h.get("webformatURL")
                if not u or u in USED_PHOTOS:
                    continue
                p = f"{WORK}/photo{idx}.jpg"
                with open(p, "wb") as f:
                    f.write(requests.get(u, timeout=180).content)
                USED_PHOTOS.add(u)
                return p
        except Exception as e:
            print("Pixabay error", e)
    return None


def build_scene(photo, cap, audio, dur, out, idx=0):
    frames = int(dur * 30) + 1
    if photo:
        mode = idx % 3
        if mode == 0:      # ধীরে জুম-ইন
            z, x, y = f"1+0.25*on/{frames}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
        elif mode == 1:    # ধীরে জুম-আউট
            z, x, y = f"1.25-0.25*on/{frames}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
        else:              # বাঁ থেকে ডানে প্যান
            z, x, y = "1.2", f"(iw-iw/zoom)*on/{frames}", "ih/2-(ih/zoom/2)"
        vf = (f"[0:v]scale=1620:2880:force_original_aspect_ratio=increase,crop=1620:2880,"
              f"zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s={W}x{H}:fps=30,setsar=1[bg];"
              f"[bg][1:v]overlay=0:0:shortest=1[v]")
        src = ["-i", photo]
    else:
        src = ["-f", "lavfi", "-i", f"color=c=0x16213e:s={W}x{H}:r=30"]
        vf = "[0:v]setsar=1[bg];[bg][1:v]overlay=0:0:shortest=1[v]"
    sh(["ffmpeg", "-y", *src, "-loop", "1", "-i", cap, "-i", audio,
        "-filter_complex", vf, "-map", "[v]", "-map", "2:a", "-af", "apad",
        "-t", str(dur), "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "48000", "-ac", "2", out])


def upload(path, data):
    tok = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": env("YT_CLIENT_ID"), "client_secret": env("YT_CLIENT_SECRET"),
        "refresh_token": env("YT_REFRESH_TOKEN"), "grant_type": "refresh_token"},
        timeout=30).json()
    if "access_token" not in tok:
        raise SystemExit(f"Token error: {tok}")
    title = data["title"][:90] + " #Shorts"
    meta = {"snippet": {"title": title,
                        "description": data["description"] + "\n\n#Shorts",
                        "tags": data.get("tags", [])[:15], "categoryId": "27",
                        "defaultLanguage": "bn", "defaultAudioLanguage": "bn"},
            "status": {"privacyStatus": PRIVACY, "selfDeclaredMadeForKids": False}}
    h = {"Authorization": "Bearer " + tok["access_token"],
         "Content-Type": "application/json; charset=UTF-8",
         "X-Upload-Content-Type": "video/mp4"}
    r = requests.post("https://www.googleapis.com/upload/youtube/v3/videos"
                      "?uploadType=resumable&part=snippet,status",
                      headers=h, data=json.dumps(meta), timeout=60)
    if r.status_code != 200:
        raise SystemExit(f"Init error: {r.status_code} {r.text}")
    with open(path, "rb") as f:
        r2 = requests.put(r.headers["Location"], data=f,
                          headers={"Content-Type": "video/mp4"}, timeout=600)
    print("Upload:", r2.status_code, r2.text[:300])
    if r2.status_code not in (200, 201):
        raise SystemExit("Upload failed")


def upload_facebook(path, data):
    pid = os.environ.get("FB_PAGE_ID", "").strip()
    tok = os.environ.get("FB_PAGE_TOKEN", "").strip()
    if not pid or not tok:
        print("Facebook: চাবি সেট করা নেই, বাদ দেওয়া হলো")
        return None
    g = "https://graph.facebook.com/v26.0"
    r = requests.post(f"{g}/{pid}/video_reels",
                      json={"upload_phase": "start", "access_token": tok}, timeout=60)
    j = r.json()
    if "video_id" not in j:
        print("FB start error:", r.status_code, r.text[:500])
        return False
    vid = j["video_id"]
    url = j.get("upload_url") or f"https://rupload.facebook.com/video-upload/v26.0/{vid}"
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        r2 = requests.post(url, headers={"Authorization": "OAuth " + tok,
                                         "offset": "0", "file_size": str(size),
                                         "Content-Type": "application/octet-stream"},
                           data=f, timeout=900)
    print("FB upload:", r2.status_code, r2.text[:300])
    if r2.status_code != 200:
        return False
    desc = data["title"] + "\n\n" + data["description"] + "\n\n#Reels"
    for attempt in range(6):
        time.sleep(10)
        r3 = requests.post(f"{g}/{pid}/video_reels",
                           params={"access_token": tok, "video_id": vid,
                                   "upload_phase": "finish", "video_state": "PUBLISHED",
                                   "description": desc, "title": data["title"][:90],
                                   "is_ai_generated": "true"}, timeout=120)
        print("FB publish:", r3.status_code, r3.text[:300])
        if r3.status_code == 200 and r3.json().get("success"):
            return True
    return False


def upload_instagram(path, data):
    uid = os.environ.get("IG_USER_ID", "").strip()
    tok = (os.environ.get("IG_ACCESS_TOKEN", "").strip()
           or os.environ.get("FB_PAGE_TOKEN", "").strip())
    if not uid or not tok:
        print("Instagram: চাবি সেট করা নেই, বাদ দেওয়া হলো")
        return None
    g = "https://graph.facebook.com/v26.0"
    caption = (data["title"] + "\n\n" + data["description"] + "\n\n#Reels")[:2000]
    r = requests.post(f"{g}/{uid}/media",
                      data={"media_type": "REELS", "upload_type": "resumable",
                            "caption": caption, "access_token": tok}, timeout=60)
    j = r.json()
    if "id" not in j:
        print("IG container error:", r.status_code, r.text[:500])
        return False
    cid = j["id"]
    u = j.get("uri", "")
    url = u if u.startswith("http") else f"https://rupload.facebook.com/ig-api-upload/v26.0/{cid}"
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        r2 = requests.post(url, headers={"Authorization": "OAuth " + tok,
                                         "offset": "0", "file_size": str(size)},
                           data=f, timeout=900)
    print("IG upload:", r2.status_code, r2.text[:300])
    if r2.status_code != 200:
        return False
    for _ in range(30):   # সর্বোচ্চ প্রায় ৫ মিনিট অপেক্ষা
        time.sleep(10)
        st = requests.get(f"{g}/{cid}", params={"fields": "status_code", "access_token": tok},
                          timeout=60).json()
        code = st.get("status_code")
        print("IG status:", code)
        if code == "FINISHED":
            break
        if code in ("ERROR", "EXPIRED"):
            print(st)
            return False
    else:
        return False
    r3 = requests.post(f"{g}/{uid}/media_publish",
                       data={"creation_id": cid, "access_token": tok}, timeout=120)
    print("IG publish:", r3.status_code, r3.text[:300])
    return r3.status_code == 200 and "id" in r3.json()


def main():
    os.makedirs(WORK, exist_ok=True)
    data = get_script()
    print("Title:", data["title"])
    data["scenes"].append({"text": CTA,
                           "keyword": "mosque sunset" if data.get("islamic") else "sky clouds"})
    data["description"] = data["description"] + "\n\nভিডিওটা ভালো লাগলে লাইক করুন ও চ্যানেল সাবস্ক্রাইব করুন।"
    if TELEGRAM_LINK and "আপনার" not in TELEGRAM_LINK:
        data["description"] += "\n\nআমাদের টেলিগ্রাম চ্যানেলে জয়েন করুন: " + TELEGRAM_LINK
    names = []
    for i, sc in enumerate(data["scenes"]):
        audio, cap, out = f"{WORK}/a{i}.mp3", f"{WORK}/c{i}.png", f"{WORK}/s{i}.mp4"
        make_voice(sc["text"], audio)
        make_caption(sc["text"], cap)
        photo = get_photo(sc.get("keyword", "nature"), i)
        build_scene(photo, cap, audio, round(duration(audio) + 0.5, 2), out, i)
        names.append(f"s{i}.mp4")
    with open(f"{WORK}/list.txt", "w") as f:
        f.write("\n".join(f"file '{n}'" for n in names))
    final = f"{WORK}/final.mp4"
    sh(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", f"{WORK}/list.txt",
        "-c", "copy", "-movflags", "+faststart", final])
    yt_ok = False
    try:
        upload(final, data)
        yt_ok = True
    except (Exception, SystemExit) as e:
        print("YouTube আপলোড ব্যর্থ:", e)
    fb_ok = None
    try:
        fb_ok = upload_facebook(final, data)
    except Exception as e:
        print("Facebook আপলোড ব্যর্থ:", e)
        fb_ok = False
    ig_ok = None
    try:
        ig_ok = upload_instagram(final, data)
    except Exception as e:
        print("Instagram আপলোড ব্যর্থ:", e)
        ig_ok = False
    print("ফলাফল -> YouTube:", yt_ok, "| Facebook:", fb_ok, "| Instagram:", ig_ok)
    if not (yt_ok or fb_ok or ig_ok):
        raise SystemExit("কোথাও আপলোড হয়নি")
    with open(USED, "a", encoding="utf-8") as f:
        f.write(data["title"].replace("\n", " ") + "\n")


main()
