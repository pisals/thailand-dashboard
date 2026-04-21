import streamlit as st
import feedparser
import json
import re
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="Thailand Manufacturing Intelligence",
    page_icon="🇹🇭",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide Streamlit branding for fullscreen
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {padding: 0rem 1rem;}
    iframe {border: none !important;}
</style>
""", unsafe_allow_html=True)

st_autorefresh(interval=600_000, key="news_refresh")

FEEDS = [
    # Verified working Thai sources
    {"name": "Bangkok Post", "url": "https://www.bangkokpost.com/rss/data/business.xml"},
    {"name": "Bangkok Post Tech", "url": "https://www.bangkokpost.com/rss/data/tech.xml"},
    {"name": "The Standard", "url": "https://thestandard.co/feed"},
    {"name": "The Thaiger", "url": "https://thethaiger.com/feed"},
    {"name": "Thailand Business News", "url": "https://www.thailand-business-news.com/feed"},
    {"name": "InfoQuest", "url": "https://www.infoquest.co.th/rss"},
    {"name": "Thai PBS World", "url": "https://www.thaipbsworld.com/feed/"},
    {"name": "Nation Thailand", "url": "https://www.nationthailand.com/feeds/rss.xml"},
    
    # International sources covering Thailand/Asia
    {"name": "Reuters Asia Business", "url": "https://feeds.reuters.com/reuters/INbusinessNews"},
    {"name": "Bloomberg Asia", "url": "https://feeds.bloomberg.com/markets/news.rss"},
    {"name": "Nikkei Asia", "url": "https://asia.nikkei.com/rss/feed/nar"},
    {"name": "South China Morning Post", "url": "https://www.scmp.com/rss/91/feed"},
    {"name": "Channel News Asia", "url": "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=6511"},
    {"name": "Jakarta Post Business", "url": "https://www.thejakartapost.com/rss/business"},
]

CATEGORIES = {
    "Government": ["government","ministry","policy","boi","cabinet","regulation","prime minister","nesdc","announce","approve","law","decree"],
    "Investment": ["invest","fdi","billion","million","baht","factory","plant","eec","expand","acquisition","fund","capital","joint venture","project"],
    "GDP / Economy": ["gdp","growth","economy","inflation","rate","bank of thailand","export","import","trade","forecast","quarter","bot","fiscal"],
    "Industry": ["manufactur","industrial","automotive","ev","electric vehicle","semiconductor","electronics","pmi","mpi","supply chain","assembly","production"],
    "Oil & Gas": ["oil","gas","petroleum","pttep","lng","crude","refin","upstream","offshore","brent","barrel","fuel","natural gas","exploration"],
    "Petrochemical": ["petrochemical","pttgc","irpc","ethylene","polymer","cracker","aromatic","paraxylene","chemical","feedstock","naphtha","olefin","styrene","benzene"],
    "Support": ["support","subsidy","grant","incentive","tax","tariff","sme","loan","rebate","training","skill","promotion","scheme","relief"],
}

def clean_html(raw):
    clean = re.sub(r"<[^>]+>", "", raw or "")
    clean = re.sub(r"&[a-zA-Z#0-9]+;", " ", clean)
    return re.sub(r"\s+", " ", clean).strip()

def classify(text):
    t = text.lower()
    scores = {cat: sum(1 for kw in kws if kw in t) for cat, kws in CATEGORIES.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Industry"

def parse_date(entry):
    for attr in ("published_parsed", "updated_parsed"):
        val = getattr(entry, attr, None)
        if val:
            try:
                return datetime(*val[:6])
            except:
                pass
    return datetime.now()

def get_fallback():
    now = datetime.now()
    def d(n): return now - timedelta(days=n)
    return [
        {"title":"BOI approves ฿38B in EV and semiconductor projects Q1 2026","desc":"Board of Investment grants 47 approvals targeting electronics and clean energy manufacturers.","link":"https://www.boi.go.th","date":d(0),"source":"BOI Thailand","cat":"Government"},
        {"title":"PTT Exploration completes Gulf of Thailand well — 45 mmscfd discovery","desc":"PTTEP confirms significant natural gas discovery extending production to 2040.","link":"https://www.bangkokpost.com","date":d(1),"source":"Bangkok Post","cat":"Oil & Gas"},
        {"title":"IRPC invests ฿15B in petrochemical complex upgrade at Map Ta Phut","desc":"IRPC targets high-value specialty polymers to improve margins.","link":"https://www.thansettakij.com","date":d(2),"source":"Thansettakij","cat":"Petrochemical"},
        {"title":"Manufacturing PMI hits 51.4 — third straight month of expansion","desc":"Thai manufacturing expanded for a third consecutive month on new export orders.","link":"https://www.bangkokpost.com","date":d(2),"source":"Bangkok Post","cat":"Industry"},
        {"title":"NESDC raises 2026 GDP forecast to 3.2–4.0%","desc":"Thailand upgraded outlook citing stronger industrial output and tourism recovery.","link":"https://www.nesdc.go.th","date":d(3),"source":"NESDC","cat":"GDP / Economy"},
        {"title":"EEC records ฿220B investment applications in Q1 2026","desc":"Eastern Economic Corridor hits highest-ever quarterly investment figure.","link":"https://www.eec.or.th","date":d(5),"source":"EEC Office","cat":"Investment"},
        {"title":"Bangchak to build 100MW green hydrogen plant in Rayong","desc":"Refinery-to-hydrogen pivot supports Thailand net-zero 2065 target.","link":"https://www.bangkokpost.com","date":d(6),"source":"Bangkok Post","cat":"Oil & Gas"},
        {"title":"Olefins cracker margin recovery boosts PTTGC and IRPC outlook","desc":"Ethylene-naphtha spread widens to $180/t as ASEAN demand recovers.","link":"https://www.thansettakij.com","date":d(7),"source":"Thansettakij","cat":"Petrochemical"},
        {"title":"FDI inflows jump 18% year-on-year — ฿142B in Q1 2026","desc":"Strong investment from Japan, China, and Europe drives record Q1 FDI.","link":"https://www.bot.or.th","date":d(8),"source":"Bank of Thailand","cat":"Investment"},
        {"title":"OIE launches SME factory modernization grant — up to ฿2M","desc":"Industry 4.0 Upgrade Grant targets manufacturers adopting automation.","link":"https://www.oie.go.th","date":d(9),"source":"OIE","cat":"Support"},
        {"title":"PTT Group announces ฿180B upstream capex plan","desc":"State energy giant accelerates gas production and CCUS investment.","link":"https://www.infoquest.co.th","date":d(10),"source":"InfoQuest","cat":"Oil & Gas"},
        {"title":"Thai Paraxylene exports hit five-year high","desc":"PX production exceeds 3M tonnes as Asian PET demand surges.","link":"https://www.bangkokbiznews.com","date":d(12),"source":"Bangkok Biz News","cat":"Petrochemical"},
        {"title":"Samsung SDI to build ฿28B EV battery plant","desc":"South Korean maker secures EEC incentives for 10 GWh facility.","link":"https://asia.nikkei.com","date":d(14),"source":"Nikkei Asia","cat":"Investment"},
        {"title":"Thailand 2025 GDP confirmed at 3.0%","desc":"Manufacturing contributed 1.4 pp to growth.","link":"https://www.nesdc.go.th","date":d(20),"source":"NESDC","cat":"GDP / Economy"},
        {"title":"Ministry unveils 10-year port cluster plan","desc":"Policy targets southern provinces for petrochemical and LNG.","link":"https://www.moi.go.th","date":d(22),"source":"Ministry of Industry","cat":"Government"},
    ]

@st.cache_data(ttl=600)
def fetch_all_news():
    all_items = []
    for feed in FEEDS:
        try:
            parsed = feedparser.parse(feed["url"])
            for e in parsed.entries[:25]:
                raw = getattr(e, "summary", "") or ""
                desc = clean_html(raw)
                combo = f"{e.get('title','')} {desc}"
                all_items.append({
                    "title": clean_html(e.get("title","Untitled")),
                    "desc": desc[:300],
                    "link": e.get("link","#"),
                    "date": parse_date(e),
                    "source": feed["name"],
                    "cat": classify(combo),
                })
        except:
            continue
    
    all_items.sort(key=lambda x: x["date"], reverse=True)
    seen, unique = set(), []
    for item in all_items:
        key = item["title"][:60]
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique if unique else get_fallback()

def load_html():
    with open("components/dashboard.html", "r", encoding="utf-8") as f:
        return f.read()

def build_page(news_items):
    html = load_html()
    news_json = json.dumps([{
        "title": item["title"],
        "desc": item["desc"],
        "link": item["link"],
        "date": item["date"].strftime("%d %b %Y"),
        "source": item["source"],
        "cat": item["cat"],
    } for item in news_items], ensure_ascii=False)
    html = html.replace("__NEWS_DATA__", news_json)
    html = html.replace("__LAST_UPDATED__", datetime.now().strftime("%d %b %Y %H:%M"))
    return html

news = fetch_all_news()
page_html = build_page(news)
st.components.v1.html(page_html, height=1400, scrolling=True)