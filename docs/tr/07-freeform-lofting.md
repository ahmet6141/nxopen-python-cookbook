> 🌐 [English](../07-freeform-lofting.md) · **Türkçe**

# 07 · Serbest-Form Lofting: Spline'lar, Noktaya-Kapanan Loft'lar ve Parametrik Üreticiler

[01-core-api.md](01-core-api.md) içindeki her şey **tek** bir profilden (extrude/revolve) inşa edilir. Bu sayfa diğer aileyi kapsar: **kesitler yığını üzerinden loft'lanan** katılar — kanat, gövde, nacelle, pal ve şekli bir eksen boyunca sürekli değişen her cismin arkasındaki teknik. Büyük, çok-parçalı headless build'lerde (yüzlerce gövdeli parametrik uçak/UCAV üreticileri, NX 2506) canlı doğrulanmıştır.

**Bu sayfada:** sketch'siz spline'lar (7.1) · Through-Curves lofting (7.2) · loft'u tek uçtan (7.3) veya iki uçtan (7.4) noktaya kapatma · sağlam datum-plane arama (7.5) · idempotent yeniden-çalıştırma (7.6) · Expression'la sürülen parametreler (7.7) · kesişim-hacmi doğrulama (7.8).

Tüm parçacıklar [01-core-api.md](01-core-api.md) içindeki boilerplate'i varsayar: `session = NXOpen.Session.GetSession()` ve `part` çalışma parçasıdır.

---

## 7.1 Sketch gerektirmeyen bağımsız bir spline

```python
b = part.Features.CreateStudioSplineBuilderEx(None)
b.DrawingPlaneOption = NXOpen.Features.StudioSplineBuilderEx.DrawingPlaneOptions.General
b.DrawingPlane = part.Planes.CreatePlane(origin, normal, NXOpen.SmartObject.UpdateOption.WithinModeling)
b.InputCurveOption = NXOpen.Features.StudioSplineBuilderEx.InputCurveOptions.Hide
b.MatchKnotsType    = NXOpen.Features.StudioSplineBuilderEx.MatchKnotsTypes.NotSet
b.IsAssociative = False     # kurulduktan sonra noktalardan bağımsız — üretilmiş geometri için sağlam
b.IsPeriodic    = False     # True = dikişsiz kapalı döngü (gövde halkası); False = keskin firar kenarı (airfoil)
b.Degree        = 3

temp_points = []
for p in points:                                        # points: list[Point3d]
    pt = part.Points.CreatePoint(p)
    temp_points.append(pt)
    gcd = b.ConstraintManager.CreateGeometricConstraintData()
    gcd.Point = pt
    b.ConstraintManager.Append(gcd)

b.Commit()
spline = b.Curve            # Destroy()'dan ÖNCE oku — sonuç bu property'de yaşar
b.Destroy()

# yardımcı (construction) noktaları temizle (IsAssociative=False iken güvenlidir):
for pt in temp_points:
    part.Points.DeletePoint(pt)
```

> **Tuzak:** `CreateSketchSplineBuilder` **aktif bir sketch** gerektirir — hiçbiri açık değilken `Commit()` *"Incorrect object for this operation."* hatasını fırlatır. Sketch'siz eğri üretimi için (parametrelerden geometri kurarken normal durum budur, bir GUI sketch oturumundan değil) her zaman **`CreateStudioSplineBuilderEx`** kullan.
>
> **Tuzak:** .NET referansı bir `MatchKnotsTypes.None` üyesi listeler, ama `None` Python'da ayrılmış bir kelimedir — `MatchKnotsTypes.None` daha NX journal'ı yüklemeden bir **`SyntaxError`** olur. Python binding'i (ve GUI'den kaydedilen her Python journal'ı) bunu **`NotSet`** olarak yazar.

---

## 7.2 Through-Curves loft — kesitleri tek bir katıya yığma

```python
b = part.Features.FreeformSurfaceCollection.CreateThroughCurvesBuilder1(None)

# toleranslar — bu tam değerler prodüksiyon journal'larında kanıtlanmıştır
b.Alignment.AlignCurve.DistanceTolerance  = 0.01
b.Alignment.AlignCurve.ChainingTolerance  = 0.0095
b.Alignment.AlignCurve.AngleTolerance     = 0.5
b.SectionTemplateString.DistanceTolerance = 0.01
b.SectionTemplateString.ChainingTolerance = 0.0095
b.SectionTemplateString.AngleTolerance    = 0.5

b.Alignment.AlignType = NXOpen.GeometricUtilities.AlignmentMethodBuilder1.Type.Parameter   # kritik, aşağıya bak
b.Construction   = NXOpen.Features.ThroughCurvesBuilder1.ConstructionMethod.Normal
b.PatchType      = NXOpen.Features.ThroughCurvesBuilder1.PatchTypes.Multiple
b.BodyPreference = NXOpen.Features.ThroughCurvesBuilder1.BodyPreferenceTypes.Solid   # kapalı kesit -> kapaklı katı
b.PreserveShape = False
b.ClosedInV = False
b.NormalToEndSections = False

for spline, help_point in zip(sections, help_points):    # sections: list[Spline], loft sırasıyla;
    sec = part.Sections.CreateSection(0.0095, 0.01, 0.5)  # help_point: spline'ın üzerinde (veya yakınında) bir
    sec.SetAllowedEntityTypes(NXOpen.Section.AllowTypes.OnlyCurves)  # Point3d — ör. üretildiği ilk girdi noktası
    rule = part.ScRuleFactory.CreateRuleCurveDumb([spline])
    sec.AllowSelfIntersection(False)
    sec.AllowDegenerateCurves(False)
    sec.AddToSection([rule], spline, None, None, help_point, NXOpen.Section.Mode.Create, False)
    b.SectionsList.Append(sec)

feat = b.CommitFeature()
b.Destroy()
body = feat.GetBodies()[0]
```

> **Temiz, burulmasız bir loft'un sırrı:** her kesitin spline'ını **aynı nokta sayısı ve aynı nokta sırasıyla** üret (bir airfoil için her zaman firar kenarı → üst yüzey → hücum kenarı → alt yüzey → firar kenarı) ve `AlignType = Parameter` ayarla. NX o zaman kesitler arasında bir eşleşme tahmin etmek yerine nokta-indeksini nokta-indeksine eşler — hücum kenarları hücum kenarlarıyla, firar kenarları firar kenarlarıyla hizalanır, burulma oluşmaz. Bir Journal kaydında göreceğin GUI-kayıtlı `SetStartCurveOfClosedLoop` / `ReverseDirectionOfLoop` çağrıları *tutarsız* girdi eğrileri için elle yapılan düzeltmelerdir — üretimi sen kontrol ediyorsan ve sıralamayı baştan tutarlı tutuyorsan gereksizdirler.
>
> Kesit sırası = `SectionsList.Append` sırası = loft'un V yönü. Bu builder'da loft, inline boolean'lar için **yalnızca oluşturma (create-only)** işlemidir — bkz. [04-boolean-and-geometry-rules.md](04-boolean-and-geometry-rules.md); gövdeyi tek bir loft olarak kur, geri kalan her şeyi ona unite et.

---

## 7.3 Loft'u TEK bir noktaya kapatma — güdük değil, gerçekten sivri burun/uç

Son kesiti küçük bir halka olan kapaklı bir loft, güdük görünür. Gerçekten sivri bir uç (ogive burun, kanat ucu, spinner) elde etmek için, eğri kesitlerinden *önce* (veya sonra) yerleştirilen, **tek bir noktadan** oluşan bir kesit ekle:

```python
pole = part.Points.CreatePoint(NXOpen.Point3d(x0, 0.0, 0.0))
pole.SetVisibility(NXOpen.SmartObject.VisibilityOption.Visible)   # kullanılabilmesi için "dumb" nokta görünür olmalı

psec = part.Sections.CreateSection(0.0095, 0.01, 0.5)
psec.SetAllowedEntityTypes(NXOpen.Section.AllowTypes.CurvesAndPoints)      # kritik — noktalar eğri değildir
prule = part.ScRuleFactory.CreateRuleCurveDumbFromPoints([pole])
psec.AddToSection([prule], pole, None, None, pole.Coordinates, NXOpen.Section.Mode.Create, False)

b.SectionsList.Append(psec)          # eğri kesitlerinden ÖNCE ekle -> loft bu noktaya kapanır
# ... eğri kesitlerini 7.2'deki gibi ekle ...
```

> Nokta, loft feature'ının bir **parent'ı** olur — silme, gizlemek için `Blank()` kullan. Canlı bir feature'ın parent'ını silmek ya başarısız olur ya da feature'ı bozar.

---

## 7.4 Loft'u İKİ ucundan da noktaya kapatma

Aynı hile, aynı loft'un her iki ucunda da işe yarar — her iki uçta da motor/tahrik açıklığı olmayan tam sivri-uçlu bir gövde için kullanışlıdır (bir planör gövdesi, bir uçan-kanat ucu):

```python
def loft_with_poles(start_pole, end_pole, sections, helps, name):
    b = part.Features.FreeformSurfaceCollection.CreateThroughCurvesBuilder1(None)
    # ... 7.2'deki gibi toleranslar/Alignment/Construction ...
    if start_pole is not None:
        append_pole_section(b, start_pole)          # 7.3'teki nokta-kesit yardımcısı
    for spline, help_pt in zip(sections, helps):
        # ... 7.2'deki gibi normal Section.Append ...
        pass
    if end_pole is not None:
        append_pole_section(b, end_pole)             # AYNI yardımcı, SON olarak eklenir
    feat = b.CommitFeature()
    feat.SetName(name)                               # isimli -> cleanup_previous (7.6) tekrar çalıştırmada bulabilir
    b.Destroy()
    return feat.GetBodies()[0]
```

7.3'teki nokta-kesit kodunu küçük bir `append_pole_section(builder, pole)` yardımcısına çıkar — her iki uçta da birebir aynı şekilde tekrar kullanılır.

**Pratik bir genişletme:** her uçtaki pole'u konfigürasyona göre opsiyonel yap, ve bir açıklığın gerektiği yerde (bir motor bağlantısı, bir kanal girişi gibi) o uca yakın minimum kesit yarıçapını bir pole yerine sabit bir değere clamp'le:

```python
floor_r = spinner_radius if station_is_the_open_end else 2.5     # 2.5 mm = pratik "sıfıra yakın" taban
half_width  = max(nominal_half_width  * shape_fn(t), floor_r)
half_height = max(nominal_half_height * shape_fn(t), floor_r)
```

Tek bir üretici fonksiyon, hangi ucun pole hangi ucun `floor_r` clamp'i aldığını değiştirerek hem tam sivri-uçlu bir gövde **hem de** herhangi bir ucunda düz, ölçülü bir kesik olan bir gövde üretebilir — ayrı bir kod yoluna gerek yok.

---

## 7.5 İsimle datum-plane arama — sağlam yöntem

`Datums.FindObject("DATUM_CSYS(0) XZ plane")` yalnızca tam olarak o isimle o mutlak datum'a sahip bir parçada çalışır — yeni bir parça, boş bir parça ya da farklı şablonlu bir parça bunu bulamaz ve *"No object found with this name."* hatası alırsın. Kanıtlanmış, sağlam yedekleme (fallback) zinciri:

```python
def find_or_create_xz_plane():
    try:
        return part.Datums.FindObject("DATUM_CSYS(0) XZ plane")   # 1) hızlı yol — yalnızca şablon parçalar
    except Exception:
        pass

    def xz_by_geometry():                                    # 2) isim değil GEOMETRİYLE ara
        for o in part.Datums:
            if isinstance(o, NXOpen.DatumPlane) and abs(abs(o.Normal.Y) - 1.0) < 1e-6 \
               and abs(o.Normal.X) < 1e-6 and abs(o.Normal.Z) < 1e-6:
                return o
        return None

    plane = xz_by_geometry()
    if plane is not None:
        return plane

    # 3) hiçbiri yoksa -> mutlak orijinde bir datum CSYS kur, sonra tekrar ara
    db = part.Features.CreateDatumCsysBuilder(None)
    xf = part.Xforms.CreateXform(NXOpen.Point3d(0.0, 0.0, 0.0), NXOpen.Vector3d(1.0, 0.0, 0.0),
                                  NXOpen.Vector3d(0.0, 1.0, 0.0), NXOpen.SmartObject.UpdateOption.WithinModeling, 1.0)
    csys = part.CoordinateSystems.CreateCoordinateSystem(xf, NXOpen.SmartObject.UpdateOption.WithinModeling)
    db.Csys = csys
    db.CommitFeature()
    db.Destroy()
    return xz_by_geometry()                                  # az önce kurulan düzlemi bulur
```

> **İlgili tuzak:** `DatumPlaneBuilder.SetCornerPoints(c1..c4)` script'ten çağrıldığında *"Datum plane undefinable"* hatası fırlatır — GUI-kayıtlı journal'larda görünse bile. Atla; onun yerine `builder.ResizeDuringUpdate = True` ayarla ve boyutlandırmayı NX'e bırak.

---

## 7.6 Kendi kendini temizleyen yeniden-üretim — idempotent regenerasyon

Bir parametreyi değiştirdikten sonra eski geometriyi elle silmeden **aynı** parçada tekrar çalıştırabileceğin bir üretici:

```python
def cleanup_previous(mark, prefix):
    doomed = [f for f in part.Features if f.Name.upper().startswith(prefix)]
    doomed += [c for c in part.Curves if c.Name.upper().startswith(prefix + "_SEC")]
    doomed += [p for p in part.Points if p.Name.upper().startswith(prefix + "_SEC")]
    if doomed:
        session.UpdateManager.AddObjectsToDeleteList(doomed)
        session.UpdateManager.DoUpdate(mark)
```

Bunu herhangi bir şey inşa etmeden **önce** çağır. Yalnızca oluşturduğun her feature/eğri/nokta'ya tutarlı biçimde `feature.SetName("PROJEM_...")` verirsen çalışır — isimsiz bir nesne filtre tarafından eşleştirilemez ve temizlenmez, bir sonraki çalıştırmada yetim olarak kalır.

> **Expression'lar Feature DEĞİLDİR** — `cleanup_previous`'tan dokunulmadan geçerler. Amaç da bu: Tools → Expressions'ta bir değeri değiştir, journal'ı tekrar çalıştır, sadece *geometri* yeniden üretilirken senin parametre düzenlemen kalıcı olur. Bkz. 7.7.

---

## 7.7 Parametrik Expression okuma-varsa/yoksa-oluşturma + geri-yazma

7.6 ile eşleştirerek bir journal'ı, sabit kodlanmış sabitler yerine Tools → Expressions'tan sürülen, düzenlenebilir ve tekrar-çalıştırılabilir bir üreticiye dönüştür:

```python
def P(name, default, unit=None):
    for ex in part.Expressions:
        if ex.Name.lower() == name.lower():
            return ex.Value                                   # zaten var -> oku
    rhs = str(default)
    if unit is None:
        part.Expressions.Create(f"{name}={rhs}")               # birimsiz (oran, kesit kodu, sayım)
    else:
        u = part.UnitCollection.FindObject(unit)                # "MilliMeter" / "Degrees" / ...
        part.Expressions.CreateWithUnits(f"{name}={rhs}", u)
    return default                                              # ilk çalıştırmada varsayılanı da döndür

def set_p(name, value):
    for ex in part.Expressions:
        if ex.Name.lower() == name.lower():
            ex.RightHandSide = f"{value:.3f}"
            return
```

Her expression ismi için tek, projeye özgü bir önek kullan (`myproj_wing_span`, `myproj_root_chord`, ...) — aynı parçadaki başka üreticilerle çakışmayı önler ve `cleanup_previous`'un isimlendirme filtresini (7.6) belirsizlikten kurtarır. Bir üretici bir yakınsama/boyutlandırma döngüsü çalıştırıyorsa, yakınsanmış sonuçlar üzerinde sonda `set_p(...)` çağır — böylece sonradan NX arayüzünden görünür ve elle düzenlenebilir olurlar.

---

## 7.8 Boolean Intersect ile gerçek kesişim hacmini doğrulama

`nx_inspect` tarzı interference sayımları sana iki gövdenin çakıştığını *bildirir*; bu ise sayısal olarak *ne kadar* çakıştığını verir — sadece dokunması gereken (veya hiç dokunmaması gereken) herhangi iki parça için ikinci, nicel bir doğrulama katmanı olarak kullanışlıdır:

```python
bb = part.Features.CreateBooleanBuilderUsingCollector(NXOpen.Features.BooleanFeature.Null)
bb.Operation = NXOpen.Features.Feature.BooleanType.Intersect
bb.RetainTarget = True
bb.RetainTool   = True                       # iki orijinali de koru — bu bir sonda (probe), gerçek birleştirme değil
bb.Targets.Add(body_a)
bb.Tools.Add(body_b)                         # not: bir SelectObjectList üzerinde .Add, ScCollector DEĞİL
before = {b.Tag for b in part.Bodies}
bb.Commit()
new_bodies = [b for b in part.Bodies if b.Tag not in before]   # varsa, kesişim katısı/katıları

# hacim: NewMassProperties(units[:take], 0.99, [new_body]).Volume — 2.9'daki kanıtlanmış reçete
# temizlik: her yeni gövde için uf.Obj.DeleteObject(b.Tag), sonra bb.Destroy()
```

- **Kesişim yoksa `Commit()` fırlatır.** İstisnayı "0 mm³ çakışma" olarak ele al (dokunmaması-gereken bir çift için PASS), gerçek bir hata olarak değil.
- Bu sarmalayıcının `uf.Modl`'unda `AskMassProps3d` yoktur — hacim için tek yol hâlâ `NewMassProperties`'tir (2.9).

---

## Tuzak özeti

Bunlar burada tekrarlamak yerine [03-pitfalls.md](03-pitfalls.md) içinde birer satırı hak edecek kadar büyük — oradaki #26–29'a bak: çoklu-gövde kitlerinde kütle-özellikleri collector'ının sıfır döndürmesi tuzağı, sketch'li-vs-sketch'siz spline tuzağı, `SetCornerPoints`, ve isimle-datum-arama'nın kırılganlığı.
