import time
import feedparser
import random
import requests
import smtplib
import json

islenen_haberler = set()

BENIM_GMAILIM = "your_email@gmail.com"
BENIM_UYGULAMA_SIFREM = "your_app_password"

def mail_fırlat(konu,icerik):
   try:
        tam_mesaj = f"Subject: {konu}\nContent-Type: text/plain; charset=utf-8\n\n{icerik}"
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls() 
        server.login(BENIM_GMAILIM, BENIM_UYGULAMA_SIFREM)
        
        
        server.sendmail(BENIM_GMAILIM, BENIM_GMAILIM, tam_mesaj.encode('utf-8'))
        server.quit() 
        print("📧 Analiz raporu kendi mail kutuna başarıyla fırlatıldı!")
        
   except Exception as hata:
        print(f"❌ Mail  gönderilirken bir hata oluştu: {hata}")

def haber_çekme():
    rss_url = "https://www.coindesk.com/arc/outboundfeeds/rss/"

    try:
        print('haberler çekiliyor')
       
        kaynak=feedparser.parse(rss_url)

        haber=kaynak.get('entries',[])
        print(f'toplam {len(haber)} başarıyla çekildi')
        return haber
    except Exception as hata:
        print(f'bir hata meydana geldi: {hata}')
        return []
    
def haberleri_filtrele(ham_haberler):
    kritik_kelimeler=["fed", "bitcoin", "hack", "sec", "whale", "dump", "pump", "crash", "crypto"]
    temiz_haberler=[]
    print(f'{len(ham_haberler)} filtereye alınıyor')

    for haber in ham_haberler:
        başlık=haber.get('title','').lower()
        özet=haber.get('summary','').lower()
        
        kelime_bulundu_mu=False
        for kelime in kritik_kelimeler:
            if kelime in başlık or  kelime in özet:
                kelime_bulundu_mu=True
                break

        if kelime_bulundu_mu:
            temiz_veri={
                'başlık':haber.get('title'),
                'özet': haber.get('summary'),
                'link':haber.get('link')
            }    
            temiz_haberler.append(temiz_veri)
    print(f'ayrıştırma tamamnlandı {len(temiz_haberler)} bulundu')
    return temiz_haberler

def yapay_zeka_analiz(haber_başlık,haber_özet): 
    API_KEY = "your_groq_api_key_here"
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    sistem_talimati = (
        "You must respond only in JSON format. "
        "Sen deneyimli bir kripto ve makroekonomi analistisin. "
        "Sana verilen haberin piyasa algısını (Sentiment) analiz et. "
        "Cevabını tam olarak şu JSON formatında ver, başka hiçbir şey yazma:\n"
        '{"algi": "POZİTİF" veya "NEGATİF" veya "NÖTR", "risk_skoru": 1-10 arası sayı, "ozet_yorum": "1 cümlelik Türkçe analiz"}'
    )

    veri_paketi={
        "model": "llama3-70b-8192",
        'messages':[
            {'role':'system','content': sistem_talimati},
            {'role': 'user','content': f"Haber Başlığı: {haber_başlık}\nHaber Özeti: {haber_özet}"}
        ],
        "response_format": {"type": "json_object"} 
    
    }
    try:
        
        cevap=requests.post(url,headers=headers, json=veri_paketi,timeout=30)
        if cevap.status_code != 200:
            print(f"Groq API hatası verdi ({cevap.status_code}): {cevap.text}")
            return None
       
        cevap.raise_for_status()
        cevap_json = cevap.json()
        ai_mesaji = cevap_json.get("choices", [{}])[0].get("message", {}).get("content", "")
        print(" Yapay zeka haberi başarıyla analiz etti.")
        return ai_mesaji # Geriye JSON metni döner
    
    except Exception as hata:
        print(f'bir hata meydana geldi:{hata}')
        return None
    
def botu_başlat():
    print('bot aktif edildi')

    while True:
     ham_haberler=haber_çekme()
     if not ham_haberler:
        print('haber bulunamadı')
        time.sleep(300)
        continue
     
     kritik_haberler=haberleri_filtrele(ham_haberler)
     if kritik_haberler:
        print(f" Analiz edilecek {len(kritik_haberler)} adet kritik haber var!")

        for haber in kritik_haberler:
            başlık=haber.get('başlık')
            özet=haber.get('özet')
            link=haber.get('link')

            if link in islenen_haberler:
                 continue

            ai_raporu = yapay_zeka_analiz(başlık, özet)

            if ai_raporu:
                try:
                    # Gelen JSON metnini Python sözlüğüne çeviriyoruz
                    ai_data = json.loads(ai_raporu)

                    algı = ai_data.get("algi", "NÖTR")
                    risk = ai_data.get("risk_skoru", "-")
                    yorum = ai_data.get("ozet_yorum", "Yorum yapılamadı.")
                    özet = haber.get("özet", "Özet yok")
                    link = haber.get("link", "Link yok")

                    
                    mail_konu = f"Kripto Analiz [{algı}]: {başlık[:40]}..."#başlığın ilk 40 cümlesini alır

                    mail_icerik = (
                        f"📰 HABER: {başlık}\n\n"
                        f"📊 PİYASA ALGISI: {algı}\n"
                        f"⚠️ RİSK SKORU: {risk}/10\n\n"
                        f"🧠 YAPAY ZEKA YORUMU:\n{yorum}\n\n"
                        f"🔗 Haber Linki: {link}\n\n"
                        f"📝 HABERİN ÖZETİ:\n{özet}\n\n"
                    )

                    try:
                            risk_puanı = int(risk)
                    except:
                            risk_puanı = 0

                    if int(risk) > 6:
                     mail_fırlat(mail_konu, mail_icerik)
                     islenen_haberler.add(link)

                    else:
                        print('haber puanı 6 dan düşük')
                        islenen_haberler.add(link)

                except json.JSONDecodeError:
                    print(" AI geçersiz JSON döndürdü")
                    continue

                except Exception as hata:
                    print(f" Bir hata meydana geldi: {hata}")


            print(f"📧 '{başlık}' konulu haber analizi mail listesine eklendi.")

         
     bekleme_süresi=random.randint(100,500)
     print(f'işlem tamamlandı bekleme moduna geçiliyor')
     time.sleep(bekleme_süresi)

def ana_menu():

 while True:
   print("1 - Botu Başlat (Canlı Tarama)")
   print("2 - Sistem Ayarlarını Kontrol Et")
   print("3 - Çıkış Yap")
   seçim=input('seçim yapınız(1-3):')
    
   if seçim=='1':
      botu_başlat()
    
   elif seçim == "2":
            print("\n Durum: Sistem Ayarları Stabil.")
            print("Hedef RSS: CoinDesk")
            print(" AI Model: Llama3-8b-8192")
            print("Çıktı Kanalı: E-Posta (Yatırımcı Bülteni)")

   elif seçim=='3':
      print('sistem kapanıyor')
      break
   
   else:
      print('geçersiz seçim yaptınız')

if __name__ == "__main__":
 ana_menu()