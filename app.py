import json
import os
import re
import streamlit as st
import google.generativeai as genai  # Google Generative AI eklendi

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

# ── SABİTLER ────────────────────────────────────────────────────────────────

EMBEDDING_MODEL   = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
SIMILARITY_THRESHOLD = 0.45
TOP_K_GENERATION  = 10

# API Anahtarı Ayarı (Streamlit secrets veya Çevresel değişken kullanılabilir)
GEMINI_API_KEY = "AIzaSyD-jJcslajaE24-yzNTJf2URLhAW2y_UQQ" 
genai.configure(api_key=GEMINI_API_KEY)

# Metadata sözlükleri korunuyor
DURUM_ESLEME = {
    "iptal": "iptal edildi", "iptal edildi": "iptal edildi",
    "yolda": "yolda", "teslim": "teslim edildi",
    "teslim edildi": "teslim edildi", "hazirlaniyor": "hazirlaniyor",
    "hazırlanıyor": "hazirlaniyor", "bekliyor": "hazirlaniyor",
}

KATEGORI_ESLEME = {
    "fast food": "Fast Food", "burger": "Fast Food", "hamburger": "Fast Food",
    "pizza": "Pizza", "sushi": "Sushi", "kebap": "Kebap",
    "döner": "Döner", "cafe": "Cafe", "kahve": "Cafe", "tatlı": "Tatlı",
}

# ── 1-4. VERİ YÜKLEME, CHUNKİNG, EMBEDDİNG, İNDEKSLEME ────────────────────
@st.cache_resource(show_spinner="Veri seti yükleniyor...")
def load_vector_db():
    with open("dataset.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    docs = []
    siparis_index = {}

    for item in data:
        sid, restoran, kategori, urunler, durum = item.get("id"), item.get("restoran"), item.get("kategori"), item.get("urunler", []), item.get("durum")
        siparis_index[sid] = item
        base_meta = {"siparis_id": sid, "restoran": restoran, "kategori": kategori, "durum": durum}
        
        # Chunking mantığı (Genel, Ürün, Durum)
        docs.append(Document(page_content=f"Sipariş {sid}. {restoran} {kategori}. Ürünler: {', '.join(urunler)}. Durum: {durum}", metadata={**base_meta, "chunk_turu": "genel"}))
        docs.append(Document(page_content=f"{restoran} ürünleri: {', '.join(urunler)}", metadata={**base_meta, "chunk_turu": "urun"}))
        docs.append(Document(page_content=f"Sipariş durumu: {durum}. Restoran: {restoran}", metadata={**base_meta, "chunk_turu": "durum"}))

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL, model_kwargs={"device": "cpu"}, encode_kwargs={"normalize_embeddings": True})
    db = FAISS.from_documents(docs, embeddings)
    return db, siparis_index, len(data)

db, siparis_index, toplam_siparis = load_vector_db()

# ── 5-7. METADATA FİLTRELEME & RETRIEVAL ───────────────────────────────────
def metadata_filtresi_cikar(soru: str) -> dict:
    soru_kucuk = soru.lower()
    filtre = {}
    for k, v in DURUM_ESLEME.items():
        if k in soru_kucuk: filtre["durum"] = v; break
    for k, v in KATEGORI_ESLEME.items():
        if k in soru_kucuk: filtre["kategori"] = v; break
    return filtre

def retrieve_ve_rerank(soru: str, esik: float) -> list[dict]:
    meta_filtre = metadata_filtresi_cikar(soru)
    ham_sonuclar = db.similarity_search_with_score(soru, k=toplam_siparis*3)
    siparis_skorlari = {}

    for doc, l2_mesafe in ham_sonuclar:
        cosine_sim = max(0.0, 1.0 - (l2_mesafe ** 2) / 2.0)
        if cosine_sim < esik: continue
        
        meta = doc.metadata
        if meta_filtre and any(meta.get(k) != v for k, v in meta_filtre.items()): continue

        sid = meta.get("siparis_id")
        if sid not in siparis_skorlari:
            siparis_skorlari[sid] = {"maks_skor": cosine_sim, "chunk_turleri": set()}
        siparis_skorlari[sid]["maks_skor"] = max(siparis_skorlari[sid]["maks_skor"], cosine_sim)
        siparis_skorlari[sid]["chunk_turleri"].add(meta.get("chunk_turu"))

    siralandi = sorted(siparis_skorlari.items(), key=lambda x: x[1]["maks_skor"], reverse=True)
    return [{"siparis": siparis_index[sid], "skor": b["maks_skor"], "chunk_turleri": sorted(b["chunk_turleri"])} for sid, b in siralandi]

# ── 8. GENERATION — Gemini API Entegrasyonu ────────────────────────────────
def llm_yanit_uret(soru: str, sonuclar: list[dict], meta_filtre: dict) -> str:
    """Claude yerine Google Gemini 2.5 Flash kullanır."""
    if not sonuclar: return None

    baglam_parcalari = []
    for i, s in enumerate(sonuclar[:TOP_K_GENERATION], 1):
        sp = s["siparis"]
        baglam_parcalari.append(f"[Sipariş {i}] ID: {sp['id']} | Restoran: {sp['restoran']} | Ürünler: {', '.join(sp['urunler'])} | Durum: {sp['durum']}")

    baglam = "\n".join(baglam_parcalari)
    
    # Gemini Sistem Komutu ve Prompt Yapılandırması
    prompt = f"""Sen bir restoran sipariş takip asistanısın. Aşağıdaki bağlamı kullanarak soruyu yanıtla.
    
Kurallar:
- Sadece verilen bağlamı kullan.
- Yanıtı Türkçe, net ve kısa tut.
- Kaç sipariş bulunduğunu belirt.

Bağlam:
{baglam}

Soru: {soru}
Yanıt:"""

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Gemini API Hatası: {str(e)}"

# ── STREAMLİT ARAYÜZÜ (Görsel kısımlar korunmuştur) ──────────────────────────
# --- API KEY OKUMA ---
api_dosyasi = "GoogleAPIkeys.txt"
GEMINI_API_KEY = ""

if os.path.exists(api_dosyasi):
    with open(api_dosyasi, "r", encoding="utf-8") as f:
        GEMINI_API_KEY = f.read().strip()
# ---------------------

# (Sidebar ve Mesaj Döngüsü orijinal kodla aynıdır...)
# [Orijinal kodunuzdaki Sidebar ve Sohbet akışını buraya ekleyebilirsiniz]

with st.sidebar:
    esik = st.slider("Benzerlik Eşiği", 0.10, 0.95, SIMILARITY_THRESHOLD)
    llm_aktif = st.toggle("Gemini Yanıt Üretimi", value=True)

    st.divider()
    st.markdown("### 🔑 API Ayarları")

    # value=GEMINI_API_KEY parametresini ekledik
    yeni_key = st.text_input("Gemini API Key", value=GEMINI_API_KEY, type="password")

    if st.button("Kaydet"):
        if yeni_key:
            with open(api_dosyasi, "w", encoding="utf-8") as f:
                f.write(yeni_key)
            st.success("API Key başarıyla kaydedildi! Sistem yenileniyor...")
            st.rerun()
        else:
            st.error("Lütfen kutuyu boş bırakmayın!")

genai.configure(api_key=GEMINI_API_KEY)
if "messages" not in st.session_state: st.session_state.messages = []
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

soru = st.chat_input("Siparişleri sorun...")
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"): st.markdown(soru)

    with st.chat_message("assistant"):
        with st.status("Gemini & RAG çalışıyor..."):
            meta_filtre = metadata_filtresi_cikar(soru)
            sonuclar = retrieve_ve_rerank(soru, esik)
        
        if not sonuclar:
            ana_cevap = "Sonuç bulunamadı."
        elif llm_aktif:
            ana_cevap = llm_yanit_uret(soru, sonuclar, meta_filtre)
        else:
            ana_cevap = f"{len(sonuclar)} sipariş listelendi (LLM kapalı)."

        st.markdown(ana_cevap)
        with st.expander("🔍 Teknik Detaylar"):
            st.write(sonuclar)

    st.session_state.messages.append({"role": "assistant", "content": ana_cevap})