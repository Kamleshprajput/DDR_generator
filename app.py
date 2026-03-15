import streamlit as st
import google.generativeai as genai
import json
import re
import tempfile
import os
import io
from datetime import datetime
from PIL import Image
from pdf2image import convert_from_bytes
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, Image as RLImage, PageBreak
)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="UrbanRoof DDR Generator",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.ur-header { background:linear-gradient(135deg,#1a1a1a 0%,#2d2d2d 100%); border-radius:12px; padding:2rem 2.5rem; margin-bottom:1.5rem; display:flex; align-items:center; gap:16px; }
.ur-header-title { font-family:'DM Serif Display',serif; font-size:26px; font-weight:400; color:white; margin:0; }
.ur-header-sub   { font-size:13px; color:rgba(255,255,255,0.55); margin:2px 0 0; }
.section-wrap    { padding:1.5rem 2rem; border-bottom:1px solid #f5f5f5; }
.section-tag     { font-size:10px; font-weight:600; letter-spacing:0.8px; text-transform:uppercase; color:#888; margin-bottom:6px; display:flex; align-items:center; gap:6px; }
.section-tag-dot { width:6px; height:6px; border-radius:50%; background:#F5A623; display:inline-block; }
.section-title   { font-family:'DM Serif Display',serif; font-size:20px; font-weight:400; color:#1a1a1a; margin:0 0 1rem; }
.area-card       { background:#fafafa; border:1px solid #f0f0f0; border-radius:8px; padding:1rem 1.25rem; margin-bottom:10px; }
.area-header     { display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; }
.area-name       { font-size:14px; font-weight:500; color:#1a1a1a; }
.badge-high     { background:#FCEBEB; color:#A32D2D; padding:3px 10px; border-radius:20px; font-size:11px; font-weight:500; }
.badge-moderate { background:#FAEEDA; color:#854F0B; padding:3px 10px; border-radius:20px; font-size:11px; font-weight:500; }
.badge-low      { background:#EAF3DE; color:#3B6D11; padding:3px 10px; border-radius:20px; font-size:11px; font-weight:500; }
.badge-na       { background:#f5f5f5; color:#888;   padding:3px 10px; border-radius:20px; font-size:11px; font-weight:500; }
.thermal-note   { background:#E6F1FB; border-left:3px solid #185FA5; border-radius:0 4px 4px 0; padding:8px 10px; margin-top:8px; font-size:12px; color:#0C447C; line-height:1.5; }
.action-item    { display:flex; gap:12px; margin-bottom:12px; align-items:flex-start; }
.action-num     { width:26px; height:26px; border-radius:50%; background:#F5A623; color:white; font-size:11px; font-weight:600; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.action-title   { font-size:14px; font-weight:500; color:#1a1a1a; margin-bottom:3px; }
.action-desc    { font-size:13px; line-height:1.6; color:#666; }
.cause-row      { display:flex; gap:10px; margin-bottom:10px; align-items:flex-start; }
.cause-icon     { width:20px; height:20px; border-radius:4px; background:#FCEBEB; color:#A32D2D; font-size:11px; font-weight:700; display:flex; align-items:center; justify-content:center; flex-shrink:0; margin-top:2px; }
.cause-text     { font-size:13px; line-height:1.6; color:#555; }
.missing-item   { display:flex; gap:8px; align-items:flex-start; padding:8px 12px; background:#fafafa; border:1px solid #f0f0f0; border-radius:8px; margin-bottom:8px; font-size:13px; color:#666; }
.missing-tag    { font-size:10px; font-weight:600; color:#854F0B; background:#FAEEDA; padding:2px 6px; border-radius:4px; white-space:nowrap; }
.disclaimer     { background:#fafafa; border:1px solid #f0f0f0; border-radius:8px; padding:1rem; font-size:12px; color:#888; line-height:1.6; margin-top:1.5rem; }
div[data-testid="stFileUploader"] { border:none !important; }
.stButton button { background:#F5A623 !important; color:white !important; border:none !important; border-radius:8px !important; font-weight:500 !important; font-size:14px !important; padding:0.6rem 1.5rem !important; width:100%; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def get_api_key() -> str:
    """Read Gemini API key from st.secrets only."""
    try:
        return st.secrets["GEMINI_API_KEY"]
    except KeyError:
        st.error("GEMINI_API_KEY not found in Streamlit secrets.")
        st.stop()


def severity_badge(sev: str) -> str:
    s = (sev or "").lower()
    if "high" in s or "critical" in s:
        return f'<span class="badge-high">{sev}</span>'
    if "moderate" in s or "medium" in s:
        return f'<span class="badge-moderate">{sev}</span>'
    if "low" in s or "good" in s:
        return f'<span class="badge-low">{sev}</span>'
    return f'<span class="badge-na">{sev or "N/A"}</span>'


def priority_badge(priority: str) -> str:
    p = (priority or "").lower()
    if "immediate" in p:
        return '<span style="font-size:10px;font-weight:600;background:#FCEBEB;color:#A32D2D;padding:2px 8px;border-radius:20px;">Immediate</span>'
    if "short" in p:
        return '<span style="font-size:10px;font-weight:600;background:#FAEEDA;color:#854F0B;padding:2px 8px;border-radius:20px;">Short-term</span>'
    if "long" in p:
        return '<span style="font-size:10px;font-weight:600;background:#EAF3DE;color:#3B6D11;padding:2px 8px;border-radius:20px;">Long-term</span>'
    return ""


def _poppler_error(e: Exception) -> bool:
    """Return True and show a clear error if poppler is missing."""
    err = str(e)
    if "poppler" in err.lower() or "Unable to get page count" in err:
        st.error(
            "poppler is not installed or not in PATH.\n\n"
            "**Streamlit Cloud:** add a `packages.txt` file containing `poppler-utils`.\n\n"
            "**Local (Mac):** `brew install poppler`\n"
            "**Local (Ubuntu/Debian):** `sudo apt-get install poppler-utils`"
        )
        return True
    return False


def _pdf_to_images(pdf_bytes: bytes, dpi: int = 120, max_pages: int = 60) -> list:
    """Convert PDF pages to PIL Images. Returns [] on failure."""
    try:
        return convert_from_bytes(
            pdf_bytes, dpi=dpi,
            first_page=1, last_page=max_pages,
            fmt="jpeg",
        )
    except Exception as e:
        _poppler_error(e)
        return []


def _crop_to_content(img: Image.Image, white_thresh: int = 245) -> Image.Image:
    """
    Remove near-white margins from a page image.
    Returns the tightest bounding box around non-white pixels,
    with a small padding. Falls back to full image if nothing found.
    """
    import numpy as np
    arr  = np.array(img.convert("L"))
    mask = arr < white_thresh
    rows = np.where(mask.any(axis=1))[0]
    cols = np.where(mask.any(axis=0))[0]
    if len(rows) == 0 or len(cols) == 0:
        return img
    pad = 8
    top    = max(0,          int(rows[0])  - pad)
    bottom = min(img.height, int(rows[-1]) + pad)
    left   = max(0,          int(cols[0])  - pad)
    right  = min(img.width,  int(cols[-1]) + pad)
    return img.crop((left, top, right, bottom))


def _extract_photos_from_page(page_img: Image.Image) -> list:
    """
    Extract the actual photograph(s) embedded in a PDF page.

    Strategy — detect rectangular photo regions using contour analysis:
    1. Convert to grayscale, threshold to binary
    2. Find large rectangular regions that look like photos
       (high colour variance, not near-white)
    3. If detection fails, fall back to cropping the full page

    For thermal pages the layout is always:
      LEFT half  = thermal heat-map image
      RIGHT half = visible-light photograph
    We return BOTH halves as separate images.
    """
    import numpy as np

    w, h = page_img.size

    # ── Detect if this is a thermal page ────────────────────────────────
    # Thermal pages have a strongly coloured (red/green/blue) left half
    left_half  = page_img.crop((0, 0, w // 2, h))
    right_half = page_img.crop((w // 2, 0, w, h))

    left_arr  = np.array(left_half)
    # Thermal images have high channel spread (false colour = large R-G or G-B diff)
    r, g, b   = left_arr[:,:,0], left_arr[:,:,1], left_arr[:,:,2]
    channel_spread = float(np.mean(np.abs(r.astype(int) - g.astype(int)) +
                                   np.abs(g.astype(int) - b.astype(int))))

    if channel_spread > 30:
        # Thermal page — return thermal (left) and visible-light (right) separately
        thermal_crop = _crop_to_content(left_half)
        visible_crop = _crop_to_content(right_half)
        return [("thermal", thermal_crop), ("visible", visible_crop)]
    else:
        # Regular inspection page — find photo regions
        photos = _find_photo_regions(page_img)
        if photos:
            return [("photo", p) for p in photos]
        # Fallback: return whole page cropped
        return [("photo", _crop_to_content(page_img))]


def _find_photo_regions(page_img: Image.Image) -> list:
    """
    Find embedded photo rectangles in an inspection PDF page.
    Uses the fact that photos have:
    - High local colour variance (not flat white/grey text areas)
    - Rectangular shape
    - Minimum size (at least 15% of page area)

    Returns list of cropped PIL Images, or [] if none found.
    """
    import numpy as np

    w, h   = page_img.size
    arr    = np.array(page_img.convert("L"))
    min_area = w * h * 0.10   # photo must be at least 10% of page

    # Divide page into a grid and score each cell by colour variance
    GRID   = 20
    cell_w = w // GRID
    cell_h = h // GRID
    scores = np.zeros((GRID, GRID))

    full_arr = np.array(page_img)
    for gy in range(GRID):
        for gx in range(GRID):
            cell = full_arr[gy*cell_h:(gy+1)*cell_h, gx*cell_w:(gx+1)*cell_w]
            # Score = std dev of pixel values (high = photo content, low = white/text)
            scores[gy, gx] = float(np.std(cell))

    # Threshold: cells with score > 25 are likely photo pixels
    photo_mask = scores > 25

    # Find connected rectangular blobs of high-score cells
    from scipy import ndimage
    labeled, n_features = ndimage.label(photo_mask)

    regions = []
    for label_id in range(1, n_features + 1):
        blob = np.where(labeled == label_id)
        gy_min, gy_max = int(blob[0].min()), int(blob[0].max())
        gx_min, gx_max = int(blob[1].min()), int(blob[1].max())

        # Convert grid coords back to pixel coords
        px_top    = gy_min * cell_h
        px_bottom = min(h, (gy_max + 1) * cell_h)
        px_left   = gx_min * cell_w
        px_right  = min(w, (gx_max + 1) * cell_w)

        area = (px_bottom - px_top) * (px_right - px_left)
        if area >= min_area:
            crop = page_img.crop((px_left, px_top, px_right, px_bottom))
            regions.append(crop)

    return regions


def _phash(img: Image.Image, hash_size: int = 16) -> "np.ndarray":
    """
    Compute a perceptual hash (pHash) of an image.
    Returns a binary numpy array of length hash_size^2.
    Works without any external library — uses PIL + numpy DCT approximation.
    """
    import numpy as np
    # Resize to hash_size*4 for DCT, convert to greyscale
    small  = img.convert("L").resize((hash_size * 4, hash_size * 4), Image.LANCZOS)
    pixels = np.array(small, dtype=float)

    # Apply 2D DCT-II manually (cheap version using row/col cosine projection)
    dct_rows = np.zeros_like(pixels)
    N = pixels.shape[1]
    for k in range(hash_size * 4):
        dct_rows[:, k] = np.sum(
            pixels * np.cos(np.pi * k * (2 * np.arange(N) + 1) / (2 * N)),
            axis=1,
        )
    dct_cols = np.zeros_like(dct_rows)
    M = dct_rows.shape[0]
    for k in range(hash_size * 4):
        dct_cols[k, :] = np.sum(
            dct_rows * np.cos(np.pi * k * (2 * np.arange(M) + 1) / (2 * M))[:, None],
            axis=0,
        )
    # Take top-left hash_size x hash_size coefficients (low frequencies)
    dct_low = dct_cols[:hash_size, :hash_size]
    median  = np.median(dct_low)
    return (dct_low > median).flatten()


def _hash_distance(h1: "np.ndarray", h2: "np.ndarray") -> int:
    """Hamming distance between two pHash arrays. Lower = more similar."""
    return int(np.sum(h1 != h2))


def match_thermal_to_inspection(
    thermal_pages: list,         # list of PIL Images (full thermal PDF pages)
    inspection_pages: list,      # list of PIL Images (full inspection PDF pages)
    max_distance: int = 85,      # max hamming distance to count as a match (0–256)
) -> dict:
    """
    Match each thermal page to its closest inspection photo using pHash.

    Algorithm:
    1. For each thermal page — extract the visible-light photo (right half)
    2. For each inspection page — extract embedded photos
    3. Compute pHash of every extracted photo
    4. For each thermal visible-light photo, find the inspection photo
       with the lowest hamming distance
    5. Return dict: thermal_page_index (0-based) -> {
           "inspection_page_idx": int,
           "distance": int,
           "thermal_img": PIL (heat map),
           "visible_img": PIL (visible light from thermal),
           "insp_img":    PIL (matched inspection photo),
       }
    """
    import numpy as np

    # Step 1 — extract and hash inspection photos
    insp_photo_index = []   # list of (page_idx, PIL_image, hash)
    for pg_idx, page in enumerate(inspection_pages):
        extracted = _extract_photos_from_page(page)
        for kind, photo in extracted:
            if photo.width > 60 and photo.height > 60:   # skip tiny fragments
                h = _phash(photo)
                insp_photo_index.append((pg_idx, photo, h))

    if not insp_photo_index:
        return {}

    # Step 2 — for each thermal page, extract visible-light half and match
    matches = {}
    for th_idx, therm_page in enumerate(thermal_pages):
        parts = _extract_photos_from_page(therm_page)
        thermal_img  = None
        visible_img  = None
        for kind, img in parts:
            if kind == "thermal":
                thermal_img = img
            elif kind == "visible":
                visible_img = img

        if visible_img is None:
            continue

        vis_hash = _phash(visible_img)

        # Find closest inspection photo
        best_dist  = 9999
        best_entry = None
        for pg_idx, insp_photo, insp_hash in insp_photo_index:
            d = _hash_distance(vis_hash, insp_hash)
            if d < best_dist:
                best_dist  = d
                best_entry = (pg_idx, insp_photo)

        if best_entry and best_dist <= max_distance:
            pg_idx, insp_photo = best_entry
            matches[th_idx] = {
                "inspection_page_idx": pg_idx,
                "distance":            best_dist,
                "thermal_img":         thermal_img,
                "visible_img":         visible_img,
                "insp_img":            insp_photo,
            }

    return matches


def extract_images_from_pdf(pdf_bytes: bytes, max_pages: int = 60, dpi: int = 100) -> list:
    """Convert PDF pages to PIL Images. Returns [] on failure."""
    return _pdf_to_images(pdf_bytes, dpi=dpi, max_pages=max_pages)


# ═══════════════════════════════════════════════════════════════════════════════
# PDF GENERATION  (ReportLab)
# ═══════════════════════════════════════════════════════════════════════════════

ORANGE   = colors.HexColor("#F5A623")
DARK     = colors.HexColor("#1a1a1a")
LGRAY    = colors.HexColor("#f5f5f5")
MGRAY    = colors.HexColor("#888888")
RED_BG   = colors.HexColor("#FCEBEB");  RED_FG  = colors.HexColor("#A32D2D")
AMB_BG   = colors.HexColor("#FAEEDA");  AMB_FG  = colors.HexColor("#854F0B")
GRN_BG   = colors.HexColor("#EAF3DE");  GRN_FG  = colors.HexColor("#3B6D11")
BLUE_BG  = colors.HexColor("#E6F1FB");  BLUE_FG = colors.HexColor("#0C447C")
CARD_BG  = colors.HexColor("#fafafa")
BORDER   = colors.HexColor("#e8e8e8")


def _ps(name, **kw) -> ParagraphStyle:
    defaults = dict(fontName="Helvetica", fontSize=10, leading=14,
                    textColor=colors.HexColor("#444444"))
    defaults.update(kw)
    return ParagraphStyle(name, **defaults)


def _sev_colors(sev):
    s = (sev or "").lower()
    if "high" in s or "critical" in s: return RED_BG, RED_FG
    if "moderate" in s or "medium" in s: return AMB_BG, AMB_FG
    if "low" in s or "good" in s: return GRN_BG, GRN_FG
    return LGRAY, MGRAY


def _pri_colors(pri):
    p = (pri or "").lower()
    if "immediate" in p: return RED_BG, RED_FG
    if "short" in p: return AMB_BG, AMB_FG
    if "long" in p: return GRN_BG, GRN_FG
    return LGRAY, MGRAY


def _card(inner_rows, col_w, bg=None):
    """Wrap a list of [content] rows in a styled card table."""
    t = Table([[r] for r in inner_rows], colWidths=[col_w])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), bg or CARD_BG),
        ("BOX",           (0, 0), (-1, -1), 0.5, BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
    ]))
    return t


def generate_pdf(data: dict, area_images: dict, had_thermal: bool) -> bytes:
    buf = io.BytesIO()
    W_PAGE, H_PAGE = A4
    LM = RM = 20 * mm
    W = W_PAGE - LM - RM

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=LM, rightMargin=RM,
        topMargin=20 * mm, bottomMargin=20 * mm,
        title="Detailed Diagnosis Report",
        author="UrbanRoof Private Limited",
    )

    S = {
        "cover_title": _ps("ct", fontName="Helvetica-Bold", fontSize=24,
                           textColor=colors.white, leading=30),
        "cover_sub":   _ps("cs", fontSize=12, textColor=colors.HexColor("#aaaaaa"), leading=16),
        "white_sm":    _ps("wsm", fontSize=8, textColor=colors.HexColor("#aaaaaa")),
        "sec_tag":     _ps("stag", fontName="Helvetica-Bold", fontSize=8,
                           textColor=MGRAY, leading=12, spaceAfter=2),
        "sec_title":   _ps("stit", fontName="Helvetica-Bold", fontSize=15,
                           textColor=DARK, leading=20, spaceAfter=6),
        "body":        _ps("body"),
        "bold":        _ps("bold", fontName="Helvetica-Bold", textColor=DARK),
        "small":       _ps("small", fontSize=8, textColor=MGRAY, leading=11),
        "thermal":     _ps("therm", fontSize=9, textColor=BLUE_FG, leading=13, leftIndent=6),
        "cause":       _ps("cause", fontSize=10, textColor=colors.HexColor("#555555"),
                           leading=14, leftIndent=10, spaceAfter=4),
        "act_title":   _ps("at", fontName="Helvetica-Bold", fontSize=10,
                           textColor=DARK, leading=14, spaceAfter=2),
        "act_desc":    _ps("ad", fontSize=9, textColor=colors.HexColor("#555555"),
                           leading=13, leftIndent=6, spaceAfter=4),
        "caption":     _ps("cap", fontSize=7, textColor=MGRAY,
                           leading=9, alignment=TA_CENTER),
        "disclaimer":  _ps("disc", fontName="Helvetica-Oblique",
                           fontSize=8, textColor=MGRAY, leading=12),
        "ok":          _ps("ok", fontSize=10, textColor=GRN_FG),
    }

    prop          = data.get("property", {})
    summ          = data.get("summary", {})
    areas         = data.get("areas", [])
    causes        = data.get("rootCauses", [])
    sev_rsn       = data.get("severityReasoning", "")
    actions       = data.get("actions", [])
    notes         = data.get("additionalNotes", "")
    missing       = data.get("missingInfo", [])
    therm_summary = data.get("thermalSummary", "")
    gen_on        = datetime.now().strftime("%d %b %Y, %I:%M %p")

    story = []

    # ── helpers ────────────────────────────────────────────────────────
    def sec(tag, title):
        story.append(Paragraph(f"  {tag.upper()}", S["sec_tag"]))
        story.append(Paragraph(title, S["sec_title"]))
        story.append(HRFlowable(width=W, thickness=0.5, color=BORDER, spaceAfter=6))

    def kv_rows(pairs):
        rows = [[Paragraph(k, S["small"]), Paragraph(str(v), S["body"])] for k, v in pairs]
        t = Table(rows, colWidths=[44*mm, W - 44*mm])
        t.setStyle(TableStyle([
            ("TOPPADDING",    (0,0),(-1,-1), 3),
            ("BOTTOMPADDING", (0,0),(-1,-1), 3),
            ("LEFTPADDING",   (0,0),(-1,-1), 0),
            ("RIGHTPADDING",  (0,0),(-1,-1), 0),
            ("VALIGN",        (0,0),(-1,-1),"TOP"),
        ]))
        return t

    def pill(text, bg_c, fg_c, w=22*mm):
        t = Table([[Paragraph(text, _ps("p", fontName="Helvetica-Bold",
                                        fontSize=7, textColor=fg_c,
                                        alignment=TA_CENTER))]],
                  colWidths=[w])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), bg_c),
            ("TOPPADDING",    (0,0),(-1,-1), 2),
            ("BOTTOMPADDING", (0,0),(-1,-1), 2),
            ("LEFTPADDING",   (0,0),(-1,-1), 4),
            ("RIGHTPADDING",  (0,0),(-1,-1), 4),
        ]))
        return t

    def rl_img(pil_im, max_w):
        b = io.BytesIO()
        pil_im.save(b, format="JPEG", quality=68)
        b.seek(0)
        aspect = pil_im.size[1] / pil_im.size[0]
        return RLImage(b, width=max_w, height=max_w * aspect)

    # ── Cover ──────────────────────────────────────────────────────────
    cover_rows = [
        [Paragraph("UrbanRoof Private Limited", S["white_sm"])],
        [Spacer(1, 3*mm)],
        [Paragraph("Detailed Diagnosis Report", S["cover_title"])],
        [Paragraph(f"{prop.get('address','Property')} — {prop.get('type','Structure')}",
                   S["cover_sub"])],
        [Spacer(1, 4*mm)],
        [Paragraph(f"Generated: {gen_on}   |   {'Inspection + Thermal' if had_thermal else 'Inspection only'}",
                   S["white_sm"])],
    ]
    cover_t = Table([[r] for r in cover_rows], colWidths=[W])
    cover_t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), DARK),
        ("TOPPADDING",    (0,0),(-1,-1), 14),
        ("BOTTOMPADDING", (0,0),(-1,-1), 14),
        ("LEFTPADDING",   (0,0),(-1,-1), 16),
        ("RIGHTPADDING",  (0,0),(-1,-1), 16),
    ]))
    story.append(cover_t)
    story.append(Spacer(1, 7*mm))

    # ── Section 1 — Summary ────────────────────────────────────────────
    sec("Overview", "Property Issue Summary")

    sw3 = (W - 6*mm) / 3
    def metric_box(label, value):
        inner = Table(
            [[Paragraph(label, S["small"])],
             [Paragraph(str(value), _ps("mv", fontName="Helvetica-Bold",
                                        fontSize=20, textColor=DARK, leading=24))]],
            colWidths=[sw3 - 6*mm],
        )
        inner.setStyle(TableStyle([("TOPPADDING",(0,0),(-1,-1),2),
                                    ("BOTTOMPADDING",(0,0),(-1,-1),2),
                                    ("LEFTPADDING",(0,0),(-1,-1),0),
                                    ("RIGHTPADDING",(0,0),(-1,-1),0)]))
        outer = Table([[inner]], colWidths=[sw3])
        outer.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), LGRAY),
            ("TOPPADDING",    (0,0),(-1,-1), 8),
            ("BOTTOMPADDING", (0,0),(-1,-1), 8),
            ("LEFTPADDING",   (0,0),(-1,-1), 10),
            ("RIGHTPADDING",  (0,0),(-1,-1), 10),
        ]))
        return outer

    mrow = Table(
        [[metric_box("Issues Identified", summ.get("totalIssues", len(areas))),
          metric_box("Areas Inspected",   summ.get("areasInspected", len(areas))),
          metric_box("Overall Condition", summ.get("overallCondition", "Moderate"))]],
        colWidths=[sw3]*3
    )
    mrow.setStyle(TableStyle([("LEFTPADDING",(0,0),(-1,-1),3),
                               ("RIGHTPADDING",(0,0),(-1,-1),3),
                               ("TOPPADDING",(0,0),(-1,-1),0),
                               ("BOTTOMPADDING",(0,0),(-1,-1),0)]))
    story.append(mrow)
    story.append(Spacer(1, 4*mm))
    story.append(kv_rows([
        ("Address",          prop.get("address",        "Not Available")),
        ("Property type",    prop.get("type",           "Not Available")),
        ("Building age",     prop.get("age",            "Not Available")),
        ("Floors",           prop.get("floors",         "Not Available")),
        ("Inspected by",     prop.get("inspectedBy",    "Not Available")),
        ("Inspection date",  prop.get("inspectionDate", "Not Available")),
        ("Previous audit",   prop.get("previousAudit",  "Not Available")),
        ("Previous repairs", prop.get("previousRepairs","Not Available")),
        ("Score",            prop.get("overallScore",   "Not Available")),
    ]))
    story.append(Spacer(1, 8*mm))

    # ── Section 2 — Area-wise with images ─────────────────────────────
    sec("Area-wise findings", "Visual Observation & Thermal Readings")

    for area in areas:
        aname = area.get("name", "Area")
        neg   = area.get("negativeFindings", "")
        pos   = area.get("positiveFindings", "")
        therm = area.get("thermalData", "")
        sev   = area.get("severity", "")
        sbg, sfg = _sev_colors(sev)

        sev_pill = pill(sev or "N/A", sbg, sfg, 22*mm)
        hdr = Table(
            [[Paragraph(aname, S["bold"]), sev_pill]],
            colWidths=[W - 34*mm, 32*mm],
        )
        hdr.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"MIDDLE"),
                                  ("LEFTPADDING",(0,0),(-1,-1),0),
                                  ("RIGHTPADDING",(0,0),(-1,-1),0),
                                  ("TOPPADDING",(0,0),(-1,-1),0),
                                  ("BOTTOMPADDING",(0,0),(-1,-1),4)]))

        card_items = [hdr]
        if neg:
            card_items += [Paragraph("Damage observed (negative side):", S["bold"]),
                           Paragraph(neg, S["body"])]
        if pos:
            card_items += [Spacer(1, 2*mm),
                           Paragraph("Root cause area (positive side):", S["bold"]),
                           Paragraph(pos, S["body"])]
        if therm and therm.strip().lower() not in ("not available","n/a",""):
            therm_sb = area.get("thermalSeverityBasis","")
            therm_content = [Paragraph(f"Thermal reading: {therm}", S["thermal"])]
            if therm_sb and therm_sb.strip().lower() not in ("not available","n/a",""):
                therm_content.append(
                    Paragraph(therm_sb, _ps("tsb", fontSize=8, textColor=BLUE_FG,
                                            leading=11, leftIndent=6))
                )
            tb = Table([[item] for item in therm_content], colWidths=[W - 28*mm])
            tb.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),BLUE_BG),
                                     ("TOPPADDING",(0,0),(-1,-1),5),
                                     ("BOTTOMPADDING",(0,0),(-1,-1),5),
                                     ("LEFTPADDING",(0,0),(-1,-1),8),
                                     ("RIGHTPADDING",(0,0),(-1,-1),8)]))
            card_items += [Spacer(1,2*mm), tb]

        # Gemini-assigned images — inspection and thermal shown in labelled pairs
        assigned   = area_images.get(aname, {})
        insp_set   = assigned.get("insp",  [])[:3]
        therm_set  = assigned.get("therm", [])[:2]
        all_imgs   = insp_set + therm_set

        if all_imgs:
            card_items.append(Spacer(1, 3*mm))
            labels   = (["Inspection"] * len(insp_set)) + (["Thermal"] * len(therm_set))
            n_img    = len(all_imgs)
            img_w    = (W - 28*mm - (n_img - 1)*3*mm) / n_img

            # Caption row
            cap_cells = [
                Paragraph(lbl, _ps(f"ic{k}", fontSize=7, textColor=MGRAY,
                                    leading=9, alignment=TA_CENTER))
                for k, lbl in enumerate(labels)
            ]
            cap_tbl = Table([cap_cells], colWidths=[img_w]*n_img)
            cap_tbl.setStyle(TableStyle([
                ("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),2),
                ("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),2),
            ]))
            card_items.append(cap_tbl)

            # Image row
            img_cells = [rl_img(im, img_w) for im in all_imgs]
            img_tbl   = Table([img_cells], colWidths=[img_w]*n_img)
            img_tbl.setStyle(TableStyle([
                ("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),0),
                ("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),2),
                ("VALIGN",(0,0),(-1,-1),"TOP"),
            ]))
            card_items.append(img_tbl)

        story.append(KeepTogether(_card(card_items, W - 8*mm)))
        story.append(Spacer(1, 3*mm))

    story.append(Spacer(1, 5*mm))

    # ── Section 3 — Root Causes ────────────────────────────────────────
    sec("Diagnosis", "Probable Root Causes")
    if causes:
        for i, c in enumerate(causes, 1):
            story.append(Paragraph(f"{i}.  {c}", S["cause"]))
    else:
        story.append(Paragraph("Not Available", S["body"]))
    story.append(Spacer(1, 8*mm))

    # ── Section 3b — Thermal Summary ──────────────────────────────────
    if had_thermal and therm_summary and therm_summary.strip().lower() not in ("not available","n/a","none",""):
        sec("Thermal scan summary", "What the Thermal Scan Revealed")
        story.append(Paragraph(therm_summary, S["body"]))
        story.append(Spacer(1, 8*mm))

    # ── Section 4 — Severity ───────────────────────────────────────────
    sec("Severity assessment", "Issue Severity Overview")

    high_c = sum(1 for a in areas if "high"     in a.get("severity","").lower() or "critical" in a.get("severity","").lower())
    mod_c  = sum(1 for a in areas if "moderate" in a.get("severity","").lower())
    low_c  = sum(1 for a in areas if "low"      in a.get("severity","").lower())

    sw = (W - 8*mm) / 3
    def sev_box(label, count, bg_c, fg_c):
        inner = Table(
            [[Paragraph(label, _ps("sl", fontSize=8, textColor=fg_c))],
             [Paragraph(str(count), _ps("sv", fontName="Helvetica-Bold",
                                        fontSize=22, textColor=fg_c, leading=26))]],
            colWidths=[sw - 6*mm],
        )
        inner.setStyle(TableStyle([("TOPPADDING",(0,0),(-1,-1),2),
                                    ("BOTTOMPADDING",(0,0),(-1,-1),2),
                                    ("LEFTPADDING",(0,0),(-1,-1),0),
                                    ("RIGHTPADDING",(0,0),(-1,-1),0),
                                    ("ALIGN",(0,0),(-1,-1),"CENTER")]))
        outer = Table([[inner]], colWidths=[sw])
        outer.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),bg_c),
            ("TOPPADDING",(0,0),(-1,-1),8),("BOTTOMPADDING",(0,0),(-1,-1),8),
            ("LEFTPADDING",(0,0),(-1,-1),3),("RIGHTPADDING",(0,0),(-1,-1),3),
        ]))
        return outer

    srow = Table([[sev_box("High severity",     high_c, RED_BG, RED_FG),
                   sev_box("Moderate severity", mod_c,  AMB_BG, AMB_FG),
                   sev_box("Low severity",      low_c,  GRN_BG, GRN_FG)]],
                 colWidths=[sw]*3)
    srow.setStyle(TableStyle([("LEFTPADDING",(0,0),(-1,-1),3),
                               ("RIGHTPADDING",(0,0),(-1,-1),3),
                               ("TOPPADDING",(0,0),(-1,-1),0),
                               ("BOTTOMPADDING",(0,0),(-1,-1),0)]))
    story.append(srow)
    if sev_rsn:
        story.append(Spacer(1, 4*mm))
        story.append(Paragraph(sev_rsn, S["body"]))
    story.append(Spacer(1, 8*mm))

    # ── Section 5 — Actions ────────────────────────────────────────────
    sec("Recommended actions", "Suggested Therapies & Repairs")

    if actions:
        for i, action in enumerate(actions, 1):
            pri = action.get("priority", "")
            pbg, pfg = _pri_colors(pri)

            num_t = Table([[Paragraph(str(i), _ps("n", fontName="Helvetica-Bold",
                                                   fontSize=10, textColor=colors.white,
                                                   alignment=TA_CENTER))]],
                          colWidths=[7*mm])
            num_t.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(-1,-1),ORANGE),
                ("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3),
                ("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),0),
                ("ALIGN",(0,0),(-1,-1),"CENTER"),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
            ]))

            title_row_items = [Paragraph(action.get("title","Action"), S["act_title"])]
            if pri:
                title_row_items.append(pill(pri, pbg, pfg, 22*mm))
                title_tbl = Table([title_row_items],
                                  colWidths=[W - 40*mm, 24*mm])
                title_tbl.setStyle(TableStyle([
                    ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
                    ("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),0),
                    ("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),2),
                ]))
            else:
                title_tbl = title_row_items[0]

            targets = action.get("targetAreas", [])
            target_text = "Applies to: " + ", ".join(targets) if targets else ""
            right_col = [title_tbl,
                         Paragraph(action.get("description",""), S["act_desc"])]
            if target_text:
                right_col.append(
                    Paragraph(target_text, _ps("ta", fontSize=8, textColor=MGRAY,
                                               leading=11, leftIndent=6))
                )
            arow = Table([[num_t, right_col]], colWidths=[10*mm, W - 10*mm])
            arow.setStyle(TableStyle([
                ("VALIGN",(0,0),(-1,-1),"TOP"),
                ("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),0),
                ("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),6),
            ]))
            story.append(arow)
    else:
        story.append(Paragraph("Not Available", S["body"]))
    story.append(Spacer(1, 8*mm))

    # ── Section 6 — Notes ─────────────────────────────────────────────
    if notes and notes.strip().lower() not in ("not available","n/a","none",""):
        sec("Notes", "Additional Notes")
        story.append(Paragraph(notes, S["body"]))
        story.append(Spacer(1, 8*mm))

    # ── Section 7 — Missing info ───────────────────────────────────────
    sec("Data gaps", "Missing or Unclear Information")
    if not missing:
        story.append(Paragraph(
            "All required information was successfully extracted from the provided documents.",
            S["ok"],
        ))
    else:
        for m in missing:
            row = Table(
                [[pill("Not Available", AMB_BG, AMB_FG, 28*mm),
                  Paragraph(m, S["body"])]],
                colWidths=[30*mm, W - 30*mm],
            )
            row.setStyle(TableStyle([
                ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
                ("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),0),
                ("TOPPADDING",(0,0),(-1,-1),2),("BOTTOMPADDING",(0,0),(-1,-1),2),
            ]))
            story.append(row)
            story.append(Spacer(1, 2*mm))
    story.append(Spacer(1, 8*mm))

    # ── Image Appendix ─────────────────────────────────────────────────
    # Collect all assigned images across all areas for the appendix
    gallery = []
    for aname, imgs_dict in area_images.items():
        for img in imgs_dict.get("insp", []):
            gallery.append((f"Inspection – {aname}", img))
        for img in imgs_dict.get("therm", []):
            gallery.append((f"Thermal – {aname}", img))
    if gallery:
        story.append(PageBreak())
        sec("Appendix", "Image References")
        COLS = 2
        cw = (W - (COLS-1)*4*mm) / COLS
        row_buf = []
        for source, im in gallery:
            cap = Paragraph(source, S["caption"])
            cell = Table([[rl_img(im, cw)], [cap]], colWidths=[cw])
            cell.setStyle(TableStyle([
                ("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),3),
                ("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),0),
                ("ALIGN",(0,0),(-1,-1),"CENTER"),
            ]))
            row_buf.append(cell)
            if len(row_buf) == COLS:
                rt = Table([row_buf], colWidths=[cw]*COLS)
                rt.setStyle(TableStyle([
                    ("VALIGN",(0,0),(-1,-1),"TOP"),
                    ("LEFTPADDING",(0,0),(-1,-1),0),
                    ("RIGHTPADDING",(0,0),(-1,-1),4),
                    ("TOPPADDING",(0,0),(-1,-1),0),
                    ("BOTTOMPADDING",(0,0),(-1,-1),4),
                ]))
                story.append(rt)
                row_buf = []
        if row_buf:
            pad = [Spacer(cw, 1)] * (COLS - len(row_buf))
            rt = Table([row_buf + pad], colWidths=[cw]*COLS)
            rt.setStyle(TableStyle([
                ("VALIGN",(0,0),(-1,-1),"TOP"),
                ("LEFTPADDING",(0,0),(-1,-1),0),
                ("RIGHTPADDING",(0,0),(-1,-1),4),
                ("TOPPADDING",(0,0),(-1,-1),0),
                ("BOTTOMPADDING",(0,0),(-1,-1),4),
            ]))
            story.append(rt)

    # ── Disclaimer ─────────────────────────────────────────────────────
    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width=W, thickness=0.5, color=BORDER, spaceAfter=4))
    story.append(Paragraph(
        "This report is AI-generated based on the uploaded inspection and thermal documents. "
        "It is a diagnostic summary only and does not replace a full structural engineering "
        "assessment. All findings should be verified on-site by a qualified professional "
        "before initiating repairs. UrbanRoof Private Limited accepts no liability for "
        "decisions made solely based on this AI-generated report.",
        S["disclaimer"],
    ))

    doc.build(story)
    return buf.getvalue()


# ═══════════════════════════════════════════════════════════════════════════════
# APP UI
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="ur-header">
    <div style="width:48px;height:48px;background:#F5A623;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:18px;font-weight:700;color:white;flex-shrink:0;">UR</div>
    <div>
        <p class="ur-header-title">UrbanRoof DDR Generator</p>
        <p class="ur-header-sub">AI-powered Detailed Diagnosis Report from inspection &amp; thermal data</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ℹ️ About")
    st.markdown("**Works with any:**")
    st.markdown("- Flat / row house / bungalow / CHS")
    st.markdown("- Any number of impacted areas")
    st.markdown("- With or without thermal PDF")
    st.markdown("---")
    st.markdown("**Report includes:**")
    st.markdown("- Property summary")
    st.markdown("- Area-wise observations + images")
    st.markdown("- Root cause analysis")
    st.markdown("- Severity assessment")
    st.markdown("- Recommended actions")
    st.markdown("- Downloadable PDF")

# ── Upload ────────────────────────────────────────────────────────────────────
st.markdown("### 📂 Upload Documents")
st.markdown(
    "<p style='font-size:13px;color:#888;margin-bottom:1rem;'>"
    "The AI adapts to whatever property type, number of areas, and format you provide.</p>",
    unsafe_allow_html=True,
)

c1, c2 = st.columns(2)
with c1:
    st.markdown("**Inspection Report** *(required)*")
    inspection_file = st.file_uploader("insp", type=["pdf"], key="inspection",
                                        label_visibility="collapsed")
    if inspection_file:
        st.success(f"✅ {inspection_file.name}")

with c2:
    st.markdown("**Thermal Images Report** *(optional)*")
    thermal_file = st.file_uploader("therm", type=["pdf"], key="thermal",
                                     label_visibility="collapsed")
    if thermal_file:
        st.success(f"✅ {thermal_file.name}")
    else:
        st.info("ℹ️ No thermal PDF — report generated from inspection only.")

st.markdown("<br>", unsafe_allow_html=True)

api_key = get_api_key()
ready   = bool(inspection_file)

if not inspection_file:
    st.info("Upload the Inspection Report PDF above.")

# ── Generate ──────────────────────────────────────────────────────────────────
if st.button("🔍 Generate Detailed Diagnosis Report", disabled=not ready):

    inspection_bytes = inspection_file.read()
    thermal_bytes    = thermal_file.read() if thermal_file else None
    has_thermal      = thermal_bytes is not None

    # Step 1 — extract all pages at medium DPI for matching + display
    with st.spinner("📄 Extracting PDF pages…"):
        insp_pages  = extract_images_from_pdf(inspection_bytes, max_pages=60, dpi=120)
        therm_pages = extract_images_from_pdf(thermal_bytes,    max_pages=60, dpi=120) if has_thermal else []
        n_insp  = len(insp_pages)
        n_therm = len(therm_pages)

    st.info(
        f"Found {n_insp} page(s) in inspection PDF"
        + (f" and {n_therm} in thermal PDF." if has_thermal else ".")
    )

    # Step 1b — algorithmically match thermal pages to inspection photos
    thermal_matches = {}   # thermal_page_idx (0-based) -> match dict
    if has_thermal and therm_pages and insp_pages:
        with st.spinner("🔍 Matching thermal images to inspection photos using perceptual hashing…"):
            thermal_matches = match_thermal_to_inspection(
                therm_pages, insp_pages, max_distance=85
            )
        n_matched = len(thermal_matches)
        st.info(f"Matched {n_matched} of {n_therm} thermal pages to inspection photos.")

    # Step 2 — Gemini analysis
    SYSTEM = """You are UrbanRoof's expert building diagnostics AI. Your job is to read an
inspection report and optional thermal imaging report, cross-reference them deeply,
and produce a structured Detailed Diagnosis Report (DDR) as JSON.

═══════════════════════════════════════════════════
STEP A — READ & INDEX EVERY PAGE BEFORE WRITING JSON
═══════════════════════════════════════════════════
Before producing any output, mentally build an index:

For DOCUMENT 1 (Inspection Report):
  For each page, note:
  - Is it a cover/TOC/disclaimer/text-only page? → skip for images
  - Is it a photo page? → note the EXACT location label visible in the caption or
    surrounding text (e.g. "Hall Skirting", "Master Bedroom 1st Floor",
    "Common Bathroom Ground Floor"). Be as specific as the document is.
  - Is it a checklist/form page? → extract observations but do NOT assign as image

For DOCUMENT 2 (Thermal Report):
  Each page typically has:
  - A thermal camera image (false-colour heat map showing hotspot/coldspot temps)
  - A paired visible-light photo of the same location
  - A data panel showing: Hotspot °C, Coldspot °C, Emissivity, Date/Time
  For each thermal page, note:
  - The exact location visible in the visible-light photo
  - The hotspot and coldspot temperatures
  - The timestamp (helps sequence observations)

═══════════════════════════════════════════════════
STEP B — CROSS-REFERENCE THERMAL ↔ INSPECTION
═══════════════════════════════════════════════════
Match each thermal page to its corresponding inspection observation using:
1. LOCATION MATCH — the physical location visible in the photo must match
   the area name exactly, not just the flat number.
   BAD: "this thermal page is from Flat 103 so assign to all Flat 103 areas"
   GOOD: "this thermal page shows skirting-level dampness at a wall corner →
          matches the area named Bedroom Skirting Level Dampness"

2. TEMPERATURE INTERPRETATION — use the hotspot/coldspot delta to assess severity:
   - Coldspot 3°C+ below ambient (23°C) = active moisture/wet surface → High severity
   - Coldspot 1–3°C below ambient = residual dampness → Moderate severity
   - Coldspot < 1°C below ambient = dry or minor surface variation → Low severity
   - Ambient reference: 23°C (emissivity 0.94 in all thermal images)

3. VISUAL CONFIRMATION — only link a thermal page to an inspection area if
   the visible-light photo in the thermal page shows the SAME physical damage
   (same wall, same corner, same type of defect) as described in the inspection.

═══════════════════════════════════════════════════
STEP C — IMAGE ASSIGNMENT RULES (strict)
═══════════════════════════════════════════════════
When assigning pages to areas:
- Assign a page only if its caption/label/photo content explicitly shows that
  SPECIFIC room/location — not just the same flat.
- A page showing "Hall ceiling dampness" → assign ONLY to the Hall area.
- A page showing "Master Bedroom skirting" → assign ONLY to Master Bedroom area.
- Text-only pages, cover pages, TOC, disclaimers, checklist forms → assign to NO area.
- Each page may appear in at most ONE area assignment.
- Max 3 inspection pages and 2 thermal pages per area.
- If no photo exists for an area, use empty lists — never assign a wrong page.

═══════════════════════════════════════════════════
OUTPUT — valid JSON only, no markdown, no preamble
═══════════════════════════════════════════════════
{
  "property": {
    "address": "full address or Not Available",
    "type": "Flat / Row House / Bungalow / CHS / etc.",
    "age": "years or Not Available",
    "floors": "number or Not Available",
    "inspectedBy": "name(s) or Not Available",
    "inspectionDate": "date or Not Available",
    "overallScore": "score % or Not Available",
    "previousAudit": "Yes / No / Not Available",
    "previousRepairs": "Yes / No / Not Available"
  },
  "summary": {
    "totalIssues": <integer — number of distinct impacted areas>,
    "criticalAreas": <integer — count of High severity areas>,
    "areasInspected": <integer>,
    "overallCondition": "Good / Moderate / Poor"
  },
  "areas": [
    {
      "name": "Specific area name — include room + location e.g. Master Bedroom Skirting Level",
      "severity": "High / Moderate / Low — informed by thermal coldspot delta if available",
      "negativeFindings": "What damage is visible on the impacted side — be specific about location within room",
      "positiveFindings": "What root-cause defect is visible on the source side",
      "thermalData": "Hotspot X°C, Coldspot Y°C, delta Z°C below ambient — interpretation e.g. active moisture or Not Available",
      "thermalSeverityBasis": "One sentence explaining how the thermal reading informed the severity rating — or Not Available"
    }
  ],
  "rootCauses": [
    "Each distinct root cause — specific, not generic (e.g. gaps in tile grout joints allowing capillary moisture rise through RCC slab)"
  ],
  "severityReasoning": "Paragraph explaining overall severity — reference specific thermal readings where available",
  "actions": [
    {
      "title": "Short action name",
      "priority": "Immediate / Short-term / Long-term",
      "description": "Step-by-step repair in plain language",
      "targetAreas": ["area name 1", "area name 2"]
    }
  ],
  "thermalSummary": "Overall summary of what the thermal scan revealed — temperature ranges found, number of active moisture zones, how findings compare to visual inspection",
  "additionalNotes": "Document conflicts, unusual findings, or Not Available",
  "missingInfo": ["each absent or unclear item"],
  "imageAssignments": [
    {
      "areaName": "Must exactly match one of the area names above",
      "inspectionPages": [<1-indexed page numbers — only pages whose photo caption/content explicitly names this specific room/location>],
      "thermalPages": [<1-indexed page numbers from thermal doc whose visible-light photo shows this exact location>]
    }
  ]
}"""

    # Build a page manifest to give Gemini a concrete reference frame
    page_manifest = f"DOCUMENT 1 (Inspection Report): {n_insp} pages total\n"
    if has_thermal:
        page_manifest += (
            f"DOCUMENT 2 (Thermal Images Report): {n_therm} pages total\n"
            f"Note: Each page of Document 2 contains one thermal camera image "
            f"(false-colour heat map) paired with a visible-light photo of the same location, "
            f"plus a data panel showing Hotspot/Coldspot temperatures.\n"
        )

    USER = (
        "Follow Steps A, B, C from your instructions and produce the DDR JSON.\n\n"
        + page_manifest
        + "\nKey reminder for imageAssignments:\n"
        + "- Do NOT assign pages based on flat number alone.\n"
        + "- Only assign a page if its visible photo content shows that specific room/location.\n"
        + "- Text pages, checklists, cover pages = no image assignment.\n"
        + ("- For each thermal page, the visible-light photo tells you the exact location — "
           "use that to match to the inspection area, not the flat number.\n"
           if has_thermal else
           "- No thermal document provided. Set thermalData to Not Available for all areas.\n")
        + "\nReturn ONLY the JSON."
    )

    with st.spinner("🤖 Gemini is reading your documents…"):
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                generation_config=genai.GenerationConfig(
                    temperature=0.1,
                    response_mime_type="application/json",
                ),
                system_instruction=SYSTEM,
            )

            parts = []
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as t1:
                t1.write(inspection_bytes); t1p = t1.name
            parts.append(genai.upload_file(path=t1p, mime_type="application/pdf",
                                            display_name=inspection_file.name))
            os.unlink(t1p)

            if has_thermal:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as t2:
                    t2.write(thermal_bytes); t2p = t2.name
                parts.append(genai.upload_file(path=t2p, mime_type="application/pdf",
                                                display_name=thermal_file.name))
                os.unlink(t2p)

            parts.append(USER)
            raw = model.generate_content(parts).text.strip()

            cleaned = re.sub(r"^```(?:json)?\s*", "", raw)
            cleaned = re.sub(r"\s*```$", "", cleaned).strip()
            m = re.search(r"\{[\s\S]*\}", cleaned)
            if not m:
                st.error("Could not extract JSON from Gemini response.")
                with st.expander("Raw output"): st.code(raw[:3000])
                st.stop()

            data = json.loads(m.group())

            # Build area_images using Gemini page assignments + algo-matched thermal
            assignments = data.get("imageAssignments", [])
            areas_list  = data.get("areas", [])
            area_images = {}   # areaName -> {"insp": [PIL], "therm": [PIL], "pairs": [(insp,therm)]}

            with st.spinner("🖼️ Building image set per area…"):
                # Index inspection photos extracted per page
                insp_photo_cache = {}   # page_idx -> list of cropped photos
                for pg_idx, page in enumerate(insp_pages):
                    parts = _extract_photos_from_page(page)
                    photos = [img for kind, img in parts if img.width > 60]
                    if photos:
                        insp_photo_cache[pg_idx] = photos

                # Build per-area images from Gemini assignments
                for assign in assignments:
                    name  = assign.get("areaName", "").strip()
                    i_pgs = [p-1 for p in assign.get("inspectionPages", [])
                             if isinstance(p, int) and 1 <= p <= n_insp]  # to 0-based

                    insp_extracted = []
                    for pg_idx in i_pgs[:3]:
                        photos = insp_photo_cache.get(pg_idx, [])
                        insp_extracted.extend(photos[:2])  # max 2 photos per page

                    area_images.setdefault(name, {"insp": [], "therm": [], "pairs": []})
                    area_images[name]["insp"] = insp_extracted[:3]

                # Attach matched thermal images to their closest area
                # Strategy: find which Gemini area the matched inspection page belongs to
                # Build reverse map: inspection_page_idx -> area_name
                page_to_area = {}
                for assign in assignments:
                    name  = assign.get("areaName", "").strip()
                    i_pgs = [p-1 for p in assign.get("inspectionPages", [])
                             if isinstance(p, int) and 1 <= p <= n_insp]
                    for pg_idx in i_pgs:
                        page_to_area[pg_idx] = name

                for th_idx, match in thermal_matches.items():
                    insp_pg_idx   = match["inspection_page_idx"]
                    area_name     = page_to_area.get(insp_pg_idx, "")
                    thermal_img   = match.get("thermal_img")
                    visible_img   = match.get("visible_img")
                    insp_img      = match.get("insp_img")

                    if not area_name:
                        # No Gemini area claimed this page — assign to closest area
                        # by finding which area has inspection photos on similar pages
                        # (simple fallback: assign to first area with no thermal yet)
                        for a in areas_list:
                            aname = a.get("name","")
                            if aname in area_images and not area_images[aname]["therm"]:
                                area_name = aname
                                break

                    if area_name:
                        entry = area_images.setdefault(area_name,
                                    {"insp": [], "therm": [], "pairs": []})
                        if thermal_img and len(entry["therm"]) < 2:
                            entry["therm"].append(thermal_img)
                        # Store matched pair for side-by-side display
                        if insp_img and visible_img:
                            entry["pairs"].append({
                                "insp":    insp_img,
                                "visible": visible_img,
                                "thermal": thermal_img,
                                "distance": match["distance"],
                            })

            st.session_state.update({
                "ddr_data": data, "had_thermal": has_thermal,
                "area_images": area_images,
                "thermal_matches": thermal_matches,
            })

        except json.JSONDecodeError as e:
            st.error(f"❌ JSON parse error: {e}")
            with st.expander("Raw output"): st.code(raw[:3000])
            st.stop()
        except Exception as e:
            err = str(e)
            if "API_KEY_INVALID" in err or "api key" in err.lower():
                st.error("❌ Invalid Gemini API key.")
            elif "quota" in err.lower() or "429" in err:
                st.error("❌ Quota exceeded — wait a moment and retry.")
            elif "safety" in err.lower():
                st.error("❌ Gemini safety filter triggered.")
            else:
                st.error(f"❌ Error: {err}")
            st.stop()


# ═══════════════════════════════════════════════════════════════════════════════
# RENDER REPORT
# ═══════════════════════════════════════════════════════════════════════════════
if "ddr_data" in st.session_state:
    data            = st.session_state["ddr_data"]
    had_thermal     = st.session_state.get("had_thermal", False)
    area_images     = st.session_state.get("area_images", {})
    thermal_matches = st.session_state.get("thermal_matches", {})

    prop          = data.get("property", {})
    summ          = data.get("summary", {})
    areas         = data.get("areas", [])
    causes        = data.get("rootCauses", [])
    sev_rsn       = data.get("severityReasoning", "")
    actions       = data.get("actions", [])
    notes         = data.get("additionalNotes", "")
    missing       = data.get("missingInfo", [])
    therm_summary = data.get("thermalSummary", "")
    gen_on        = datetime.now().strftime("%d %b %Y, %I:%M %p")

    # Header
    st.markdown(f"""
    <div style="background:#1a1a1a;border-radius:12px 12px 0 0;padding:1.75rem 2rem;margin-top:1.5rem;">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:1rem;">
            <div style="display:flex;align-items:center;gap:10px;">
                <div style="width:32px;height:32px;background:#F5A623;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;color:white;">UR</div>
                <span style="font-size:14px;font-weight:500;color:white;">UrbanRoof Private Limited</span>
            </div>
            <div style="font-size:11px;color:rgba(255,255,255,0.4);text-align:right;">
                <div>Detailed Diagnosis Report</div>
                <div>Generated: {gen_on}</div>
                <div style="margin-top:3px;color:rgba(255,255,255,0.3);">{"Inspection + Thermal" if had_thermal else "Inspection only"}</div>
            </div>
        </div>
        <h2 style="font-family:'DM Serif Display',serif;font-size:26px;font-weight:400;color:white;margin:0 0 4px;">Detailed Diagnosis Report</h2>
        <p style="font-size:13px;color:rgba(255,255,255,0.5);margin:0;">{prop.get('address','Property')} — {prop.get('type','Structure')}</p>
    </div>
    <div style="border:1px solid #f0f0f0;border-top:none;border-radius:0 0 12px 12px;background:white;">
    """, unsafe_allow_html=True)

    # S1 — Summary
    st.markdown("""<div class="section-wrap"><div class="section-tag"><span class="section-tag-dot"></span>Overview</div><p class="section-title">Property Issue Summary</p>""", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Issues Identified", summ.get("totalIssues", len(areas)))
    c2.metric("Areas Inspected",   summ.get("areasInspected", len(areas)))
    c3.metric("Overall Condition", summ.get("overallCondition","Moderate"))
    st.markdown(f"""
    <table style="font-size:13px;color:#555;width:100%;margin-top:.75rem;border-collapse:collapse;">
    <tr><td style="padding:5px 0;width:160px;color:#999;">Address</td><td>{prop.get('address','Not Available')}</td></tr>
    <tr><td style="padding:5px 0;color:#999;">Property type</td><td>{prop.get('type','Not Available')}</td></tr>
    <tr><td style="padding:5px 0;color:#999;">Building age</td><td>{prop.get('age','Not Available')}</td></tr>
    <tr><td style="padding:5px 0;color:#999;">Floors</td><td>{prop.get('floors','Not Available')}</td></tr>
    <tr><td style="padding:5px 0;color:#999;">Inspected by</td><td>{prop.get('inspectedBy','Not Available')}</td></tr>
    <tr><td style="padding:5px 0;color:#999;">Inspection date</td><td>{prop.get('inspectionDate','Not Available')}</td></tr>
    <tr><td style="padding:5px 0;color:#999;">Previous audit</td><td>{prop.get('previousAudit','Not Available')}</td></tr>
    <tr><td style="padding:5px 0;color:#999;">Previous repairs</td><td>{prop.get('previousRepairs','Not Available')}</td></tr>
    <tr><td style="padding:5px 0;color:#999;">Score</td><td>{prop.get('overallScore','Not Available')}</td></tr>
    </table></div>""", unsafe_allow_html=True)

    # S2 — Areas with inline images
    st.markdown("""<div class="section-wrap"><div class="section-tag"><span class="section-tag-dot"></span>Area-wise findings</div><p class="section-title">Visual Observation &amp; Thermal Readings</p>""", unsafe_allow_html=True)

    for area in areas:
        aname    = area.get("name", "Area")
        neg      = area.get("negativeFindings","")
        pos      = area.get("positiveFindings","")
        therm    = area.get("thermalData","")
        therm_sb = area.get("thermalSeverityBasis","")

        has_therm = therm and therm.strip().lower() not in ("not available","n/a","")
        has_sb    = therm_sb and therm_sb.strip().lower() not in ("not available","n/a","")

        tnote = ""
        if has_therm:
            tnote = f'''<div class="thermal-note">
                <strong>🌡️ Thermal reading:</strong> {therm}
                {f'<br><span style="font-size:11px;opacity:0.85;">{therm_sb}</span>' if has_sb else ""}
            </div>'''

        # ── Render area card (HTML only — no st.image inside HTML block) ──
        st.markdown(f"""
        <div class="area-card">
            <div class="area-header">
                <span class="area-name">{aname}</span>
                {severity_badge(area.get("severity",""))}
            </div>
            <div style="font-size:13px;line-height:1.65;color:#555;">
                {"<p><strong style=\'color:#1a1a1a;\'>Damage observed (negative side):</strong><br>"+neg+"</p>" if neg else ""}
                {"<p style=\'margin-top:6px;\'><strong style=\'color:#1a1a1a;\'>Root cause area (positive side):</strong><br>"+pos+"</p>" if pos else ""}
                {tnote}
            </div>
        </div>""", unsafe_allow_html=True)

        # ── Images rendered OUTSIDE the HTML block (fixes <div> rendering bug) ──
        assigned   = area_images.get(aname, {})
        insp_imgs  = assigned.get("insp",  [])[:3]
        therm_imgs = assigned.get("therm", [])[:2]
        pairs      = assigned.get("pairs", [])

        if pairs:
            # Show algorithmically matched pairs: inspection | visible-light | thermal
            st.caption("📷 Matched images — inspection photo  ↔  thermal visible-light  ↔  thermal heat-map")
            for pair in pairs[:2]:
                c1, c2, c3 = st.columns(3)
                c1.caption("Inspection photo")
                c1.image(pair["insp"],    use_container_width=True)
                c2.caption("Thermal visible-light")
                c2.image(pair["visible"], use_container_width=True)
                if pair.get("thermal") is not None:
                    c3.caption(f"Thermal heat-map (match score: {pair['distance']})")
                    c3.image(pair["thermal"], use_container_width=True)
                else:
                    c3.caption("Heat-map")
                    c3.markdown(
                        '<div style="background:#f5f5f5;border-radius:6px;padding:1.5rem;'
                        'text-align:center;color:#aaa;font-size:12px;">No thermal image</div>',
                        unsafe_allow_html=True
                    )
        elif insp_imgs or therm_imgs:
            # Fallback: show individual images without pairing
            all_display = (
                [("📷 Inspection", img) for img in insp_imgs] +
                [("🌡️ Thermal",    img) for img in therm_imgs]
            )
            cols = st.columns(len(all_display))
            for col, (label, img) in zip(cols, all_display):
                col.caption(label)
                col.image(img, use_container_width=True)
        else:
            st.markdown(
                '<div style="background:#f9f9f9;border:1px dashed #ddd;border-radius:6px;'
                'padding:0.75rem 1rem;color:#bbb;font-size:12px;margin-bottom:8px;">'
                '📷 No images available for this area</div>',
                unsafe_allow_html=True
            )

    st.markdown("</div>", unsafe_allow_html=True)

    # S3 — Root causes
    st.markdown("""<div class="section-wrap"><div class="section-tag"><span class="section-tag-dot"></span>Diagnosis</div><p class="section-title">Probable Root Causes</p>""", unsafe_allow_html=True)
    for c in (causes or ["Not Available"]):
        st.markdown(f'<div class="cause-row"><div class="cause-icon">!</div><div class="cause-text">{c}</div></div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # S3b — Thermal Summary (only if thermal doc was provided)
    if had_thermal and therm_summary and therm_summary.strip().lower() not in ("not available","n/a","none",""):
        st.markdown(f"""<div class="section-wrap">
            <div class="section-tag"><span class="section-tag-dot"></span>Thermal scan summary</div>
            <p class="section-title">What the Thermal Scan Revealed</p>
            <p style="font-size:13px;line-height:1.75;color:#555;">{therm_summary}</p>
        </div>""", unsafe_allow_html=True)

    # S4 — Severity
    high_c = sum(1 for a in areas if "high"     in a.get("severity","").lower() or "critical" in a.get("severity","").lower())
    mod_c  = sum(1 for a in areas if "moderate" in a.get("severity","").lower())
    low_c  = sum(1 for a in areas if "low"      in a.get("severity","").lower())
    st.markdown("""<div class="section-wrap"><div class="section-tag"><span class="section-tag-dot"></span>Severity assessment</div><p class="section-title">Issue Severity Overview</p>""", unsafe_allow_html=True)
    s1, s2, s3 = st.columns(3)
    s1.markdown(f'<div style="background:#FCEBEB;border-radius:8px;padding:.75rem 1rem;text-align:center;"><div style="font-size:11px;color:#A32D2D;margin-bottom:4px;">High severity</div><div style="font-size:28px;font-weight:500;color:#A32D2D;">{high_c}</div></div>', unsafe_allow_html=True)
    s2.markdown(f'<div style="background:#FAEEDA;border-radius:8px;padding:.75rem 1rem;text-align:center;"><div style="font-size:11px;color:#854F0B;margin-bottom:4px;">Moderate severity</div><div style="font-size:28px;font-weight:500;color:#854F0B;">{mod_c}</div></div>', unsafe_allow_html=True)
    s3.markdown(f'<div style="background:#EAF3DE;border-radius:8px;padding:.75rem 1rem;text-align:center;"><div style="font-size:11px;color:#3B6D11;margin-bottom:4px;">Low severity</div><div style="font-size:28px;font-weight:500;color:#3B6D11;">{low_c}</div></div>', unsafe_allow_html=True)
    if sev_rsn:
        st.markdown(f'<p style="font-size:13px;color:#666;line-height:1.65;margin-top:1rem;">{sev_rsn}</p>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # S5 — Actions
    st.markdown("""<div class="section-wrap"><div class="section-tag"><span class="section-tag-dot"></span>Recommended actions</div><p class="section-title">Suggested Therapies &amp; Repairs</p>""", unsafe_allow_html=True)
    if not actions:
        st.markdown('<p style="color:#999;font-size:13px;">Not Available</p>', unsafe_allow_html=True)
    else:
        for i, action in enumerate(actions, 1):
            targets     = action.get("targetAreas", [])
            targets_html = ""
            if targets:
                pills = "".join(
                    f'<span style="font-size:10px;background:#f0f0f0;color:#555;padding:2px 7px;border-radius:10px;margin-right:4px;">{t}</span>'
                    for t in targets
                )
                targets_html = f'<div style="margin-top:4px;">{pills}</div>'
            st.markdown(f"""
            <div class="action-item">
                <div class="action-num">{i}</div>
                <div>
                    <div class="action-title">{action.get('title','Action')} &nbsp;{priority_badge(action.get('priority',''))}</div>
                    <div class="action-desc">{action.get('description','')}</div>
                    {targets_html}
                </div>
            </div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # S6 — Notes
    if notes and notes.strip().lower() not in ("not available","n/a","none",""):
        st.markdown(f"""<div class="section-wrap"><div class="section-tag"><span class="section-tag-dot"></span>Notes</div><p class="section-title">Additional Notes</p><p style="font-size:13px;line-height:1.75;color:#555;">{notes}</p></div>""", unsafe_allow_html=True)

    # S7 — Missing
    st.markdown("""<div class="section-wrap" style="border-bottom:none;"><div class="section-tag"><span class="section-tag-dot"></span>Data gaps</div><p class="section-title">Missing or Unclear Information</p>""", unsafe_allow_html=True)
    if not missing:
        st.markdown('<p style="font-size:13px;color:#3B6D11;">✅ All required information successfully extracted.</p>', unsafe_allow_html=True)
    else:
        for m in missing:
            st.markdown(f'<div class="missing-item"><span class="missing-tag">Not Available</span><span>{m}</span></div>', unsafe_allow_html=True)
    st.markdown("</div></div>", unsafe_allow_html=True)

    # Disclaimer
    st.markdown("""<div class="disclaimer">This report is AI-generated based on the uploaded documents. It is a diagnostic summary only and does not replace a full structural engineering assessment. All findings should be verified on-site by a qualified professional before initiating repairs. UrbanRoof Private Limited accepts no liability for decisions made solely based on this AI-generated report.</div>""", unsafe_allow_html=True)

    # Download buttons
    st.markdown("<br>", unsafe_allow_html=True)
    with st.spinner("📄 Building PDF…"):
        pdf_bytes = generate_pdf(data, area_images, had_thermal)

    dl1, dl2, dl3 = st.columns(3)
    with dl1:
        st.download_button(
            "⬇️ Download PDF Report", data=pdf_bytes,
            file_name=f"DDR_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
        )
    with dl2:
        st.download_button(
            "⬇️ Download JSON", data=json.dumps(data, indent=2),
            file_name=f"DDR_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
        )
    with dl3:
        if st.button("🔄 Generate New Report"):
            for k in ["ddr_data","had_thermal","area_images","thermal_matches"]:
                st.session_state.pop(k, None)
            st.rerun()