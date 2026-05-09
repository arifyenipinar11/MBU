import json
import random

restoranlar = {
    "Kral Burger": {
        "kategori": "Fast Food",
        "menuler": [
            "Kral Burger", "Double Burger", "Cheeseburger", "Tavuk Burger",
            "Patates Kızartması", "Soğan Halkası", "Coca Cola", "Ayran",
            "Acılı Tavuk Menü", "Mega Et Menü"
        ]
    },
    "Dayı Döner": {
        "kategori": "Döner",
        "menuler": [
            "Et Döner Dürüm", "Tavuk Döner Dürüm", "Pilav Üstü Döner",
            "İskender", "Ayran", "Şalgam", "Lavaş", "Çoban Salata",
            "Bol Soslu Tavuk Döner", "Kaşarlı Et Döner"
        ]
    },
    "Usta Pizza": {
        "kategori": "Pizza",
        "menuler": [
            "Margarita Pizza", "Karışık Pizza", "Sucuklu Pizza", "Tavuklu Pizza",
            "Ton Balıklı Pizza", "Vegan Pizza", "Patates", "Kola",
            "Bol Peynirli Pizza", "Acılı Mexicano Pizza"
        ]
    },
    "Abi Kebap": {
        "kategori": "Kebap",
        "menuler": [
            "Adana Kebap", "Urfa Kebap", "Tavuk Şiş", "Ciğer Şiş",
            "Lahmacun", "Açık Ayran", "Ezme", "Künefe",
            "Beyti Kebap", "Karışık Izgara"
        ]
    },
    "Sahil Balık": {
        "kategori": "Deniz Ürünleri",
        "menuler": [
            "Levrek Izgara", "Çipura Izgara", "Kalamar", "Karides Güveç",
            "Balık Ekmek", "Roka Salatası", "Mevsim Salata", "Limonata",
            "Somon Izgara", "Midye Tava"
        ]
    }
}

isimler = [
    "Mehmet abi", "Ali usta", "Hasan dayı", "Yunus", "Emre", "Murat",
    "Ayşe abla", "Zeynep", "Fatma", "Kerem", "Burak", "Can", "Osman hoca",
    "Sefa", "Cem", "Eren", "Mustafa", "Ahmet", "İsmail", "Hakan"
]

adresler = [
    "İskenderun Sahil Mahallesi", "Primall AVM yanı", "KYK Muhiddin İbni Arabi Yurdu",
    "Çay Mahallesi", "Numune Mahallesi", "Meydan Mahallesi", "Pac Meydanı",
    "Hatay yolu üzeri", "Üniversite kampüsü yakını", "Sanayi sitesi girişi",
    "Fener Caddesi", "Atatürk Bulvarı", "Liman çevresi", "Dumlupınar Mahallesi"
]

notlar = [
    "Abi soğan olmasın.",
    "Usta acısı bol olsun.",
    "Dayı sıcak gelsin lütfen.",
    "İçecek soğuk olsun.",
    "Ketçap mayonez fazla koyun.",
    "Ekmek arası değil tabakta olsun.",
    "Adrese gelmeden arayın.",
    "Temassız teslimat olsun.",
    "Yanına ekstra peçete koyun.",
    "Soslar ayrı gelsin."
]

siparis_durumlari = ["hazırlanıyor", "yolda", "teslim edildi", "iptal edildi", "ürün eklendi"]

veriler = []

siparis_id = 1000

for restoran, bilgi in restoranlar.items():
    for i in range(500):
        secilen_urunler = random.sample(bilgi["menuler"], random.randint(2, 5))
        durum = random.choice(siparis_durumlari)
        fiyat = random.randint(180, 900)

        ekstra = ""
        if durum == "iptal edildi":
            ekstra = random.choice([
                "Müşteri yanlış adres girdiği için sipariş iptal edildi.",
                "Restoran yoğunluktan dolayı siparişi iptal etti.",
                "Ödeme alınamadığı için sipariş iptal edildi.",
                "Müşteri arayıp vazgeçtiği için iptal edildi."
            ])
        elif durum == "ürün eklendi":
            ek_urun = random.choice(bilgi["menuler"])
            ekstra = f"Müşteri sonradan {ek_urun} ekledi."

        metin = f"""
Sipariş No: {siparis_id}
Restoran: {restoran}
Kategori: {bilgi['kategori']}
Müşteri: {random.choice(isimler)}
Adres: {random.choice(adresler)}
Ürünler: {', '.join(secilen_urunler)}
Toplam Tutar: {fiyat} TL
Durum: {durum}
Not: {random.choice(notlar)}
Ek Bilgi: {ekstra}
"""

        veriler.append({
            "id": siparis_id,
            "restoran": restoran,
            "kategori": bilgi["kategori"],
            "metin": metin.strip()
        })

        siparis_id += 1

with open("dataset.json", "w", encoding="utf-8") as f:
    json.dump(veriler, f, ensure_ascii=False, indent=2)

print(f"{len(veriler)} adet veri oluşturuldu.")
veriler = []
siparis_id = 1000

for restoran, bilgi in restoranlar.items():
    for i in range(500):
        secilen_urunler = random.sample(bilgi["menuler"], random.randint(2, 4))

        veri = {
            "id": siparis_id,
            "restoran": restoran,
            "kategori": bilgi["kategori"],
            "urunler": secilen_urunler,
            "durum": random.choice(["hazırlanıyor", "yolda", "iptal edildi", "ürün eklendi"])
        }

        veriler.append(veri)
        siparis_id += 1

with open("dataset.json", "w", encoding="utf-8") as f:
    json.dump(veriler, f, ensure_ascii=False, indent=2)

print("Dataset oluşturuldu:", len(veriler))