import os, json, time, random, asyncio, subprocess, datetime
import requests, edge_tts
from PIL import Image, ImageDraw, ImageFont

THEME = "মজার বৈজ্ঞানিক তথ্য"  # মহাবিশ্বের রহস্য ০.১
SUBTOPICS = ["মহাকাশ", "মানবদেহ", "প্রাণীজগৎ", "সমুদ্র", "উদ্ভিদ",
             "আবহাওয়া", "পদার্থবিজ্ঞান", "রসায়ন", "প্রযুক্তি", "ডাইনোসর",
             "মস্তিষ্ক", "খাবারের বিজ্ঞান", "পৃথিবীর রহস্য", "আবিষ্কার"]
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
    sub = random.choice(SUBTOPICS)
    old = "\n".join(used_titles()[-40:]) or "নেই"
    prompt = f"""তুমি একজন ইউটিউব শর্টস স্ক্রিপ্টরাইটার। চ্যানেলের বিষয়: {THEME}। আজকের উপবিষয়: {sub}। তারিখ {today}।
এই উপবিষয়ে একটা একদম নতুন ও আকর্ষণীয় আইডিয়া বেছে বাংলায় ৪০ সেকেন্ডের ভিডিও স্ক্রিপ্ট লেখো।
নিচের শিরোনামগুলোর মতো বা একই বিষয়ের আইডিয়া দেবে না:
{old}
শুধু JSON দাও, এই ফরম্যাটে:
{{"title":"বাংলা শিরোনাম (৭০ অক্ষরের মধ্যে)","description":"২-৩ লাইনের বাংলা বর্ণনা","tags":["ট্যাগ১","ট্যাগ২"],"scenes":[{{"text":"১-২ ছোট বাক্যের বাংলা বর্ণনা","keyword":"english stock video search words, 1-3 words"}}]}}
৬টা দৃশ্য দাও। প্রথম দৃশ্যে কৌতূহল জাগানো হুক, শেষ দৃশ্যে ফলো করার আহ্বান। তথ্য অবশ্যই সঠিক হতে হবে।"""
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
                    return json.loads(text)
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


def get_clip(keyword, idx):
    for q in (keyword, "nature"):
        try:
            r = requests.get("https://pixabay.com/api/videos/",
                             params={"key": env("PIXABAY_API_KEY"), "q": q,
                                     "per_page": 10, "safesearch": "true"},
                             timeout=30).json()
            hits = r.get("hits", [])
            random.shuffle(hits)
            for h in hits:
                for size in ("large", "medium"):
                    u = h["videos"].get(size, {}).get("url")
                    if u:
                        p = f"{WORK}/clip{idx}.mp4"
                        with open(p, "wb") as f:
                            f.write(requests.get(u, timeout=180).content)
                        return p
        except Exception as e:
            print("Pixabay error", e)
    return None


def build_scene(clip, cap, audio, dur, out):
    if clip:
        src = ["-stream_loop", "-1", "-i", clip]
    else:
        src = ["-f", "lavfi", "-i", f"color=c=0x16213e:s={W}x{H}:r=30"]
    vf = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
          f"crop={W}:{H},fps=30,setsar=1[bg];[bg][1:v]overlay=0:0[v]")
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
                        "tags": data.get("tags", [])[:15], "categoryId": "27"},
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


def main():
    os.makedirs(WORK, exist_ok=True)
    data = get_script()
    print("Title:", data["title"])
    names = []
    for i, sc in enumerate(data["scenes"]):
        audio, cap, out = f"{WORK}/a{i}.mp3", f"{WORK}/c{i}.png", f"{WORK}/s{i}.mp4"
        make_voice(sc["text"], audio)
        make_caption(sc["text"], cap)
        clip = get_clip(sc.get("keyword", "nature"), i)
        build_scene(clip, cap, audio, round(duration(audio) + 0.5, 2), out)
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
    print("ফলাফল -> YouTube:", yt_ok, "| Facebook:", fb_ok)
    if not yt_ok and not fb_ok:
        raise SystemExit("কোথাও আপলোড হয়নি")
    with open(USED, "a", encoding="utf-8") as f:
        f.write(data["title"].replace("\n", " ") + "\n")


main()
