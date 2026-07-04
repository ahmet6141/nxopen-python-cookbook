> 🌐 [English](../04-boolean-and-geometry-rules.md) · **Türkçe**

# 04 · Prosedürel Modelleme için Boolean & Geometri Kuralları

Kod üzerinden katı model ürettiğinizde, modellerin sessizce bozulduğu yer boolean işlemleridir. NX bir unite/subtract işlemini *başarılı* olarak raporlar ve yine de size birbirinden kopuk gövdeler bırakabilir. Bu kurallar, headless olarak büyük çok-gövdeli montajlar inşa edilirken zor yoldan öğrenildi; bunlar API tuhaflıkları değil, geometri gerçekleridir.

## Gerçekte neyin kaynaştığı

- **Unite (birleştirme) yapılan parçalar hedefle gerçek hacim paylaşmalıdır.** Bir parçanın güvenilir şekilde birleşmesi için hedef katıya **≥ 15 mm gömülmesi** gerekir (somun/burç gibi küçük donanımlar için ≥ ~6 mm yeterlidir, yapısal elemanlar için ≥ ~14 mm gerekir).
- **Nokta teması ve çizgi teması KAYNAŞMAZ.** Köşe köşeye (nokta) ve kenar kenara (çizgi) temas, "birbirine değiyor" olsalar dahi iki ayrı gövde bırakır. **Sıfır çakışmalı yüzey teması da unite (birleştirme) yapmaz** — hacimsel iç içe geçme gereklidir.
- **Hedefin tamamen dışında kalan bir tool, sonraki bir subtract'ta başarısız olur.** Hedefin tamamen dışına ofsetlenmiş bir parça hedefe yalnızca bir köşeden değiyorsa, ayrı bir gövde olarak kalır — ve "birleşmiş" bölgeyi hedefleyen sonraki bir subtract işlemi *"Tool body completely outside target body."* hatasını verir.

## Unite sırası önemlidir

Boolean işlemleri sırayla uygulanır, bu yüzden **temas, unite işleminin yapıldığı anda mevcut olmalıdır.** Plaka → pim → plaka istifi için, her yeni parça eklendiğinde gerçekten katı malzemeye değecek şekilde bu sırayla unite yapın. Sırayı yanlış yaparsanız, ara bir unite henüz orada olmayan bir geometriye iner.

## Hangi builder'lar boolean'ı güvenilir şekilde uygular

- Boolean işlemleri **prism / cylinder / tube / hole / extrude / revolve** üzerinde güvenilir şekilde uygulanır (extrude/revolve `BooleanOperation.SetTargetBodies` yolu üzerinden).
- **`loft`, bazı builder yollarında** boolean amacıyla **yalnızca create (oluşturma)** işlevi görür — satır içi unite/subtract işlemi uygulanmayabilir, bu da loft ile oluşturulan gövdeyi bağımsız bırakır. **Desen:** bir gövdeyi **tek bir loft (create)** olarak inşa edin, ardından geri kalan her şeyi prism/cylinder olarak onun üzerine unite edin. Bir loft'un boolean'ına asla güvenmeyin.
- **Tube boolean'ları özen ister:** dış halka işlemi hedefe karşı uygular *ve* bore hedefi keser. Bu yüzden bore yarıçapını, içinden geçen herhangi bir parçanın yarıçapından **daha küçük** tutun, aksi halde bore'un subtract işlemi o parçayı iki gövdeye böler.

## Tek temiz bir profil modellemek, cylinder yığınından daha iyidir

Herhangi bir dönel gövde veya taranmış çubuk için, kesişen bir cylinder yığınını birleştirmek yerine bunu **tek bir kapalı profil** (revolve) veya **tek bir taranmış yol** (bir polyline boyunca tube) olarak modelleyin. Cylinder kolajı kırılgandır — kesişimler hayalet kenarlar yaratır ve eksenlere hizalı bounding box'ı (sınırlayıcı kutu), *gerçek* geometrinin temiz geçtiği komşularla çakışır. Tek bir dış hat = tek, temiz, profesyonel bir katı.

- Bükülmüş çubuklar (anti-roll bar'lar, fren/yakıt hatları): kesişen cylinder'lar yerine, teğet köşe-fillet yayları ile **3D bir polyline boyunca tek bir tube** taraması yapın.
- Kulaklı/gözlü plakalar: kesişen göz-cylinder'ları yerine, lobları bore'ları doğrudan taşıyan **tek bir siluet** çizin.

> **Bunun yarattığı denetim (audit) uyarısı:** tek dış hatlı plakalar, gerçek 3D geometri temiz geçse bile *prism bounding box'ının* (sınırlayıcı kutusunun) köşelerinin yakındaki revolve'lara çarpıyormuş gibi görünmesine neden olur. Bounding box'lar üzerinde otomatik bir clearance (açıklık) denetimi çalıştırırsanız, burada yanlış pozitifler bekleyin — gerçek açıklığı elle doğrulayın, ardından bilinen-iyi çifti beyaz listeye ekleyin.

## Subtract'lar gerçekten kesişmelidir

- Bir **prism-subtract yuvası**, hedefi gerçekten kesip geçmelidir — yüzeyin hemen dışında havada duran bir yuva hiçbir şey çıkarmaz.
- **Bir yüzeye teğet bir bore** başarısız olur. Bir delik ile yakınından geçtiği herhangi bir yüzey arasında **≥ 2 mm** duvar bırakın.
- **`hole` primitive'i konumunu kendi `cx / cy / z0` alanlarından okur**, paylaşılan herhangi bir `origin` alanından değil. Yanlış alan kullanılarak yerleştirilen bir delik hedefin dışına iner ve hata verir.

## Sessiz öksüz gövdeleri tespit etme

Tehlikeli hatalar **hiçbir hata üretmez** — bir unite kaldırılmış/boş bir geometriye iner (örn. bir kesim tünelini kat eden bir eleman) ve NX yalnızca *ayrı* bir gövde oluşturur. Bunları sayısal olarak yakalayın:

1. **Gövdeleri iki şekilde sayın.** Build sonrasında, `built N solid bodies` ile `named N bodies` değerlerini karşılaştırın. Bir uyumsuzluk, bir unite işleminin isimsiz bir öksüz gövde oluşturduğu anlamına gelir.
2. **Tutmayı amaçladığınız her gövdeyi isimlendirin**, böylece sonda isimsiz kalan her şey tanım gereği bir öksüzdür.
3. **Build günlüğünü** `FAIL` için grep'leyin ve son `=== done (0 errors)` satırını doğrulayın — ama yalnızca buna güvenmeyin, çünkü sessiz öksüzler günlüğe düşmez.

## NX olmadan yapılan doğrulamanın yakalayabildiği ve yakalayamadığı şeyler

NX'e dokunmadan *önce* düz bir Python venv içinde çok şeyi doğrulayabilirsiniz — bounding box'lar, clearance'lar (açıklıklar), kütle tahminleri, mate (eşleşme) mesafeleri. Ama sınırlar konusunda dürüst olun:

- **Yakalayabilir:** kaba clash'ler (çakışmalar), havada kalan (floating) parçalar, eksik mate'ler (eşleşmeler), açıkça yanlış boyutlar — ucuzdur, hızlıdır, bunları unit testlerde çalıştırın.
- **Yakalayamaz:** tool-hedefin-dışında ve nokta-temas-unite hataları. Bunlar kernel'in gerçek boolean değerlendirmesine bağlıdır ve **yalnızca gerçek bir `run_journal.exe` build'inde ortaya çıkar.** Tamamlanmış bir montajı her zaman gerçek bir NX çalıştırması ile doğrulayın.

## NX'te bounding box hesaplama

Bu API'de `uf.Modl.AskBoundingBox` **yoktur**. Eksenlere hizalı bir bbox'ı köşe noktalarından kendiniz hesaplayın:

```python
# iterate body.GetEdges() → edge.GetVertices() and min/max the coordinates
```

## Otomatik bir montaj denetimi (audit) için önerilen kusur sınıfları

Üretilen geometriniz üzerinde sayısal bir DMU kapısı inşa ederseniz, şu dört sınıf prosedürel-modelleme kusurlarının çoğunu yakalar:

| Sınıf | Tanım |
|-------|------------|
| **CLASH** | Eşleşmesi beklenmeyen iki parçanın, küçük bir toleransın (örn. > 3 mm) ötesinde birbirine girmesi. |
| **FLOATER** | Hiçbir şeye değmeyen bir gövde — bir öksüz veya yanlış konuma yerleştirilmiş bir parça. |
| **MISSING MATE** | Değmesi gerektiğini belirttiğiniz bir bağlantının aslında temas halinde olmaması. |
| **INTERFERENCE with moving parts** | Statik bir gövdenin, dönen/öteleyen bir parçanın taranmış zarfının içinde durması. |

Revolve'ları, dişli/delikli parçaların katı cylinder olarak değil gerçeğe uygun temsil edilmesi için binlenmiş radyal-profil haritaları olarak, düz uçlu cylinder'ları kapaklı olarak ve prism'leri AABB olarak modelleyin — ardından çift başına mesafeleri ölçün. Gerçek mate'leri (eşleşmeleri) ve yukarıda belirtilen tek-dış-hatlı yanlış pozitifleri beyaz listeye ekleyin.
