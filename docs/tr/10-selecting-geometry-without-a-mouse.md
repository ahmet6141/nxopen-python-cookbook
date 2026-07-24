> 🌐 [English](../10-selecting-geometry-without-a-mouse.md) · **Türkçe**

# 10 · Fare Olmadan Geometri Seçmek

[02](02-verified-recipes.md)'deki her doğrulanmış reçete girdi olarak `edges`, `faces` ya da bir `body` alır — GUI'de bunlara tıklardın. Headless'ta **programatik seçim, geri kalan her şeyi kullanılabilir kılan beceridir**: topolojiyi gez, bulduğunu sınıflandır ve geometriye göre seç. Bu sayfa o kalıpları toplar.

> ⚠️ **Doğrulama durumu:** 01–07 dokümanlarının aksine, bu sayfadaki reçeteler **henüz NX 2506'da canlı doğrulanmadı**. Gezinme çağrıları (10.1–10.2) şimdiye dek kaydedilmiş her journal'ın kullandığı temel API'dir; UF çağrıları ve ölçüm imzaları ise stub'larına karşı iki kez kontrol edilmesi gerekenlerdir. Doğrula ve [CONTRIBUTING](../../CONTRIBUTING.md) uyarınca bildir.

Tüm parçacıklar [01-core-api.md](01-core-api.md) boilerplate'ini varsayar, artı aşağıda kullanılan UF oturumu:

```python
import NXOpen, NXOpen.UF
session = NXOpen.Session.GetSession()
uf = NXOpen.UF.UFSession.GetUFSession()
```

---

## 10.1 Topoloji gezintisi

Her şey gövdeden sarkar:

```python
for body in part.Bodies:                 # parçadaki tüm katı & sheet gövdeler
    faces = body.GetFaces()              # list[Face]
    edges = body.GetEdges()              # list[Edge]

for face in faces:
    face_edges = face.GetEdges()         # bu yüzeyi sınırlayan kenarlar
    owning_body = face.GetBody()

for edge in edges:
    verts = edge.GetVertices()           # list[Point3d] — kapalı kenarlarda (daireler) BOŞ!
    length = edge.GetLength()
```

> **Boş-vertex durumu** klasik çökmedir: tam bir dairenin vertex'i yoktur, dolayısıyla `GetVertices()[0]` varsayan her kod ilk yuvarlak delikte ölür. Her vertex erişimini uzunluk kontrolüyle koru.

`feat.GetBodies()`, `feat.GetFaces()`, `feat.GetEdges()` aynı gezintiyi **tek bir feature'ın** oluşturduklarına daraltır — "az önce boss'un yaptığı kenarları" parçanın geri kalanına dokunmadan blend'lemenin genelde en temiz yolu budur.

## 10.2 Yüzey ve kenarları türe göre sınıflandırmak

`Face.SolidFaceType` / `Edge.SolidEdgeType` enum döndürür — fareyi ikame eden kaba filtre:

```python
planar   = [f for f in body.GetFaces() if f.SolidFaceType == NXOpen.Face.FaceType.Planar]
round_fs = [f for f in body.GetFaces() if f.SolidFaceType == NXOpen.Face.FaceType.Cylindrical]
lines    = [e for e in body.GetEdges() if e.SolidEdgeType == NXOpen.Edge.EdgeType.Linear]
circles  = [e for e in body.GetEdges() if e.SolidEdgeType == NXOpen.Edge.EdgeType.Circular]
```

Bir yüzeyin *nerede* olduğu ve *hangi yöne* baktığı içinse UF katmanına in — `AskFaceData` bir yüzeyin analitik verisini tek çağrıda döndürür:

```python
def face_data(face):
    # döndürür: (type_code, point[3], dir[3], box[6], radius, rad_data, norm_dir)
    # tür kodları: 22 düzlemsel, 16 silindirik, 17 konik, 18 küresel…  — stub'larını kontrol et
    return uf.Modl.AskFaceData(face.Tag)
```

`point` yüzey üzerinde temsilî bir nokta, `dir` normali (düzlemsel) ya da ekseni (silindirik), `radius` silindir/küre/koni yarıçapıdır. Aşağıdaki her "bana şunu bul" yardımcısını bu tek çağrı besler.

## 10.3 "Bana şunu bul" yardımcıları

```python
def top_planar_face(body, tol=1e-6):
    """Normali yukarı bakan, en yüksek Z'deki düzlemsel yüzey."""
    best, best_z = None, float("-inf")
    for f in body.GetFaces():
        if f.SolidFaceType != NXOpen.Face.FaceType.Planar:
            continue
        t, pt, dr, box, radius, rad_data, norm_dir = uf.Modl.AskFaceData(f.Tag)
        if abs(dr[2] - 1.0) < tol and pt[2] > best_z:
            best, best_z = f, pt[2]
    return best

def cylindrical_faces_of_diameter(body, diameter, tol=1e-3):
    """Bir çapla eşleşen her silindirik yüzey — delikler, boss'lar, pimler."""
    out = []
    for f in body.GetFaces():
        if f.SolidFaceType == NXOpen.Face.FaceType.Cylindrical:
            t, pt, dr, box, radius, rad_data, norm_dir = uf.Modl.AskFaceData(f.Tag)
            if abs(2.0 * radius - diameter) < tol:
                out.append(f)
    return out

def vertical_edges(body, tol=1e-6):
    """Z'ye paralel doğrusal kenarlar — klasik chamfer/blend adayları."""
    out = []
    for e in body.GetEdges():
        vs = e.GetVertices()
        if len(vs) != 2:
            continue                                   # kapalı kenarların vertex'i yoktur (10.1)
        dx, dy, dz = vs[1].X - vs[0].X, vs[1].Y - vs[0].Y, vs[1].Z - vs[0].Z
        length = (dx * dx + dy * dy + dz * dz) ** 0.5
        if length > 0 and abs(abs(dz) / length - 1.0) < tol:
            out.append(e)
    return out
```

Bunlardan birleştirilebilir tek-satırlıklar türer — örn. "üst ağzı blend'le" demek, `top_planar_face(body).GetEdges()`'i doğrudan doğrulanmış EdgeBlend reçetesine (2.1) beslemektir. Thread reçetesinin *"aday başlangıç yüzeylerini sırayla dene"* tavsiyesi (2.4) de böyle uygulanır: silindirik yüzeye komşu düzlemsel yüzeyleri sırala ve biri commit olana kadar döngüye sok.

## 10.4 Vertex'lerden bounding box — tam yardımcı

[04](04-boolean-and-geometry-rules.md), bu wrapper'da `AskBoundingBox` olmadığını söyler ve yaklaşımı taslak halinde verir; işte fonksiyonun tamamı:

```python
def body_aabb(body):
    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    for edge in body.GetEdges():
        for v in edge.GetVertices():
            for i, c in enumerate((v.X, v.Y, v.Z)):
                lo[i] = min(lo[i], c)
                hi[i] = max(hi[i], c)
    return tuple(lo), tuple(hi)
```

İki dürüst uyarı: yalnızca **vertex'leri** görür, dolayısıyla uç noktası kenar ortasında olan bir gövde (küre, fıçı yüzeyi) biraz küçük bir kutu raporlar; ve *yalnızca* kapalı kenarlı bir gövde (yine küre) hiç vertex vermez. Eğri gövdelerde denetim-kalitesinde kutu için kenar orta-noktalarını da örnekle, ya da vertex kutusunu alt sınır olarak kabul et.

## 10.5 İsimler, nitelikler, katmanlar — parçayı gezilebilir kılmak

Seçimin öteki yarısı: nesneleri **oluştururken** işaretle ki sonraki kod (ve 7.6'daki temizlik filtresi) onları geometri yerine isimle bulabilsin.

```python
body.SetName("HULL")
feat.SetName("MYPROJ_WING")                            # 7.6 kuralı
hull = next(b for b in part.Bodies if b.Name == "HULL")

# nitelikler — isimlerden zengin, STEP/JT'ye aktarılabilir (SetUserAttribute için 05'e bak)
pn = body.GetStringUserAttribute("PART_NO", -1)        # tam getter için stub'larını kontrol et

# katmanlar — export'lara da taşınan kaba göster/gizle mekanizması
body.Layer = 20                                        # nesneyi katman 20'ye taşı
part.Layers.WorkLayer = 20                             # bundan sonra yeni nesneler buraya düşer
```

Üretilmiş parçalar için pratik bir katman şeması: katılar 1'de, yardımcı eğri/noktalar 41'de, datum'lar 61'de — böylece GUI kullanıcısı tek katman-durumu değişikliğiyle tüm iskeleyi gizler, exporter'ın da "yalnız katman 1 katıları"nı seçer; bu aynı zamanda Parasolid-zehirlenmesi tuzağını (tuzak #22) da dolanır.

## 10.6 Ölçüm — mesafe ve açı

Hacim/kütle için doğrulanmış yol `NewMassProperties`'tir (2.9). Nesneler arası mesafeler için:

```python
unit = part.UnitCollection.FindObject("MilliMeter")
m = part.MeasureManager.NewDistance(unit, obj_a, obj_b)   # minimum mesafe
print(m.Value)
# yeni sürümler MeasureType enum'u alan overload'lar ekler — stub'larını kontrol et
# (buradaki imzalar sürümler arasında API'nin çoğundan daha fazla oynar)
```

`MeasureManager` ayrıca `NewAngle` sunar. Ama *geçti/kaldı* geometri kontrolleri için [7.8](07-freeform-lofting.md)'deki boolean-intersect sondası çoğu zaman daha güvenilir araçtır: hiçbir mesafe ölçümünün veremeyeceği "gerçekte ne kadar malzeme çakışıyor" sorusunu yanıtlar.

## 10.7 Neden `FindObject` değil?

Kayıtlı journal'lar `part.Bodies.FindObject("EXTRUDE(3)")` ile doludur — bunları kopyalama dürtüsüne diren. O **journal tanımlayıcıları feature-oluşturma sırasını kodlar**; reçete farklı geçmişe sahip bir parçada çalıştığı anda kırılırlar — isimle-datum-arama (tuzak #29, 7.5'te geometrik olarak çözüldü) ile aynı kırılganlıktır. Sağlam tercih sırası:

1. **Dönüş değerlerini yakala** — oluşturma anında `feat.GetBodies()[0]`; bir daha asla arama.
2. **Kendi isimlerin** — oluştururken `SetName`, sonra `Name` ile bul (10.5).
3. **Geometri sorguları** — 10.3 yardımcıları; 1–2 mümkün olmadığında (örn. senin kurmadığın bir parça üzerinde çalışırken).
4. Journal tanımlayıcısıyla `FindObject` — yalnızca geçmişini tamamen kontrol ettiğin bir parçaya karşı tek bir journal çalıştırması içinde.
