> 🌐 [English](../06-resources.md) · **Türkçe**

# 06 · Kaynaklar

Sıkıştığınızda yer imlerine eklemeye değer yerler. **En güvenilir tek referans kendi yerel stub'larınızdır** — bunlar, çevrimiçi hiçbir kaynağın aksine, tam NX sürümünüzle eşleşir.

## Yerel kurulumunuz (önce burayı kontrol edin)

- **`<install>/UGOPEN/pythonStubs/NXOpen/`** — tam NX sürümünüz için `.pyi` tip stub'ları. Çevrimiçi bir örnek gerçekle çelişiyorsa, doğru olan stub'dır. Otomatik tamamlama için IDE'nizi buraya yönlendirin ve bir imzanın (signature) gerçek parametre türlerini öğrenmek için stub'ı doğrudan okuyun.
- **`<install>/UGOPEN/`** — örnek journal'lar ve UF (User Function) başlık dosyaları.

## Resmi Siemens

- **NXOpen Python API Reference** — [docs.sw.siemens.com](https://docs.sw.siemens.com) ("NXOpen Python" araması yapın). Sınıf/metot listesinin yetkili kaynağı olsa da örnekler GUI'ye ağırlık verir.
- **Siemens Community — NX forumları** — [community.sw.siemens.com](https://community.sw.siemens.com) — Siemens mühendisleri ve ileri düzey kullanıcılarla soru-cevap.

## Topluluk

- **nxjournaling.com** — uzun soluklu NX journaling topluluğu: eğitimler, örnek journal'lar ve gerçek problemlerin aranabilir arşivi. Çoğunlukla VB olsa da API kavramları doğrudan Python'a aktarılabilir.
- **eng-tips.com** (Siemens NX forumu) — pratik, yüksek isabetli sorun giderme konuları.

## GitHub'da açık kaynak

- **[cfs-energy/nxlib](https://github.com/cfs-energy/nxlib)** — NXOpen etrafında profesyonel bir Python sarmalayıcı (wrapper); daha büyük otomasyonları yapılandırmak için iyi desenler.
- **NXOpen Python type-stub projeleri** (GitHub'da `nxopen pyi` / `nx nxopen stubs` araması yapın) — topluluk tarafından bakımı yapılan stub'lar; kurulumunuzdaki stub'ları IDE'nize dahil edemiyorsanız faydalıdır.

## Bu cookbook nasıl oluşturuldu

Buradaki her reçete aynı döngüden geldi ve bu döngüyü kopyalamak iyi bir fikirdir:

1. Gerçek imzalar (signature) için **stub'ları kazın** (düz metin dokümanlara güvenmeyin).
2. Tek bir özelliği çalıştıran **minimal bir headless journal yazın**.
3. **`run_journal.exe` ile çalıştırın** ve ortaya çıkan `.prt` dosyasını inceleyin — yüzey sayıları, hacim, kütle, gövde sayısı.
4. Başarısızlık durumunda **tam hata metnini kaydedin**; bu metinler çözüme giden en hızlı yol olup issue'ları aranabilir kılar.

Buradaki bir reçetenin kendi NX sürümünüzde farklı davrandığını görürseniz, bu döngü artı sürümünüz + hata metniyle açılacak bir issue, geri katkı sağlamanın ideal yoludur.
