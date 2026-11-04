# -*- coding: utf-8 -*-
"""
Programatik SEO: "{Şehir} Google Reklam Ajansı" şehir sayfalarını üretir.

Kullanım (depo kökünden):
    python3 tools/build_city_pages.py

- URL'ler değişmez: /{slug}-google-ads/
- İlçe listesi mevcut sayfadan okunur, sektör/ürün/bölge bilgisi tools/sehir_verisi.py'den gelir.
- Header, footer ve stil bloğu mevcut sayfadan korunur.
"""
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from sehir_verisi import SEKTORLER, SEHIRLER  # noqa: E402

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://www.webportalfaaliyetleri.com"
TEL = "+905451944026"
TEL_GORUNEN = "0545 194 40 26"
WA = "905451944026"
YIL = "2026"

EK_CSS = (
    ".kw-table{width:100%;border-collapse:collapse;margin-top:22px;font-size:14px;background:#fff;border-radius:12px;overflow:hidden}"
    ".kw-table th,.kw-table td{padding:12px 14px;border-bottom:1px solid #dce5e8;text-align:left;vertical-align:top}"
    ".kw-table th{background:#101a20;color:#fff;font-size:12px;letter-spacing:.6px}"
    ".kw-table td code{display:inline-block;margin:2px 4px 2px 0;background:#eef4f7;border-radius:6px;padding:2px 6px;font-size:13px}"
    ".neg-list{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}.neg-list span{font-size:12px;border:1px solid #e3c8c8;color:#8a3b3b;background:#fdf5f5;border-radius:999px;padding:3px 9px}"
    ".check-list{list-style:none;padding:0;margin:22px 0 0;max-width:900px}.check-list li{padding:14px 0 14px 34px;border-top:1px solid #d7e0e4;position:relative;color:#52616b;line-height:1.7}"
    ".check-list li:before{content:'✓';position:absolute;left:4px;top:13px;font-weight:700;color:#0b5cad}.check-list strong{color:#17212b}"
    ".near-links{display:flex;flex-wrap:wrap;gap:10px;margin-top:20px}.near-links a{border:1px solid #c9d8e0;border-radius:999px;padding:8px 14px;background:#fff;text-decoration:none;font-weight:600;font-size:14px}"
    ".city-final .city-btn.secondary{color:#17212b!important;border-color:#80909b}"
    ".season{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:15px;margin-top:22px}"
    "@media(max-width:760px){.season{grid-template-columns:1fr}.kw-table{font-size:13px;table-layout:fixed}.kw-table th,.kw-table td{padding:10px 8px;word-break:break-word}.kw-table th:nth-child(3),.kw-table td:nth-child(3){display:none}}"
)

YAKIN_SAYISI = 6

# ---------------------------------------------------------------- Türkçe ekler
SERT = set("fstkçşhp")
KALIN = set("aıouâ")
INCE = set("eiöüî")


def _son_unlu(s):
    for ch in reversed(s.lower()):
        if ch in KALIN:
            return "a"
        if ch in INCE:
            return "e"
    return "e"


def bulunma(ad):
    """Bartın -> Bartın'da, Kars -> Kars'ta"""
    u = _son_unlu(ad)
    son = ad[-1].lower()
    d = "t" if son in SERT else "d"
    return f"{ad}'{d}{u}"


def buyuk(s):
    return s.replace("i", "İ").replace("ı", "I").upper()


def e(s):
    return html.escape(s, quote=True)


# ---------------------------------------------------------------- mevcut sayfadan okuma
def mevcut_parcalar(yol):
    s = open(yol, encoding="utf-8").read()
    stil = re.search(r"<style>(\.city-page.*?)</style>", s, re.S).group(1).replace(EK_CSS, "")
    header = re.search(r'(<header class="site-header">.*?</header>)', s, re.S).group(1)
    footer = re.search(r'(<footer class="site-footer">.*?</footer>)', s, re.S).group(1)
    alan = re.search(r'class="city-area-list">(.*?)</ul>', s, re.S)
    ilceler = re.findall(r"<strong>(.*?)</strong>", alan.group(1)) if alan else []
    head_scripts = re.search(r"(<!-- Google tag \(gtag\.js\) -->.*?)</head>", s, re.S).group(1)
    return stil, header, footer, [html.unescape(i) for i in ilceler], head_scripts


# ---------------------------------------------------------------- içerik üretimi
def yer_adi(ilce, sehir):
    return sehir if ilce == "Merkez" else ilce


def kw(kalip, yer, urun):
    return kalip.replace("{yer}", yer).replace("{urun}", urun or yer).lower()


ILCE_NOTLARI = [
    "İl merkezi aramaları genelde en yüksek hacmi ve rekabeti taşır; teklif burada ayrı izlenmelidir.",
    "İlçe adıyla yapılan aramalar daha az hacimli ama niyeti daha nettir; ayrı reklam grubu açmak tıklama başı maliyeti düşürebilir.",
    "Hizmet verilmeyen mahallelerden gelen tıklamalar konum raporunda görülür; gerekirse yarıçap yerine ilçe seçilmelidir.",
    "Bu bölgede mobil aramalar ağırlıklı olabilir; çağrı öğesi ve WhatsApp butonu reklamla aynı ekranda görünmelidir.",
    "Arama terimleri raporunda ilçe adı geçen sorgular ayrı etiketlenirse hangi bölgenin telefon getirdiği netleşir.",
]


def sayfa_uret(slug, veri, parcalar, tum_sehirler):
    ad, bolge, sektor_keys, urun = veri
    stil, header, footer, ilceler, head_scripts = parcalar
    loc = bulunma(ad)
    url = f"{SITE}/{slug}-google-ads/"
    sektorler = [SEKTORLER[k] for k in sektor_keys]
    for k in sektor_keys:
        if k == "yoresel_urun" and not urun:
            raise ValueError(f"{slug}: yoresel_urun için ürün gerekli")
    sektor_adlari = [s["ad"].split(" (")[0].lower() for s in sektorler]
    sektor_metin = ", ".join(sektor_adlari[:-1]) + " ve " + sektor_adlari[-1]
    ilce_metin = ", ".join(ilceler[:4]) if ilceler else ad

    title = f"{ad} Google Reklam Ajansı | Google Ads Yönetimi {YIL} | Web Portal Faaliyetleri"
    desc = (f"{ad} Google reklam ajansı: {sektor_adlari[0]} ve {sektor_adlari[1]} odaklı Google Ads kurulumu, "
            f"{ilce_metin} için bölge hedefleme, telefon/WhatsApp dönüşüm takibi ve negatif kelime yönetimi.")
    if len(desc) > 165:
        desc = (f"{ad} Google reklam ajansı: {sektor_adlari[0]} odaklı Google Ads yönetimi, {ilce_metin} hedefleme "
                f"ve telefon dönüşüm takibi.")

    wa_text = f"Merhaba, {ad} için Google reklam ajansı hizmeti hakkında bilgi almak istiyorum."
    wa_link = f"https://wa.me/{WA}?text=" + re.sub(r"\s", "%20", wa_text)

    # --- sektör kartları + anahtar kelime tablosu
    ornek_yer = [yer_adi(i, ad) for i in ilceler] or [ad]
    sektor_kartlari = []
    tablo_satir = []
    for idx, (key, s) in enumerate(zip(sektor_keys, sektorler)):
        yer2 = ornek_yer[(idx + 1) % len(ornek_yer)]
        kws = [kw(s["kaliplar"][0], ad, urun), kw(s["kaliplar"][1], yer2, urun), kw(s["kaliplar"][2], ad, urun)]
        neg = "".join(f"<span>-{e(n)}</span>" for n in s["negatif"])
        ozel = ""
        if key == "yoresel_urun":
            ozel = f" {e(ad)} denince akla gelen {e(urun)} gibi ürünlerde satış çoğunlukla il dışına yapılır."
        sektor_kartlari.append(
            f'<article class="city-card"><span class="mini">{idx+1:02d} • SEKTÖR</span><h3>{e(s["ad"])}</h3>'
            f'<p>{e(s["not"])}{ozel}</p><div class="neg-list">{neg}</div></article>'
        )
        tablo_satir.append(
            f'<tr><td><strong>{e(s["ad"])}</strong></td><td>' + " ".join(f"<code>{e(k)}</code>" for k in kws) +
            f'</td><td>{e(s["sezon"])}</td></tr>'
        )

    # --- ilçe hedefleme
    ilce_li = []
    for i, ilce in enumerate(ilceler):
        s = sektorler[i % len(sektorler)]
        ornek = kw(s["kaliplar"][i % 3], yer_adi(ilce, ad), urun)
        notu = ILCE_NOTLARI[0] if ilce == "Merkez" or i == 0 else ILCE_NOTLARI[1 + (i + len(ad)) % 4]
        ilce_li.append(f'<li><strong>{e(ilce)}</strong><span>Örnek arama: “{e(ornek)}”. {e(notu)}</span></li>')
    ilce_bolumu = ""
    if ilce_li:
        ilce_bolumu = (
            f'<section class="city-section alt"><div class="city-wrap"><h2>{e(ad)} ilçelerinde Google reklam hedeflemesi</h2>'
            f'<p>Google reklamında bütçeyi koruyan ilk ayar, reklamın kime gösterileceğidir. {e(ad)} için konum seçeneğini '
            f'“Hedeflenen konumlarda bulunan veya düzenli olarak bulunan kişiler” olarak ayarlamak, ilgi alanına göre il dışından '
            f'gelen tıklamaları azaltır. Aşağıdaki ilçe ve arama örnekleri planlama içindir; nihai kapsam işletmenin fiilen hizmet '
            f'verdiği bölgeye göre belirlenir.</p><ul class="city-area-list">{"".join(ilce_li)}</ul></div></section>'
        )

    # --- yakın şehirler
    ayni = sorted([k for k, v in tum_sehirler.items() if v[1] == bolge and k != slug])
    if ayni:
        bas = sum(ord(c) for c in slug) % len(ayni)
        yakin = (ayni[bas:] + ayni[:bas])[:YAKIN_SAYISI]
    else:
        yakin = []
    yakin_link = "".join(
        f'<a href="/{k}-google-ads/">{e(tum_sehirler[k][0])} Google reklam ajansı</a>' for k in yakin
    )

    # --- SSS
    sss = [
        (f"{ad} Google reklam ajansı ile çalışırken ilk ne yapılır?",
         f"Önce hesabın ve sitenin dönüşüm takibi kontrol edilir. {ad} için telefon ve WhatsApp tıklamaları ölçülmeden "
         f"yapılan optimizasyon tahmine dayanır; ardından {sektor_adlari[0]} gibi işletmenin sektörüne uygun anahtar kelime grupları kurulur."),
        (f"{loc} reklama tıklama geliyor ama telefon gelmiyor, neden?",
         "En sık nedenler: dönüşüm takibinin kurulu olmaması, Görüntülü Reklam Ağı veya arama ağı iş ortaklarının açık kalması, "
         "geniş eşlemeli kelimelerin alakasız sorgular yakalaması, konumun ilgi alanına göre hedeflenmesi ve açılış sayfasında "
         "telefonun ilk ekranda görünmemesi. Arama terimleri raporu bunların hangisinin geçerli olduğunu gösterir."),
        (f"{ad} için hangi negatif anahtar kelimeler eklenmeli?",
         f"Sektöre göre değişir. {sektorler[0]['ad']} için " + ", ".join(sektorler[0]["negatif"][:3]) +
         f"; {sektorler[1]['ad'].lower()} için " + ", ".join(sektorler[1]["negatif"][:3]) +
         " gibi terimler sık görülen başlangıç örnekleridir. Liste her hafta arama terimleri raporuna göre güncellenir."),
        (f"Web Portal Faaliyetleri'nin {loc} ofisi var mı?",
         f"Hayır. Bu sayfa {ad} için Google reklam planlamasını anlatan bir rehberdir; çalışma çevrim içi yürütülür ve "
         f"{loc} fiziksel ofis bulunduğu iddiası taşımaz."),
        ("Google reklamları belirli sayıda müşteri garanti eder mi?",
         "Hayır. Performans arama talebi, rekabet, teklif, site deneyimi ve ölçüm kurulumuna bağlıdır. Hedef, sonuçları "
         "doğru ölçüp kampanyayı veriyle geliştirmektir."),
    ]
    sss_html = "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in sss)

    schema_service = {
        "@context": "https://schema.org", "@type": "Service",
        "name": f"{ad} Google Reklam Ajansı",
        "serviceType": "Google Ads reklam yönetimi",
        "provider": {"@type": "Organization", "name": "Web Portal Faaliyetleri", "url": SITE + "/", "telephone": TEL},
        "areaServed": {"@type": "AdministrativeArea", "name": ad},
        "url": url,
        "description": f"{ad} için uzaktan Google Ads kurulumu, {sektor_metin} odaklı kampanya yönetimi, ilçe hedefleme ve dönüşüm ölçümü.",
    }
    schema_faq = {
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in sss],
    }
    schema_bc = {
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Ana sayfa", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Google Reklam Ajansı", "item": SITE + "/google-ads/"},
            {"@type": "ListItem", "position": 3, "name": "Şehirler", "item": SITE + "/google-ads-sehirleri/"},
            {"@type": "ListItem", "position": 4, "name": ad, "item": url},
        ],
    }

    def ld(o):
        return '<script type="application/ld+json">' + json.dumps(o, ensure_ascii=False) + "</script>"

    sezon_kartlari = "".join(
        f'<article class="city-card"><span class="mini">{e(buyuk(s["ad"]))}</span><h3>Yoğun dönem</h3><p>{e(s["sezon"])}.</p></article>'
        for s in sektorler
    )

    return f"""<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#0b0f14"><title>{e(title)}</title><meta name="description" content="{e(desc)}"><meta name="robots" content="index,follow"><link rel="canonical" href="{url}"><meta property="og:type" content="website"><meta property="og:locale" content="tr_TR"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{url}"><link rel="stylesheet" href="/assets/css/style.css">{ld(schema_service)}{ld(schema_faq)}{ld(schema_bc)}
<style>{stil}{EK_CSS}</style>
{head_scripts}</head><body>
{header}
<main class="city-page"><div class="city-crumbs"><a href="/">Ana sayfa</a> / <a href="/google-ads/">Google Reklam Ajansı</a> / <a href="/google-ads-sehirleri/">Şehirler</a> / {e(ad)}</div>
<section class="city-hero"><div class="city-wrap"><div class="city-eyebrow">GOOGLE REKLAM AJANSI • {e(buyuk(ad))} • {buyuk(bolge)}</div><h1>{e(ad)} Google reklam ajansı: tıklamayı değil, telefonu ölçen Google Ads yönetimi</h1><p>{loc} {e(sektor_metin)} alanlarında Google'da arama yapan müşteriye ulaşmak isteyen işletmeler için kampanya kurulumu, {e(ilce_metin)} gibi bölgelerde konum hedeflemesi, negatif anahtar kelime yönetimi ve telefon/WhatsApp dönüşüm takibini tek planda yürütüyoruz.</p><div class="city-actions"><a class="city-btn" href="{e(wa_link)}" target="_blank" rel="noopener">WhatsApp ile ücretsiz hesap analizi</a><a class="city-btn secondary" href="tel:{TEL}">{TEL_GORUNEN}</a></div><div class="city-badges"><span>{e(bolge)} Bölgesi</span>{''.join(f'<span>{e(s["ad"])}</span>' for s in sektorler)}<span>Dönüşüm takibi</span></div></div></section>
<section class="city-section"><div class="city-wrap"><h2>{loc} Google reklamında öne çıkan sektörler</h2><p class="city-intro">{e(ad)} {e(bolge)} Bölgesi'nde yer alır ve yerel aramalarda {e(sektor_metin)} öne çıkan iş alanlarıdır. Her sektörün arama niyeti, boşa tıklama kaynağı ve sezonu farklıdır; bu yüzden aynı kampanya yapısı her işletmeye uygulanmaz.</p><div class="city-grid">{''.join(sektor_kartlari)}</div><p class="city-disclosure">Kırmızı etiketler, o sektörde sık görülen negatif anahtar kelime örnekleridir.</p></div></section>
<section class="city-section"><div class="city-wrap"><h2>{e(ad)} için örnek anahtar kelime planı</h2><p>Aşağıdaki aramalar kampanya kurgusu için başlangıç örnekleridir. Gerçek hacim ve tıklama maliyeti Anahtar Kelime Planlayıcı ile kontrol edilir; ifade eşlemeli kelimelerle başlayıp arama terimleri raporuna göre genişletmek bütçeyi korur.</p><table class="kw-table"><thead><tr><th>SEKTÖR</th><th>ÖRNEK ARAMALAR</th><th>YOĞUN DÖNEM</th></tr></thead><tbody>{''.join(tablo_satir)}</tbody></table></div></section>
{ilce_bolumu}
<section class="city-section"><div class="city-wrap"><h2>Tıklama geliyor ama telefon gelmiyor mu?</h2><p>{loc} Google reklamı veren işletmelerin en sık yaşadığı sorun budur. Bir Google reklam ajansı olarak hesabı devraldığımızda ilk kontrol ettiğimiz maddeler:</p><ul class="check-list"><li><strong>Dönüşüm takibi:</strong> Telefon ve WhatsApp tıklamaları Google Ads'e dönüşüm olarak gönderilmiyorsa sistem hangi tıklamanın müşteri getirdiğini bilemez ve “tıklamaları en üst düzeye çıkar” stratejisi en ucuz, en düşük kaliteli trafiği toplar.</li><li><strong>Ağ ayarları:</strong> Arama kampanyasında Görüntülü Reklam Ağı ve arama ağı iş ortakları açıksa uygulama ve oyun içi tıklamalar artar.</li><li><strong>Konum seçeneği:</strong> “İlgilenen kişiler” seçiliyse {e(ad)} dışından gelen tıklamalar bütçeyi tüketir.</li><li><strong>Arama terimleri:</strong> Geniş eşleme; iş ilanı, “nedir”, ücretsiz gibi satın alma niyeti taşımayan sorguları yakalar.</li><li><strong>Açılış sayfası:</strong> Telefon numarası ilk ekranda görünmüyorsa ve sayfa mobilde yavaşsa kullanıcı aramadan çıkar.</li><li><strong>Geçersiz tıklama:</strong> Aynı IP'den tekrarlanan tıklamalar raporlanır ve gerekirse IP hariç tutma uygulanır.</li></ul></div></section>
<section class="city-section alt"><div class="city-wrap"><h2>{e(ad)} sektörleri için reklam takvimi</h2><div class="season">{sezon_kartlari}</div></div></section>
<section class="city-section"><div class="city-wrap"><h2>{e(ad)} Google reklam ajansı hakkında sık sorulan sorular</h2><div class="city-faq">{sss_html}</div><div class="city-links"><a href="/google-ads/">Google reklam ajansı hizmetimizi inceleyin →</a><a href="/blog/google-ads-donusum-takibi-2026/">Dönüşüm takibi rehberi →</a><a href="/blog/google-ads-negatif-anahtar-kelimeler/">Negatif anahtar kelime rehberi →</a></div></div></section>
<section class="city-section alt"><div class="city-wrap"><h2>{e(bolge)} Bölgesi'ndeki diğer şehirler</h2><p>Aynı bölgedeki illerde arama alışkanlıkları ve sezonlar benzeşebilir. Diğer şehir rehberlerine göz atın veya <a href="/google-ads-sehirleri/">81 ilin tamamını</a> inceleyin.</p><div class="near-links">{yakin_link}</div></div></section>
<section class="city-final"><div class="city-wrap"><h2>{e(ad)} için Google Ads hesabınızı ücretsiz inceleyelim.</h2><p>Hesabınızdaki arama terimlerini, konum ayarlarını ve dönüşüm takibini kontrol edip tıklamaların neden telefona dönmediğini raporlayalım.</p><div class="city-actions"><a class="city-btn" href="{e(wa_link)}" target="_blank" rel="noopener">WhatsApp'tan yazın</a><a class="city-btn secondary" href="tel:{TEL}">Hemen arayın: {TEL_GORUNEN}</a></div><p class="city-disclosure">Bu içerik {e(ad)} için Google reklam planlamasını anlatır; ilde fiziksel ofis bulunduğu iddiası taşımaz. Çalışma çevrim içi yürütülür.</p></div></section></main>
{footer}</body></html>
"""


def main():
    uretilen = 0
    for slug, veri in SEHIRLER.items():
        yol = os.path.join(KOK, f"{slug}-google-ads", "index.html")
        if not os.path.exists(yol):
            print("ATLANDI (sayfa yok):", slug)
            continue
        parcalar = mevcut_parcalar(yol)
        open(yol, "w", encoding="utf-8").write(sayfa_uret(slug, veri, parcalar, SEHIRLER))
        uretilen += 1
    print(uretilen, "şehir sayfası üretildi")


if __name__ == "__main__":
    main()
