import streamlit as st
import google.generativeai as genai
import base64
import json
import re
import tempfile
import os
from datetime import datetime

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="UrbanRoof DDR Generator",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Header */
.ur-header {
    background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
    border-radius: 12px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 16px;
}
.ur-header-logo {
    width: 48px; height: 48px;
    background: #F5A623;
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px; font-weight: 700; color: white;
    flex-shrink: 0;
}
.ur-header-title {
    font-family: 'DM Serif Display', serif;
    font-size: 26px; font-weight: 400;
    color: white; margin: 0;
}
.ur-header-sub {
    font-size: 13px; color: rgba(255,255,255,0.55);
    margin: 2px 0 0;
}

/* Upload cards */
.upload-card {
    background: white;
    border: 1.5px dashed #e0e0e0;
    border-radius: 12px;
    padding: 1.5rem;
    text-align: center;
    transition: border-color 0.2s;
}
.upload-card:hover { border-color: #F5A623; }

/* Report sections */
.report-wrapper {
    background: white;
    border-radius: 12px;
    border: 1px solid #f0f0f0;
    overflow: hidden;
    margin-top: 1.5rem;
}
.report-top-bar {
    background: #1a1a1a;
    padding: 1.75rem 2rem;
    color: white;
}
.report-top-bar h2 {
    font-family: 'DM Serif Display', serif;
    font-size: 24px; font-weight: 400;
    color: white; margin: 0 0 4px;
}
.report-top-bar p { font-size: 13px; color: rgba(255,255,255,0.5); margin: 0; }

.section-wrap {
    padding: 1.5rem 2rem;
    border-bottom: 1px solid #f5f5f5;
}
.section-tag {
    font-size: 10px; font-weight: 600;
    letter-spacing: 0.8px; text-transform: uppercase;
    color: #888; margin-bottom: 6px;
    display: flex; align-items: center; gap: 6px;
}
.section-tag-dot {
    width: 6px; height: 6px;
    border-radius: 50%; background: #F5A623;
    display: inline-block;
}
.section-title {
    font-family: 'DM Serif Display', serif;
    font-size: 20px; font-weight: 400;
    color: #1a1a1a; margin: 0 0 1rem;
}

/* Metric cards */
.metric-row {
    display: flex; gap: 12px; margin-bottom: 1rem;
    flex-wrap: wrap;
}
.metric-card {
    background: #fafafa;
    border: 1px solid #f0f0f0;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    min-width: 120px;
}
.metric-label { font-size: 11px; color: #999; margin-bottom: 4px; }
.metric-value { font-size: 22px; font-weight: 500; color: #1a1a1a; }

/* Area cards */
.area-card {
    background: #fafafa;
    border: 1px solid #f0f0f0;
    border-radius: 8px;
    padding: 1rem 1.25rem;
    margin-bottom: 10px;
}
.area-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
}
.area-name { font-size: 14px; font-weight: 500; color: #1a1a1a; }

/* Severity badges */
.badge-high { background: #FCEBEB; color: #A32D2D; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 500; }
.badge-moderate { background: #FAEEDA; color: #854F0B; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 500; }
.badge-low { background: #EAF3DE; color: #3B6D11; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 500; }
.badge-na { background: #f5f5f5; color: #888; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 500; }

.thermal-note {
    background: #E6F1FB; border-left: 3px solid #185FA5;
    border-radius: 0 4px 4px 0;
    padding: 8px 10px; margin-top: 8px;
    font-size: 12px; color: #0C447C; line-height: 1.5;
}

/* Action items */
.action-item {
    display: flex; gap: 12px; margin-bottom: 12px; align-items: flex-start;
}
.action-num {
    width: 26px; height: 26px; border-radius: 50%;
    background: #F5A623; color: white;
    font-size: 11px; font-weight: 600;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
}
.action-title { font-size: 14px; font-weight: 500; color: #1a1a1a; margin-bottom: 3px; }
.action-desc { font-size: 13px; line-height: 1.6; color: #666; }

/* Root cause */
.cause-row {
    display: flex; gap: 10px; margin-bottom: 10px; align-items: flex-start;
}
.cause-icon {
    width: 20px; height: 20px; border-radius: 4px;
    background: #FCEBEB; color: #A32D2D;
    font-size: 11px; font-weight: 700;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; margin-top: 2px;
}
.cause-text { font-size: 13px; line-height: 1.6; color: #555; }

/* Missing items */
.missing-item {
    display: flex; gap: 8px; align-items: flex-start;
    padding: 8px 12px; background: #fafafa;
    border: 1px solid #f0f0f0; border-radius: 8px;
    margin-bottom: 8px; font-size: 13px; color: #666;
}
.missing-tag {
    font-size: 10px; font-weight: 600;
    color: #854F0B; background: #FAEEDA;
    padding: 2px 6px; border-radius: 4px;
    white-space: nowrap;
}

/* Disclaimer */
.disclaimer {
    background: #fafafa; border: 1px solid #f0f0f0;
    border-radius: 8px; padding: 1rem;
    font-size: 12px; color: #888; line-height: 1.6;
    margin-top: 1.5rem;
}

/* Strimlit override tweaks */
div[data-testid="stFileUploader"] { border: none !important; }
.stButton button {
    background: #F5A623 !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: 14px !important;
    padding: 0.6rem 1.5rem !important;
    width: 100%;
}
.stButton button:hover { opacity: 0.88 !important; }
</style>
""", unsafe_allow_html=True)


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="ur-header">
    <div class="ur-header-logo">UR</div>
    <div>
        <p class="ur-header-title">UrbanRoof DDR Generator</p>
        <p class="ur-header-sub">AI-powered Detailed Diagnosis Report from inspection &amp; thermal data</p>
    </div>
</div>
""", unsafe_allow_html=True)


# ── API Key ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    api_key = st.text_input(
        "Google Gemini API Key",
        type="password",
        placeholder="AIza...",
        help="Get your key at aistudio.google.com/app/apikey",
    )
    st.markdown("---")
    st.markdown("**How to use:**")
    st.markdown("1. Enter your Gemini API key above")
    st.markdown("2. Upload Inspection Report PDF")
    st.markdown("3. Upload Thermal Images PDF (optional)")
    st.markdown("4. Click Generate")
    st.markdown("---")
    st.markdown("**Works with any:**")
    st.markdown("- Flat / apartment reports")
    st.markdown("- Row house / bungalow reports")
    st.markdown("- CHS building reports")
    st.markdown("- Any number of impacted areas")
    st.markdown("- With or without thermal PDF")
    st.markdown("---")
    st.markdown("**Report includes:**")
    st.markdown("- Property issue summary")
    st.markdown("- Area-wise observations")
    st.markdown("- Root cause analysis")
    st.markdown("- Severity assessment")
    st.markdown("- Recommended actions")
    st.markdown("- Missing info flags")


# ── File Upload ───────────────────────────────────────────────────────────────
st.markdown("### 📂 Upload Documents")
st.markdown(
    "<p style='font-size:13px;color:#888;margin-bottom:1rem;'>"
    "Upload any UrbanRoof inspection documents. The AI adapts to whatever property type, "
    "number of areas, and report format you provide — no configuration needed."
    "</p>",
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Inspection Report** *(required)*")
    inspection_file = st.file_uploader(
        "inspection_upload",
        type=["pdf"],
        key="inspection",
        label_visibility="collapsed",
        help="Upload the inspection / sample report PDF",
    )
    if inspection_file:
        st.success(f"✅ {inspection_file.name}")

with col2:
    st.markdown("**Thermal Images Report** *(optional)*")
    thermal_file = st.file_uploader(
        "thermal_upload",
        type=["pdf"],
        key="thermal",
        label_visibility="collapsed",
        help="Upload the thermal imaging PDF if available",
    )
    if thermal_file:
        st.success(f"✅ {thermal_file.name}")
    else:
        st.info("ℹ️ No thermal PDF uploaded — report will be generated from inspection data only.")

st.markdown("<br>", unsafe_allow_html=True)

ready = inspection_file is not None and api_key
if not api_key:
    st.info("👈 Enter your Google Gemini API key in the sidebar to get started.")
elif not inspection_file:
    st.info("Upload at least the Inspection Report PDF above to enable report generation.")


# ── Generate ──────────────────────────────────────────────────────────────────
if st.button("🔍 Generate Detailed Diagnosis Report", disabled=not ready):

    # ── Read files ──────────────────────────────────────────────────────────
    inspection_bytes = inspection_file.read()
    thermal_bytes = thermal_file.read() if thermal_file else None

    # ── Prompts ─────────────────────────────────────────────────────────────
    system_prompt = """You are UrbanRoof's expert building diagnostics AI. You analyze inspection forms
and thermal imaging reports to generate professional Detailed Diagnosis Reports (DDR).

IMPORTANT — DYNAMIC DOCUMENT RULES:
- Every uploaded document may be different: the property type, number of floors, number of impacted
  areas, checklist structure, and thermal data format can all vary between jobs.
- Do NOT assume fixed area names, fixed number of issues, or fixed document layouts.
- Read whatever is actually in the documents and extract ALL areas, observations, and findings present.
- If a thermal document is provided, correlate its temperature readings to the visual observations.
- If NO thermal document is provided, set thermalData to "Not Available" for all areas.
- If a field is genuinely absent from the documents, write exactly: "Not Available"
- Do NOT invent, assume, or hallucinate any data not present in the documents.
- If two documents conflict on a detail, note it in additionalNotes.
- Use plain, client-friendly language — avoid excessive jargon.

You MUST respond with ONLY valid JSON, no markdown fences, no preamble, no explanation.
The JSON structure must be exactly:

{
  "property": {
    "address": "full address or Not Available",
    "type": "Flat / Row House / Bungalow / CHS / etc. or Not Available",
    "age": "age in years or Not Available",
    "floors": "number of floors or Not Available",
    "inspectedBy": "inspector name(s) or Not Available",
    "inspectionDate": "date or Not Available",
    "overallScore": "score percentage if present or Not Available",
    "previousAudit": "Yes / No / Not Available",
    "previousRepairs": "Yes / No / Not Available"
  },
  "summary": {
    "totalIssues": <integer — count of distinct impacted areas>,
    "criticalAreas": <integer — count of High severity areas>,
    "areasInspected": <integer — total areas inspected>,
    "overallCondition": "Good / Moderate / Poor — your assessment based on findings"
  },
  "areas": [
    {
      "name": "Exact area name from the document (e.g. Hall Skirting, Master Bedroom Bathroom, Parking Ceiling)",
      "severity": "High / Moderate / Low — based on leak type, dampness level, structural risk",
      "negativeFindings": "What damage/dampness/leakage is observed on the impacted (negative) side",
      "positiveFindings": "What root-cause issue is observed on the source (positive) side",
      "thermalData": "Hotspot °C, Coldspot °C, and interpretation — or Not Available"
    }
  ],
  "rootCauses": [
    "Each distinct root cause as a separate string — e.g. gaps in tile grout joints allowing capillary moisture rise"
  ],
  "severityReasoning": "A short paragraph explaining how you assessed severity across the property",
  "actions": [
    {
      "title": "Short action name",
      "priority": "Immediate / Short-term / Long-term",
      "description": "Step-by-step repair method in plain language"
    }
  ],
  "additionalNotes": "Conflicts between documents, unusual findings, or anything the client should be aware of — or Not Available",
  "missingInfo": [
    "Each piece of information that was absent or unclear in the provided documents"
  ]
}"""

    has_thermal = thermal_bytes is not None
    user_prompt = f"""Analyze the uploaded PDF document(s) and generate a complete DDR JSON.

Documents provided:
- DOCUMENT 1: Inspection Report — contains site observations, impacted area descriptions, checklist responses, and photos
{"- DOCUMENT 2: Thermal Images Report — contains thermal camera readings with hotspot/coldspot temperatures for various locations" if has_thermal else "- No thermal document was uploaded. Set thermalData to 'Not Available' for all areas."}

Extract EVERY impacted area listed in the inspection document.
{"Cross-reference thermal temperature readings with each corresponding visual observation." if has_thermal else ""}
Return ONLY the JSON — no other text."""

    with st.spinner("🤖 Gemini is reading your documents and building the report…"):
        try:
            # Configure Gemini
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                model_name="gemini-1.5-pro",
                generation_config=genai.GenerationConfig(
                    temperature=0.1,       # Low temp = consistent, factual output
                    response_mime_type="application/json",  # Force JSON output
                ),
                system_instruction=system_prompt,
            )

            # Build content parts — inspection PDF always included
            content_parts = []

            # Upload inspection PDF via Gemini Files API
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp1:
                tmp1.write(inspection_bytes)
                tmp1_path = tmp1.name

            inspection_gemini = genai.upload_file(
                path=tmp1_path,
                mime_type="application/pdf",
                display_name=inspection_file.name,
            )
            content_parts.append(inspection_gemini)
            os.unlink(tmp1_path)

            # Upload thermal PDF only if provided
            if has_thermal:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp2:
                    tmp2.write(thermal_bytes)
                    tmp2_path = tmp2.name

                thermal_gemini = genai.upload_file(
                    path=tmp2_path,
                    mime_type="application/pdf",
                    display_name=thermal_file.name,
                )
                content_parts.append(thermal_gemini)
                os.unlink(tmp2_path)

            content_parts.append(user_prompt)

            # Call Gemini
            response = model.generate_content(content_parts)
            raw_text = response.text.strip()

            # Parse JSON — strip any accidental markdown fences
            cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text)
            cleaned = re.sub(r"\s*```$", "", cleaned).strip()

            json_match = re.search(r"\{[\s\S]*\}", cleaned)
            if not json_match:
                st.error("Could not extract valid JSON from Gemini response.")
                with st.expander("Raw Gemini output (for debugging)"):
                    st.code(raw_text[:3000])
                st.stop()

            data = json.loads(json_match.group())
            st.session_state["ddr_data"] = data
            st.session_state["had_thermal"] = has_thermal

        except json.JSONDecodeError as e:
            st.error(f"❌ Failed to parse Gemini response as JSON: {e}")
            with st.expander("Raw output"):
                st.code(raw_text[:3000])
            st.stop()
        except Exception as e:
            err_str = str(e)
            if "API_KEY_INVALID" in err_str or "API key" in err_str.lower():
                st.error("❌ Invalid Gemini API key. Get one at https://aistudio.google.com/app/apikey")
            elif "quota" in err_str.lower() or "429" in err_str:
                st.error("❌ Gemini quota exceeded. Wait a moment and try again, or upgrade your plan.")
            elif "safety" in err_str.lower():
                st.error("❌ Gemini safety filter triggered. The document content may have been flagged.")
            else:
                st.error(f"❌ Unexpected error: {err_str}")
            st.stop()


# ── Render Report ─────────────────────────────────────────────────────────────
def severity_badge(sev: str) -> str:
    if not sev:
        return '<span class="badge-na">N/A</span>'
    s = sev.lower()
    if "high" in s or "critical" in s:
        return f'<span class="badge-high">{sev}</span>'
    if "moderate" in s or "medium" in s:
        return f'<span class="badge-moderate">{sev}</span>'
    if "low" in s or "good" in s:
        return f'<span class="badge-low">{sev}</span>'
    return f'<span class="badge-na">{sev}</span>'


def priority_badge(priority: str) -> str:
    p = (priority or "").lower()
    if "immediate" in p:
        return '<span style="font-size:10px;font-weight:600;background:#FCEBEB;color:#A32D2D;padding:2px 8px;border-radius:20px;">Immediate</span>'
    if "short" in p:
        return '<span style="font-size:10px;font-weight:600;background:#FAEEDA;color:#854F0B;padding:2px 8px;border-radius:20px;">Short-term</span>'
    if "long" in p:
        return '<span style="font-size:10px;font-weight:600;background:#EAF3DE;color:#3B6D11;padding:2px 8px;border-radius:20px;">Long-term</span>'
    return ""


if "ddr_data" in st.session_state:
    data = st.session_state["ddr_data"]
    had_thermal = st.session_state.get("had_thermal", False)

    prop    = data.get("property", {})
    summ    = data.get("summary", {})
    areas   = data.get("areas", [])
    causes  = data.get("rootCauses", [])
    sev_reasoning = data.get("severityReasoning", "")
    actions = data.get("actions", [])
    notes   = data.get("additionalNotes", "")
    missing = data.get("missingInfo", [])

    generated_on = datetime.now().strftime("%d %b %Y, %I:%M %p")

    # ── Report header ────────────────────────────────────────────────────────
    addr  = prop.get("address", "Property")
    ptype = prop.get("type", "Structure")
    st.markdown(f"""
    <div style="background:#1a1a1a;border-radius:12px 12px 0 0;padding:1.75rem 2rem;margin-top:1.5rem;">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:1rem;">
            <div style="display:flex;align-items:center;gap:10px;">
                <div style="width:32px;height:32px;background:#F5A623;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;color:white;">UR</div>
                <span style="font-size:14px;font-weight:500;color:white;">UrbanRoof Private Limited</span>
            </div>
            <div style="font-size:11px;color:rgba(255,255,255,0.4);text-align:right;">
                <div>Detailed Diagnosis Report</div>
                <div>Generated: {generated_on}</div>
                <div style="margin-top:3px;color:rgba(255,255,255,0.3);">{"Inspection + Thermal" if had_thermal else "Inspection only"}</div>
            </div>
        </div>
        <h2 style="font-family:'DM Serif Display',serif;font-size:26px;font-weight:400;color:white;margin:0 0 4px;">
            Detailed Diagnosis Report
        </h2>
        <p style="font-size:13px;color:rgba(255,255,255,0.5);margin:0;">{addr} — {ptype}</p>
    </div>
    <div style="border:1px solid #f0f0f0;border-top:none;border-radius:0 0 12px 12px;background:white;">
    """, unsafe_allow_html=True)

    # ── Section 1 — Property Summary ─────────────────────────────────────────
    st.markdown("""
    <div class="section-wrap">
        <div class="section-tag"><span class="section-tag-dot"></span>Overview</div>
        <p class="section-title">Property Issue Summary</p>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Issues Identified", summ.get("totalIssues", len(areas)))
    with c2:
        st.metric("Areas Inspected", summ.get("areasInspected", len(areas)))
    with c3:
        st.metric("Overall Condition", summ.get("overallCondition", "Moderate"))

    st.markdown(f"""
    <table style="font-size:13px;color:#555;width:100%;margin-top:0.75rem;border-collapse:collapse;">
        <tr><td style="padding:5px 0;width:160px;color:#999;">Address</td><td>{prop.get('address','Not Available')}</td></tr>
        <tr><td style="padding:5px 0;color:#999;">Property type</td><td>{prop.get('type','Not Available')}</td></tr>
        <tr><td style="padding:5px 0;color:#999;">Building age</td><td>{prop.get('age','Not Available')}</td></tr>
        <tr><td style="padding:5px 0;color:#999;">Floors</td><td>{prop.get('floors','Not Available')}</td></tr>
        <tr><td style="padding:5px 0;color:#999;">Inspected by</td><td>{prop.get('inspectedBy','Not Available')}</td></tr>
        <tr><td style="padding:5px 0;color:#999;">Inspection date</td><td>{prop.get('inspectionDate','Not Available')}</td></tr>
        <tr><td style="padding:5px 0;color:#999;">Previous audit</td><td>{prop.get('previousAudit','Not Available')}</td></tr>
        <tr><td style="padding:5px 0;color:#999;">Previous repairs</td><td>{prop.get('previousRepairs','Not Available')}</td></tr>
        <tr><td style="padding:5px 0;color:#999;">Inspection score</td><td>{prop.get('overallScore','Not Available')}</td></tr>
    </table>
    </div>
    """, unsafe_allow_html=True)

    # ── Section 2 — Area-wise Observations ───────────────────────────────────
    st.markdown("""
    <div class="section-wrap">
        <div class="section-tag"><span class="section-tag-dot"></span>Area-wise findings</div>
        <p class="section-title">Visual Observation & Thermal Readings</p>
    """, unsafe_allow_html=True)

    if not areas:
        st.markdown(
            '<p style="color:#999;font-size:13px;">No impacted areas were extracted from the document.</p>',
            unsafe_allow_html=True,
        )
    else:
        for area in areas:
            neg   = area.get("negativeFindings", "")
            pos   = area.get("positiveFindings", "")
            therm = area.get("thermalData", "Not Available")

            thermal_html = ""
            if therm and therm.strip().lower() not in ("not available", "n/a", ""):
                thermal_html = f'<div class="thermal-note">🌡️ Thermal reading: {therm}</div>'

            st.markdown(f"""
            <div class="area-card">
                <div class="area-header">
                    <span class="area-name">{area.get('name','Area')}</span>
                    {severity_badge(area.get('severity',''))}
                </div>
                <div style="font-size:13px;line-height:1.65;color:#555;">
                    {"<p><strong style='color:#1a1a1a;'>Damage observed (negative side):</strong><br>" + neg + "</p>" if neg else ""}
                    {"<p style='margin-top:6px;'><strong style='color:#1a1a1a;'>Root cause area (positive side):</strong><br>" + pos + "</p>" if pos else ""}
                    {thermal_html}
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Section 3 — Root Causes ───────────────────────────────────────────────
    st.markdown("""
    <div class="section-wrap">
        <div class="section-tag"><span class="section-tag-dot"></span>Diagnosis</div>
        <p class="section-title">Probable Root Causes</p>
    """, unsafe_allow_html=True)

    if not causes:
        st.markdown('<p style="color:#999;font-size:13px;">Not Available</p>', unsafe_allow_html=True)
    else:
        for cause in causes:
            st.markdown(f"""
            <div class="cause-row">
                <div class="cause-icon">!</div>
                <div class="cause-text">{cause}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Section 4 — Severity Assessment ──────────────────────────────────────
    high_count = sum(1 for a in areas if "high" in a.get("severity","").lower() or "critical" in a.get("severity","").lower())
    mod_count  = sum(1 for a in areas if "moderate" in a.get("severity","").lower())
    low_count  = sum(1 for a in areas if "low" in a.get("severity","").lower())

    st.markdown("""
    <div class="section-wrap">
        <div class="section-tag"><span class="section-tag-dot"></span>Severity assessment</div>
        <p class="section-title">Issue Severity Overview</p>
    """, unsafe_allow_html=True)

    s1, s2, s3 = st.columns(3)
    with s1:
        st.markdown(f"""
        <div style="background:#FCEBEB;border-radius:8px;padding:0.75rem 1rem;text-align:center;">
            <div style="font-size:11px;color:#A32D2D;margin-bottom:4px;">High severity</div>
            <div style="font-size:28px;font-weight:500;color:#A32D2D;">{high_count}</div>
        </div>""", unsafe_allow_html=True)
    with s2:
        st.markdown(f"""
        <div style="background:#FAEEDA;border-radius:8px;padding:0.75rem 1rem;text-align:center;">
            <div style="font-size:11px;color:#854F0B;margin-bottom:4px;">Moderate severity</div>
            <div style="font-size:28px;font-weight:500;color:#854F0B;">{mod_count}</div>
        </div>""", unsafe_allow_html=True)
    with s3:
        st.markdown(f"""
        <div style="background:#EAF3DE;border-radius:8px;padding:0.75rem 1rem;text-align:center;">
            <div style="font-size:11px;color:#3B6D11;margin-bottom:4px;">Low severity</div>
            <div style="font-size:28px;font-weight:500;color:#3B6D11;">{low_count}</div>
        </div>""", unsafe_allow_html=True)

    if sev_reasoning:
        st.markdown(
            f'<p style="font-size:13px;color:#666;line-height:1.65;margin-top:1rem;">{sev_reasoning}</p>',
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Section 5 — Recommended Actions ──────────────────────────────────────
    st.markdown("""
    <div class="section-wrap">
        <div class="section-tag"><span class="section-tag-dot"></span>Recommended actions</div>
        <p class="section-title">Suggested Therapies & Repairs</p>
    """, unsafe_allow_html=True)

    if not actions:
        st.markdown('<p style="color:#999;font-size:13px;">Not Available</p>', unsafe_allow_html=True)
    else:
        for i, action in enumerate(actions, 1):
            pri_html = priority_badge(action.get("priority", ""))
            st.markdown(f"""
            <div class="action-item">
                <div class="action-num">{i}</div>
                <div>
                    <div class="action-title">
                        {action.get('title','Action')}
                        &nbsp;{pri_html}
                    </div>
                    <div class="action-desc">{action.get('description','')}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Section 6 — Additional Notes ─────────────────────────────────────────
    if notes and notes.strip().lower() not in ("not available", "n/a", "none", ""):
        st.markdown(f"""
        <div class="section-wrap">
            <div class="section-tag"><span class="section-tag-dot"></span>Notes</div>
            <p class="section-title">Additional Notes</p>
            <p style="font-size:13px;line-height:1.75;color:#555;">{notes}</p>
        </div>
        """, unsafe_allow_html=True)

    # ── Section 7 — Missing Information ──────────────────────────────────────
    st.markdown("""
    <div class="section-wrap" style="border-bottom:none;">
        <div class="section-tag"><span class="section-tag-dot"></span>Data gaps</div>
        <p class="section-title">Missing or Unclear Information</p>
    """, unsafe_allow_html=True)

    if not missing:
        st.markdown(
            '<p style="font-size:13px;color:#3B6D11;">✅ All required information was successfully extracted from the provided documents.</p>',
            unsafe_allow_html=True,
        )
    else:
        for m in missing:
            st.markdown(f"""
            <div class="missing-item">
                <span class="missing-tag">Not Available</span>
                <span>{m}</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("</div></div>", unsafe_allow_html=True)

    # ── Disclaimer ────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="disclaimer">
        This report is AI-generated based on the uploaded inspection and thermal documents.
        It is intended as a diagnostic summary and does not replace a full structural engineering assessment.
        All findings should be verified on-site by a qualified professional before initiating repairs.
        UrbanRoof Private Limited accepts no liability for decisions made solely based on this AI-generated report.
    </div>
    """, unsafe_allow_html=True)

    # ── Download + Reset ──────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button(
            label="⬇️ Download Report (JSON)",
            data=json.dumps(data, indent=2),
            file_name=f"DDR_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
        )
    with col_dl2:
        if st.button("🔄 Generate New Report"):
            del st.session_state["ddr_data"]
            st.session_state.pop("had_thermal", None)
            st.rerun()