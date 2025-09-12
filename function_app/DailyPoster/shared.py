import os, io, textwrap, datetime, requests
from typing import Tuple, List
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from PIL import Image, ImageDraw, ImageFont
from openai import OpenAI

# ---------- Configuration ----------
ACCOUNT_ENV = os.getenv("QBD_STORAGE_ACCOUNT")
CONTAINER = os.getenv("QBD_CAROUSEL_CONTAINER", "carousels")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
IG_USER_ID = os.getenv("IG_USER_ID")
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")

# Azure clients
_credential = DefaultAzureCredential(exclude_interactive_browser_credential=False)
_blob_svc = BlobServiceClient(account_url=f"https://{ACCOUNT_ENV}.blob.core.windows.net", credential=_credential)

# OpenAI client
_oai = OpenAI(api_key=OPENAI_API_KEY)

# ---------- Content Generation ----------

SYSTEM_PROMPT = '''You are QuantumBitesDaily, a friendly science communicator.
Audience: curious adults scrolling Instagram. Tone: snappy, accurate, playful.
Write:
- Slide 1: a 6-10 word hook title + 1-sentence teaser.
- Slide 2: 3 concise bullets with concrete facts and numbers if relevant.
- Slide 3 (CTA): one sentence to follow @QuantumBitesDaily + emoji + tease tomorrow's bite.
Keep it 100-140 words total across slides. Avoid jargon; define terms in-line.
'''

def generate_copy(topic_hint: str=None) -> dict:
    today = datetime.date.today().strftime("%B %d, %Y")
    user_prompt = f"Create today's 3-slide copy for {today}. Theme: physics + space. If you pick a phenomenon, include a stat and why it matters."
    if topic_hint:
        user_prompt += f" Prefer this topic: {topic_hint}."
    resp = _oai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role":"system","content":SYSTEM_PROMPT},
            {"role":"user","content":user_prompt}
        ],
        temperature=0.7,
        max_tokens=400
    )
    text = resp.choices[0].message.content.strip()

    parts = [p.strip() for p in text.split("\n\n") if p.strip()]
    slide1 = parts[0] if parts else text
    slide2 = parts[1] if len(parts)>1 else ""
    slide3 = parts[2] if len(parts)>2 else "Follow @QuantumBitesDaily for a daily science bite! 🚀"
    caption = f"{slide1}\n\n{slide2}\n\n{slide3}"
    hashtags = "#QuantumBitesDaily #Physics #Space #Astrophysics #Cosmology #ScienceFacts #STEM #LearnDaily #AIgenerated #AzureFunctions"
    return {"slide1":slide1, "slide2":slide2, "slide3":slide3, "caption":caption, "hashtags":hashtags}

def generate_background(prompt: str) -> Image.Image:
    img_resp = _oai.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1024x1024",
        quality="low",
        n=1
    )
    b64 = img_resp.data[0].b64_json
    import base64
    raw = base64.b64decode(b64)
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    im = im.resize((2048,2048), Image.LANCZOS)
    return im

def render_slide(bg: Image.Image, title: str, body: str, slide_no:int) -> Image.Image:
    W, H = bg.size
    canvas = bg.copy()

    overlay = Image.new("RGBA", (W,H), (0,0,0,100))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay)

    draw = ImageDraw.Draw(canvas)
    try:
        title_font = ImageFont.truetype("DejaVuSans.ttf", 64)
        body_font  = ImageFont.truetype("DejaVuSans.ttf", 36)
        footer_font= ImageFont.truetype("DejaVuSans.ttf", 28)
    except:
        title_font = ImageFont.load_default()
        body_font  = ImageFont.load_default()
        footer_font= ImageFont.load_default()

    max_width = int(W*0.82)
    y = int(H*0.12)
    for line in wrap_text(title, title_font, max_width, draw):
        draw.text((int(W*0.09), y), line, fill=(255,255,255,255), font=title_font)
        y += title_font.size + 10

    y += 20
    for line in wrap_text(body, body_font, max_width, draw):
        draw.text((int(W*0.09), y), line, fill=(230,230,230,255), font=body_font)
        y += body_font.size + 8

    footer_h = 84
    draw.rectangle([(0,H-footer_h),(W,H)], fill=(0,0,0,140))
    brand_text = f"QuantumBitesDaily  •  Slide {slide_no}/3"
    draw.text((int(W*0.04), H-footer_h+28), brand_text, fill=(255,255,255,255), font=footer_font)

    out = canvas.convert("RGB").resize((1080,1080), Image.LANCZOS)
    return out

def wrap_text(text, font, max_width, draw):
    words = text.replace("\\r","").split()
    lines, line = [], ""
    for w in words:
        test = (line + " " + w).strip()
        wlen = draw.textlength(test, font=font)
        if wlen <= max_width:
            line = test
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines

def upload_png_and_get_sas(img, blob_name: str, hours_valid:int=1) -> Tuple[str,str]:
    container_client = _blob_svc.get_container_client(CONTAINER)
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    container_client.upload_blob(name=blob_name, data=buf, overwrite=True, content_type="image/png")

    # user delegation SAS (for MSI)
    udk = _blob_svc.get_user_delegation_key(datetime.datetime.utcnow(),
                                            datetime.datetime.utcnow() + datetime.timedelta(hours=hours_valid))
    sas = generate_blob_sas(
        account_name=_blob_svc.account_name,
        container_name=CONTAINER,
        blob_name=blob_name,
        user_delegation_key=udk,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.datetime.utcnow() + datetime.timedelta(hours=hours_valid),
        protocol="https"
    )
    url = f"https://{_blob_svc.account_name}.blob.core.windows.net/{CONTAINER}/{blob_name}?{sas}"
    return url, f"https://{_blob_svc.account_name}.blob.core.windows.net/{CONTAINER}/{blob_name}"

IG_BASE = "https://graph.facebook.com/v19.0"

def ig_create_image_container(image_url: str, caption: str = "") -> str:
    params = {
        "image_url": image_url,
        "caption": caption,
        "access_token": IG_ACCESS_TOKEN
    }
    r = requests.post(f"{IG_BASE}/{IG_USER_ID}/media", params=params, timeout=60)
    r.raise_for_status()
    return r.json()["id"]

def ig_publish_carousel(children_ids: List[str], caption: str) -> str:
    params = {
        "media_type": "CAROUSEL",
        "children": ",".join(children_ids),
        "caption": caption,
        "access_token": IG_ACCESS_TOKEN
    }
    r = requests.post(f"{IG_BASE}/{IG_USER_ID}/media", params=params, timeout=60)
    r.raise_for_status()
    creation_id = r.json()["id"]

    r2 = requests.post(f"{IG_BASE}/{IG_USER_ID}/media_publish",
                       params={"creation_id": creation_id, "access_token": IG_ACCESS_TOKEN},
                       timeout=60)
    r2.raise_for_status()
    return r2.json().get("id", creation_id)