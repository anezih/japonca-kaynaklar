import json
import re
from datetime import datetime
from functools import cached_property
from itertools import takewhile
from pathlib import Path

import requests
from bs4 import BeautifulSoup, NavigableString, ResultSet, Tag
from ebooklib import epub

BETIK_DY = Path(__file__).resolve().parent
JISHO_URL = "https://jisho.org/search/{0}%20%23kanji"
NS = "DC"
ACIKLAMA = '''<span class="aciklamali">
<ruby>
{0}
<rp>(</rp>
<rt>{1}</rt>
<rp>)</rp>
</ruby></span>
'''

class Veri:
    def __init__(self) -> None:
        self.ana_url = "https://guidetojapanese.org/turkish/"

    @cached_property
    def icindekiler_url(self) -> str:
        return f"{self.ana_url}index.html"

    @cached_property
    def giris_sayfasi_metin(self) -> str:
        istenmeyen = ["head", "center", "div.toc"]
        resp = self.sayfa_indir(self.ana_url)
        soup = BeautifulSoup(resp, "html5lib")
        for i in istenmeyen:
            soup.select_one(i).extract()
        return str(soup.select_one("body"))

    @cached_property
    def css(self) -> str:
        _css = BETIK_DY / "res" / "style.css"
        if _css.exists():
            return _css.read_text(encoding="utf-8")
        else:
            print("[!] res/style.css bulunamadı. Klasörün betiğin yanında olduğundan emin olun.")
            return ""

    @cached_property
    def icerik(self) -> dict[str,dict[str,str]]:
        if (y:=(BETIK_DY / "tae_kim_turkce.json")).exists():
            return json.loads(y.read_text(encoding="utf-8"))
        else:
            r = requests.get(self.icindekiler_url)
            soup = BeautifulSoup(r.content, "html5lib")
            icindekiler = soup.select_one("div.toc.inlist > ol")
            seviye_1 = icindekiler.find_all("li", recursive=False)
            sonuc = self.icindekileri_ayikla(seviye_1)
            with open(BETIK_DY / "tae_kim_turkce.json", "w", encoding="utf-8") as c:
                json.dump(sonuc, c, ensure_ascii=False, indent=2)
            return sonuc

    def baslik_temizle(self, baslik: str) -> str:
        return re.sub(r"\s{2,}", " ", baslik.replace("\n",""))

    def sayfa_indir(self, url: str) -> str:
        resp = requests.get(url)
        resp.encoding = "utf-8"
        return resp.text

    def icindekileri_ayikla(self, sonuc_seti: ResultSet, onceki_idx: str = None) -> dict[str,dict[str,str]]:
        sonuc = {}
        for idx, li in enumerate(sonuc_seti, start=1):
            girdi: Tag = li.find("a")
            if not girdi:
                continue
            girdi_metin = self.baslik_temizle(girdi.text)
            girdi_baglanti = f"{self.ana_url}{girdi.get("href")}"
            girdi_html = self.sayfa_indir(girdi_baglanti)
            _idx = ""
            if onceki_idx:
                _idx = f"{onceki_idx}_{idx}"
            else:
                _idx = str(idx)
            sonuc[girdi_metin] = {"idx" : _idx, "baglanti" : girdi_baglanti, "icerik" : girdi_html}
            ul = li.find("ul", recursive=False)
            if ul:
                sonuc[girdi_metin]["alt_basliklar"] = self.icindekileri_ayikla(
                    ul.find_all("li", recursive=False), _idx
                )
        return sonuc

class EpubOlusturucu:
    def __init__(self) -> None:
        self.toc_temp = list()
        self.nav_temp = list()

    @cached_property
    def veri(self) -> Veri:
        return Veri()

    @cached_property
    def agac(self) -> dict[str,dict[str,str]]:
        return self.veri.icerik

    @cached_property
    def epub_nesnesi(self):
        _epub = epub.EpubBook()
        _epub.add_author(
            author="Tae Kim",
            role="aut"
        )
        _epub.add_author(
            author="github.com/anezih",
            role="cre"
        )
        _epub.add_metadata(
            namespace=NS,
            name="publisher",
            value="github.com/anezih"
        )
        _epub.set_title("Tae Kim'in Japonca Grameri")
        _epub.add_metadata(
            namespace=NS,
            name="date",
            value=datetime.today().strftime("%Y-%m-%d")
        )
        _epub.add_metadata(
            namespace=NS,
            name="description",
            value=self.veri.baslik_temizle(f"""
            https://guidetojapanese.org/turkish/index.html adresinde yer alan
             Japonca dil bilgisi rehberi Türkçe çevirisinin ePub versiyonu.
            """)
        )
        _epub.add_metadata(
            namespace=NS,
            name="subject",
            value="Dil bilgisi"
        )
        _epub.add_metadata(
            namespace=NS,
            name="subject",
            value="Yabancı Diller"
        )
        _epub.add_metadata(
            namespace=NS,
            name="subject",
            value="Japonca"
        )
        _epub.set_language("tr")
        _epub.set_language("ja")
        return _epub

    def html_isle(self, html: str, dosya_ismi: str = "") -> str:
        soup = BeautifulSoup(html, "html5lib")
        govde = soup.find("body")
        # berbat html'i düzeltmeye çalış. yine de hâlâ hatalar kalıyor.
        # _strings = [
        #     ele
        #     for ele in govde.contents
        #     if isinstance(ele, NavigableString) and str(ele).strip()
        # ]
        # for s in _strings:
        #     _metin_parcalari = [
        #         _m
        #         for _m in takewhile(
        #             lambda x: x.name not in {"h1", "h2", "h3", "div", "span", "center", "table"},
        #             s.next_siblings
        #         )
        #     ]
        #     paragraf = soup.new_tag("p")
        #     s.wrap(paragraf)
        #     for m in _metin_parcalari:
        #         paragraf.append(m)
        bos_href = govde.find_all(
            "a",
            attrs={"href" : "", "name" : False}
        )
        for b in bos_href:
            b["href"] = dosya_ismi
        # "[一-龯]" kanji karakterleriyle eşleşen regex aralığı
        kanji_baglantilari = govde.find_all(
            "a",
            href=re.compile("csse"),
            string=re.compile("[一-龯]")
        )
        pdf_baglantilari = govde.find_all(
            "a",
            href=re.compile(".pdf")
        )
        acilan_aciklama = govde.find_all(
            "span",
            class_="popup"
        )
        yanlis_baglantilar = govde.find_all(
            "a",
            href=re.compile(r"(.*?)(#.+).html")
        )
        yonlendirmeler = [govde.find(
            "table",
            {"align":"right", "cellpadding":"3"}
        ),
        govde.find(
            "div",
            class_="botmenu"
        )]
        noscript = govde.find("noscript")
        if noscript:
            noscript.decompose()
        for y in yonlendirmeler:
            if y:
                y.decompose()
        govde_str = str(govde)
        silinecekler = [
            """<img alt="Creative Commons License" border="0" src="http://creativecommons.org/images/public/somerights20.gif"/>""",
            """<span class="bottom"><img alt="e-posta adresi" src="contributor1.png"/></span>"""
        ]
        for yb in yanlis_baglantilar:
            href: str = yb["href"]
            dosya_ismi = href[:href.index("#")]
            alt_baslik = href[href.index("#"):href.index(".")]
            govde_str = govde_str.replace(
                href,
                f"{dosya_ismi}.html{alt_baslik}",
                1
            )
        for a in acilan_aciklama:
            govde_str = govde_str.replace(
                str(a),
                ACIKLAMA.format("".join(map(str,a.contents)), a["title"]),
                1
            )
        for k in kanji_baglantilari:
            govde_str = govde_str.replace(
                k["href"],
                JISHO_URL.format(k.string.strip())
            )
        for p in pdf_baglantilari:
            govde_str = govde_str.replace(
                p["href"],
                f"{self.veri.ana_url}{p["href"]}"
            )
        for s in silinecekler:
            govde_str = govde_str.replace(
                s,
                ""
            )
        govde_str = govde_str.replace("<center>", "<div>")
        govde_str = govde_str.replace("</center>", "</div>")
        govde_str = govde_str.replace("""<table cellpadding="0" cellspacing="0">""", '<table class="busayfa">')
        govde_str = re.sub(r"<table(?!\sclass)[^>]+>", '<table>', govde_str)
        govde_str = re.sub(r"<tr[^>]+>", "<tr>", govde_str)
        govde_str = govde_str.replace("<td/>", "<td></td>")
        govde_str = govde_str.replace(".html", ".xhtml")
        govde_str = govde_str.replace("negverb.", "negverbs.")
        govde_str = govde_str.replace("try.xhtml#part3", "try.xhtml")
        return BeautifulSoup(govde_str, "html5lib").prettify()

    def bolumleri_olustur(self, agac: dict):
        for baslik,deger in agac.items():
            _baslik = f"{deger['idx'].replace('_','.')} {baslik}"
            _file_name = deger["baglanti"].split("/")[-1]
            _file = f'{_file_name[:_file_name.index(".")]}.xhtml'
            bolum = epub.EpubHtml(
                title=_baslik,
                file_name=_file,
                lang="tr",
                media_type="application/xhtml+xml"
            )
            bolum.content = self.html_isle(deger["icerik"], _file)
            bolum.add_item(self.bicem)
            self.epub_nesnesi.add_item(bolum)
            # nav
            self.nav_temp.append(bolum)
            # toc
            if deger["idx"].count("_") == 0:
                self.toc_temp.append([
                    epub.Section(_baslik, _file),
                    []
                ])
            elif deger["idx"].count("_") == 1:
                i,j = (int(x)-1 for x in deger["idx"].split("_"))
                if agac[baslik].get("alt_basliklar"):
                    self.toc_temp[i][1].append([
                        epub.Section(_baslik, _file),
                        []
                    ])
                else:
                    self.toc_temp[i][1].append(bolum)
            elif deger["idx"].count("_") == 2:
                i,j,k = (int(x)-1 for x in deger["idx"].split("_"))
                self.toc_temp[i][1][-1][1].append(
                    epub.Link(_file, _baslik, f'idx_{deger["idx"]}')
                )
            if ab := deger.get("alt_basliklar"):
                self.bolumleri_olustur(ab)

    def giris_sayfasi(self):
        bolum = epub.EpubHtml(
                title="Giriş",
                file_name="giris.xhtml",
                lang="tr",
                media_type="application/xhtml+xml"
            )
        bolum.content = self.html_isle(self.veri.giris_sayfasi_metin)
        bolum.add_item(self.bicem)
        self.epub_nesnesi.add_item(bolum)
        self.nav_temp.insert(0,bolum)
        self.toc_temp.insert(0, bolum)

    def kapak_ekle(self):
        kapak = BETIK_DY / "res" / "cover.jpg"
        if not kapak.exists():
            print("[!] Kapak res/ klasöründe bulunamadı.")
            return
        kapak_resim = epub.EpubCover(
            uid="kapak",
            file_name=kapak.name,
        )
        kapak_resim.content=kapak.read_bytes()
        kapak_resim.media_type="image/jpeg"
        self.epub_nesnesi.add_item(kapak_resim)
        kapak_html = epub.EpubCoverHtml(
            image_name=kapak.name,
            title="Kapak"
        )
        kapak_html.media_type="application/xhtml+xml"
        kapak_html.is_linear = True
        self.epub_nesnesi.add_item(kapak_html)
        self.nav_temp.insert(0, kapak_html)
        self.toc_temp.insert(0, kapak_html)

    def resimleri_ekle(self):
        resimler = (BETIK_DY / "res").glob("*.gif")
        for idx, r in enumerate(resimler, start=1):
            resim = epub.EpubImage(
                uid=f"resim{idx}",
                file_name=r.name,
                media_type="image/gif",
                content=r.read_bytes()
            )
            self.epub_nesnesi.add_item(resim)

    @cached_property
    def bicem(self):
        _bicem = epub.EpubItem(
            uid="bicem",
            file_name="style/style.css",
            media_type="text/css",
            content=self.veri.css
        )
        self.epub_nesnesi.add_item(_bicem)
        return _bicem

    def kaydet(self):
        self.bolumleri_olustur(self.agac)
        self.giris_sayfasi()
        self.kapak_ekle()
        self.resimleri_ekle()
        self.epub_nesnesi.toc = self.toc_temp
        self.epub_nesnesi.spine = self.nav_temp
        self.epub_nesnesi.add_item(epub.EpubNcx())
        self.epub_nesnesi.add_item(epub.EpubNav())
        dosya_ismi = f"TaeKiminJaponcaGrameri_{datetime.today().strftime("%d_%m_%Y")}.epub"
        epub.write_epub(dosya_ismi, self.epub_nesnesi, {})

if __name__ == '__main__':
    epub_olusturucu = EpubOlusturucu()
    epub_olusturucu.kaydet()