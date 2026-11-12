# Literatür taraması

Köşeli parantez içindeki numaralar `references/README.md` dosyasındaki IEEE listesine karşılık gelir.
Aşağıdaki ifadeler o dosyadaki "Read" sütununun izin verdiği düzeyde tutuldu. Okuma düzeyi "summary" olan bir kaynaktan sayı alıntılamadan önce tam metnini aç.

## 1. Literatürün yapısı (raporda "Related Work" bölümü)

### 1.1 Klasik MPPT
- **P&O ve InC** en yaygın yöntemlerdir. Basittirler, ama sabit adım kullandıkları için hız ile kararlı durumdaki salınım arasında bir ödünleşime zorlanırlar [4], [5], [1].
- Femia vd. [8], P&O'nun **perturbasyon adımının ve örnekleme periyodunun dönüştürücü dinamiğine göre seçilmesi gerektiğini** gösterir.
  Bizim bulgumuz da bununla uyumlu: 1 ms periyotta sabit adımlı P&O ve InC ancak küçük adımla düzgün çalıştı (`tune_conventional.py`).
- Elgendy vd. P&O [9] ve InC [10] için uygulama seçeneklerini (referans gerilim veya doğrudan duty kontrolü, adım, örnekleme hızı) karşılaştırır.
  Biz makaleden farklı olarak doğrudan duty kontrolünü seçtik, raporda bu seçimi [9]'a dayandırabiliriz.
- Değişken adımlı InC [11] ve değişken adımlı P&O [12], adımı çalışma noktasına göre ayarlayarak hız ile salınım arasındaki ödünleşimi hafifletir.
  Bulanık MPPT de aynı fikrin dilsel kurallarla yapılmış hâlidir.

### 1.2 Bulanık mantık tabanlı MPPT
- Kuramsal temel bulanık kümeler [2] ve Mamdani denetleyicisidir [3].
- **Shiau vd. [13]**, girdileri farklı altı bulanık MPPT algoritmasını karşılaştırır. Bunlardan biri **"iletkenlik ile artımsal iletkenliğin toplamı"nı (SInC) tek girdi olarak kullanır**.
  ⇒ Referans makaledeki [1] SInC girdisi yeni değildir. Asıl yenilik **CSI'yı ikinci girdi olarak eklemektir**. Bu nokta eleştirel değerlendirme için önemli.
- Robles Algarín vd. [14], 65 W'lık bir sistemde bulanık MPPT'nin P&O'dan daha kısa oturma süresi, daha az güç kaybı ve daha az salınım verdiğini simülasyonla gösterir.
- Yilmaz vd. [15] bulanık MPPT'yi PI tabanlı bir şarj denetleyicisiyle birleştirir.
- Vidal-Martínez vd. [7] son on yılın bulanık PV denetleyicilerini derler. Yayınların %54.2'si Mamdani, %26.7'si Takagi–Sugeno, %19.1'i Type-2 denetleyici kullanır.
  Type-2 denetleyicilerin belirsizlik ayak izi (FOU) sayesinde **sensör gürültüsüne** daha dayanıklı olduğu belirtilir.

### 1.3 Hibrit, optimizasyonlu ve Type-2 yaklaşımlar
- Bollipo vd. [6], MPPT yöntemlerini klasik, akıllı, optimizasyon tabanlı ve hibrit olarak dörde ayırır.
  Kısmi gölgelenmede P–V eğrisinin çok tepeli olduğunu ve klasik yöntemlerin global tepeyi kaçırdığını vurgular. Bizim çalışmamızın kapsamı dışında kalan bir sınırlılık.
- Metasezgisel ve bulanık hibritler: geliştirilmiş yarasa algoritması ile bulanık mantık [16], ANFIS ile PSO [17]. [17] ayrıca dSPACE ile deneysel doğrulama da yapar.
- Type-2 bulanık MPPT: Altin [18] (aralık Type-2) ve Boudia vd. [19]. [19], simülasyonda Type-2'nin Type-1'e göre daha hızlı yakınsadığını ve daha az salınım yaptığını raporlar.

### 1.4 Ölçüm belirsizliği ve gürültü (katkımızın dayanağı)
- Intravaia vd. [20], ölçüm belirsizliğinin MPP hesabına etkisini inceler. P&O, InC ve yapay sinir ağı izleyicilerinin gürültüye duyarlılığını karşılaştırır ve belirsizlik altında sinir ağının daha iyi olduğunu bulur.
- Referans makale [1] kendi sonuç bölümünde ölçüm hassasiyetine ve bölme işlemine duyarlılığı bir sınırlılık olarak belirtir ama bunu **test etmez**.
- **Bizim katkımız** bu boşluğu doldurur. SInC + CSI denetleyicisinin gürültü altında nasıl bozulduğunu nicel olarak ölçüyoruz ve bunu bulanık kuralları değiştirmeden, sadece girdi kestirimini iyileştirerek düzeltiyoruz.
  Bu yaklaşım Type-2'ye geçmekten [7], [18], [19] daha basit ve hesaplama açısından daha ucuz bir alternatif.

## 2. Karşılaştırma tablosu (sunumdaki literatür slaytı için)

| Çalışma | Yıl | Yöntem | Bulanık girdiler / ana fikir | Doğrulama | Raporlanan ana sonuç |
|---|---|---|---|---|---|
| Shiau vd. [13] | 2015 | 6 farklı bulanık MPPT | Eğim ve değişimi, ΔP ve ΔV, **SInC (tek girdi)**, açı toplamı | Simülasyon, buck-boost | Her girdinin artı ve eksileri; açı tabanlı girdinin aralığı sonlu |
| Robles Algarín vd. [14] | 2017 | Mamdani bulanık MPPT ve P&O | – | Simulink, 65 W, buck | Bulanık MPPT'nin oturma süresi, güç kaybı ve salınımı P&O'dan daha iyi |
| Altin [18] | 2013 | Aralık Type-2 bulanık MPPT | – | Simülasyon | Type-2 MPPT önerisi |
| Priyadarshi vd. [17] | 2020 | ANFIS + PSO | Nöro-bulanık | dSPACE deney | P&O, PSO, ACO ve ABC'ye göre üstün; "sıfır salınım" iddiası |
| Ali vd. [16] | 2022 | Yarasa algoritması + bulanık | Metasezgisel ayar | Simülasyon | Değişken atmosfer koşullarında hibrit MPPT |
| Boudia vd. [19] | 2025 | Type-2 bulanık MPPT | Dinamik referans gerilime göre hata | Simülasyon | Type-2, Type-1'den daha hızlı ve daha az salınımlı |
| Djilali vd. [12] | 2025 | Değişken adımlı P&O | Bulanık değil | MATLAB | Güç dalgalanmasında %80 azalma; yanıt süresinde %30 iyileşme |
| Intravaia vd. [20] | 2024 | Gürültü duyarlılık analizi | P&O, InC, yapay sinir ağı | Simülasyon | Belirsizlik altında yapay sinir ağı en dayanıklı |
| **Melhaoui vd. [1]** | 2025 | InC + Mamdani bulanık | **SInC + CSI** | Simulink, SPR-210, boost | %97.7 verim, 53.5 ms yakınsama |
| **Bu çalışma** | 2026 | [1]'in yeniden üretimi + dayanıklı SInC kestiricisi | SInC + CSI, EMA filtre + ölü bölge | Python, ortalama model | Yeniden üretim %98.2; %1 gürültüde verim %46.5'ten %92.6'ya |

## 3. Savunmada kullanılabilecek cümleler
- "SInC girdisi 2015'te Shiau ve arkadaşları tarafından tek girdili bir bulanık MPPT'de kullanılmıştı [13]. Referans makalenin katkısı, buna CSI'yı ekleyip kural tabanını genişletmek."
- "P&O'nun örnekleme periyodunun dönüştürücünün oturma süresine göre seçilmesi gerektiği Femia ve arkadaşlarının çalışmasından [8] biliniyor. Bizim taramamız da bunu doğruladı."
- "Gürültüye karşı literatürde genellikle Type-2 bulanık mantık [7], [19] veya sinir ağları [20] öneriliyor. Biz kural tabanına hiç dokunmadan, sadece kestiriciyi iyileştirerek benzer bir dayanıklılık elde ettik."
