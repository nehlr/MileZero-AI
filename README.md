# Local RAG AI Assistant 🤖

Bu proje, Microsoft Foundry Local kullanılarak geliştirilmiş tamamen çevrimdışı (offline) çalışan bir RAG (Retrieval-Augmented Generation) Soru-Cevap asistanıdır. 

Yaz Okulu Planı'nda (Summer School Foundry Local Plan) belirtilen gereksinimler doğrultusunda inşa edilmiştir. Öğrencilerin veya araştırmacıların uzun belgeler (makaleler, notlar vb.) içerisinde kaybolmadan aradıkları bilgilere anında ulaşabilmelerini hedefler.

## 🌟 Özellikler
- **Tamamen Yerel Çalışma:** Hiçbir veri internete veya buluta gönderilmez. Tüm veritabanı, arama ve yapay zeka işlemleri kullanıcının kendi donanımında gerçekleşir.
- **Foundry Local Entegrasyonu:** Hem metinleri vektörleştirmek (Embedding) hem de cevap üretmek (Chat) için Microsoft'un hafif ve hızlı yapay zeka çalışma zamanı aracı olan Foundry Local kullanılır.
- **RAG Mimarisi:** Model ezberden konuşmaz. Soru sorulduğunda önce SQLite veritabanındaki belgeler taranır ve en alakalı kısımlar modele bağlam (context) olarak verilerek halüsinasyon yapması engellenir.
- **Modern Web Arayüzü:** Flask ve Vanilla HTML/CSS/JS kullanılarak tasarlanmış, karanlık temalı (dark mode) ve duyarlı (responsive) şık bir kullanıcı arayüzü sunar.

## 🏗️ Proje Mimarisi
- `app.py`: Web arayüzünü (Frontend) sunan ve API isteklerini karşılayan Flask sunucusu.
- `ingestion.py`: `data/` klasöründeki metin belgelerini parçalara ayıran (chunking), Foundry Local kullanarak vektörleştiren (embedding) ve `database.db` SQLite dosyasına kaydeden veri işleme boru hattı.
- `retrieval.py`: Kullanıcının sorusunu vektörleştiren ve veritabanındaki metinlerle arasındaki Kosinüs Benzerliğini (Cosine Similarity) hesaplayarak en alakalı metin parçalarını çıkaran (retrieval) arama motoru.
- `main.py`: Bulunan belgeleri bağlam olarak alıp Foundry Local'da çalışan ana LLM'e ileten ve akılcı bir yanıt üreten orkestratör script.

## 🚀 Kurulum & Çalıştırma

### Önkoşullar
- Python 3.9+
- Microsoft Foundry Local (M1/M2 Mac veya Windows için yüklü)
- `foundry-local-sdk` Python kütüphanesi

### 1. Foundry Local SDK & Modelleri Hazırlayın
Gerekli Python paketlerini ve `foundry-local-sdk`yı yükleyin:
```bash
pip install -r requirements.txt
```

Foundry Local CLI kullanarak küçük ve hızlı modelleri indirip arka plan sunucusunu başlatabilirsiniz:
```bash
# Vektörleştirme (Embedding) modelini indir ve yükle
foundry model download qwen3-embedding-0.6b
foundry model load qwen3-embedding-0.6b

# Cevap üretme (Chat) modelini indir ve sunucuyu başlat
foundry model download qwen2.5-1.5b
foundry server start -p 1234
```
*Not: Proje hem doğrudan Python içi `foundry-local-sdk` (`EmbeddingClient`, `ChatClient`) üzerinden hem de Foundry Local OpenAI-uyumlu sunucu arabirimi üzerinden sorunsuz çalışacak hibrit mimariye sahiptir.*

### 3. Belgeleri Veritabanına Aktarın (Ingestion)
Eğer `data/` klasörüne yeni `.txt` dosyaları eklerseniz, bu komutu çalıştırarak belgeleri vektörleştirin ve SQLite veritabanına kaydedin:
```bash
python ingestion.py
```

### 4. Web Arayüzünü Başlatın
Uygulamayı başlatın:
```bash
python app.py
```
Tarayıcınızda `http://127.0.0.1:8080` adresine giderek asistanınızı kullanmaya başlayabilirsiniz!

## 🎓 Öğrenilen Dersler (Lessons Learned)
Bu projenin geliştirilme sürecinde karşılaşılan en büyük zorluk ve kazanılan içgörüler şunlardır:
1. **Chunking (Parçalama) Stratejisi:** Belgeleri veritabanına kaydederken çok büyük parçalara bölmek modelin kafasını karıştırıp bağlam penceresini taşırıyordu. Çok küçük parçalar ise anlam bütünlüğünü bozuyordu. 500 karakterlik parçalar halinde (overlapping olmadan) bölmenin en stabil sonucu verdiği görüldü.
2. **Güvenlik (Responsible AI):** LLM'lerin uydurma eğilimi (hallucination) yüksektir. Sistem isteminde (System Prompt) modele *"Eğer bağlamda bilgi yoksa, bilmiyorum de"* komutunun ne kadar kritik olduğu, konu dışı bir soru sorulduğunda asistanın sınırı bilmesiyle kanıtlandı.
