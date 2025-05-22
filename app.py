import streamlit as st
import tempfile
import easyocr
import json
import re
from pdf2image import convert_from_path
import os

st.set_page_config(page_title="iBOB Dashboard", layout="wide")
st.title("📄 iBOB PDF Analyse")

uploaded_file = st.file_uploader("Upload een PDF-bestand", type=["pdf"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        temp_pdf_path = tmp_file.name

    st.success(f"✅ Bestand '{uploaded_file.name}' ontvangen. OCR wordt uitgevoerd...")

    reader = easyocr.Reader(['nl', 'en'], gpu=False)
    images = convert_from_path(temp_pdf_path, dpi=200)
    output = []

    TAGS = {
        'kosten': r"(€|\beuro\b|\btotaal\b|\bkost)",
        'materiaal': r"(hout|staal|isolatie|materiaal)",
        'planning': r"(planning|week|maand|jaar|fasering)",
        'juridisch': r"(aansprakelijk|vergunning|bestek|contract|arw)"
    }

    def tag_line(text):
        tags = []
        for key, pattern in TAGS.items():
            if re.search(pattern, text, re.IGNORECASE):
                tags.append(key)
        return tags

    for page_num, image in enumerate(images, start=1):
        result = reader.readtext(image, detail=0)
        for line in result:
            line = line.strip()
            if len(line) < 3:
                continue
            tags = tag_line(line)
            output.append({
                "pagina": page_num,
                "regel": line,
                "tags": tags
            })

    json_path = "ocr_getagd.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    st.success(f"📄 OCR voltooid. {len(output)} regels opgeslagen in `{json_path}`.")
    st.download_button("📥 Download JSON-resultaat", data=json.dumps(output, indent=2), file_name="ocr_getagd.json", mime="application/json")

    with st.expander("📊 Voorbeeld van getagde regels"):
        for item in output[:20]:
            st.markdown(f"**Pg {item['pagina']}** — *{item['regel']}*")
            st.markdown(f"`Tags:` {', '.join(item['tags']) if item['tags'] else 'geen'}")
