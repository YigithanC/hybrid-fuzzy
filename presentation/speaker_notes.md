# Konuşma notları

`build_presentation.py` tarafından üretilir; slaytlardaki notlarla aynıdır.

## 1. Kapak

(~30 sn) Merhaba. Projemde Scientific Reports'ta 2025'te yayımlanan, fotovoltaik sistemlerde
maksimum güç noktası takibi için hibrit bir bulanık mantık denetleyicisi öneren makaleyi inceledim.
Önce makalenin yöntemini sıfırdan Python'da yeniden ürettim, sonra makalenin test etmediği bir
zayıf noktayı, ölçüm gürültüsünü, inceleyip buna bir çözüm geliştirdim. Sonunda canlı demo yapacağım.

## 2. Problem: güneş paneli tek bir noktada en çok gücü verir

(~1 dk) Bir PV panelin akım–gerilim eğrisi doğrusal değil; güç eğrisinin tek bir tepesi var,
buna maksimum güç noktası, MPP deniyor. Sorun şu: bu nokta ışınım ve sıcaklıkla yer değiştiriyor.
Grafikte görüldüğü gibi ışınım düşünce MPP gücü de, MPP gerilimi de değişiyor.
Panel ile yük arasına bir DC–DC yükseltici dönüştürücü koyuyoruz; anahtarlama oranı D'yi değiştirerek
panelin gördüğü direnci ayarlıyoruz. Bizim sistemde 1000 W/m²'de optimum D yaklaşık 0,61.
MPPT algoritmasının işi D'yi sürekli bu noktada tutmak. Uygulama alanı: çatı sistemleri, şebeke
bağlantılı inverterler, şarj denetleyicileri. Her yüzde birlik verim kaybı doğrudan enerji kaybı.

## 3. Klasik yöntemlerin sınırı ve bulanık mantığın gerekçesi

(~1 dk) En yaygın iki yöntem P&O, yani değiştir ve gözle, ve artımsal iletkenlik InC.
İkisi de sabit adım kullanır. Büyük adım hızlı yakınsar ama MPP etrafında salınır; küçük adım az salınır
ama ışınım değişince yavaş kalır. Bu bir ödünleşim.
Bulanık mantık burada adımı uyarlamalı yapıyor: MPP'den uzaksan büyük, yakınsan küçük adım.
Bunu bir uzman gibi dilsel kurallarla ifade ediyoruz: "çok soldaysan D'yi çok azalt" gibi.
Ayrıca panelin tam matematiksel modeline ihtiyaç duymuyor; doğrusal olmayan sisteme uygun.

## 4. Literatür: benzer çalışmalar

(~1,5 dk) Literatürü dört grupta taradım; tabloda en ilgili olanlar var.
Önemli bir bulgu: SInC girdisi yeni değil. Shiau ve arkadaşları 2015'te altı bulanık MPPT'yi
karşılaştırmış, bunlardan biri tam olarak SInC'yi tek girdi olarak kullanıyor. Yani referans makalenin
asıl katkısı CSI'yı ikinci girdi olarak eklemek.
Gürültü tarafında literatür genelde Type-2 bulanık mantık ya da sinir ağı öneriyor; Intravaia 2024
gürültü duyarlılığını P&O, InC ve sinir ağı için inceliyor ama bulanık InC için değil.
Bizim katkımız bu boşluğa denk geliyor: kurallara dokunmadan, sadece girdi kestirimini iyileştiriyoruz.
Toplam 23 kaynak var, hepsi raporda IEEE formatında.

## 5. Teori: bulanık küme ve dilsel değişken

(~1,5 dk) Klasik kümede bir eleman ya içindedir ya değildir. Zadeh'in bulanık kümesinde
bir elemanın üyelik derecesi 0 ile 1 arasında bir sayıdır, μ_A(x).
Üyelik fonksiyonu bu dereceyi veren eğridir; biz üçgen kullanıyoruz, uçlarda omuz şeklinde.
Dilsel değişken, değerleri kelime olan değişkendir: SInC değişkeninin yedi terimi var: negatif büyük,
negatif orta, negatif küçük, sıfır, pozitif küçük, orta, büyük.
Bulanıklaştırma, ölçülen sayının her terime ne kadar ait olduğunu bulmaktır. Örneğin SInC = 0,05 için
"pozitif küçük" derecesi 0,56, "sıfır" derecesi 0,44. Komşu üçgenler toplamı 1 olacak şekilde
örtüşüyor; buna Ruspini bölüntüsü deniyor. Bu yüzden bir değer en fazla iki terimi ateşler.

## 6. Teori: Mamdani çıkarımı ve durulaştırma

(~1,5 dk) Bulanık çıkarım dört adımdan oluşur. Bulanıklaştırmadan sonra kural tabanı gelir:
"EĞER SInC pozitif küçük VE CSI sıfır İSE ΔD negatif orta" gibi kurallar.
VE işlemi için minimum alınır; bu kuralın ateşlenme gücüdür. Mamdani yönteminde çıkış kümesi
bu güçte kırpılır, tüm kuralların çıkışları maksimum ile birleştirilir.
Durulaştırmada bu birleşik kümenin ağırlık merkezi alınır; sonuç tek bir sayı, ΔD.
Sugeno'da ise çıkış bir küme değil, sabit ya da doğrusal fonksiyondur; hesaplama daha ucuz ama
yorumlanabilirlik daha az. Makale Mamdani kullanıyor, ben de öyle uyguladım.
Type-2'de üyelik derecesinin kendisi de bulanık; gürültüye dayanıklılık için öneriliyor,
sonda bununla kıyaslayacağım.

## 7. Makalenin yöntemi: sistem mimarisi ve girdiler

(~1,5 dk) Sistem: SPR-210 panel, yükseltici dönüştürücü ve 50 ohm yük. Denetleyici her 1 ms'de
panelin gerilim ve akımını örnekliyor.
Birinci girdi SInC: akım/gerilim artı akım değişimi/gerilim değişimi. Güç eğrisinin türevini sıfırlamak
bu toplamı sıfırlamakla aynı; yani MPP'de SInC sıfır. SInC pozitifse MPP'nin solundayız, D azaltılmalı;
negatifse sağındayız, D artırılmalı.
İkinci girdi CSI: SInC'nin bir önceki örneğe göre değişimi. Çalışma noktasının MPP'ye hangi hızla
yaklaştığını ya da uzaklaştığını söylüyor; aşmayı ve salınımı azaltmak için.
Çıkış ΔD; D'ye ekleniyor ve 0,05 ile 0,95 arasında sınırlanıyor.

## 8. Kural tabanı: 5 × 7 = 35 Mamdani kuralı (makale Tablo 5)

(~1,5 dk) Kural tabanı makaledeki Tablo 5. Satırlar CSI, sütunlar SInC.
Okuma örneği: SInC negatif büyükse, yani MPP'nin çok sağındaysak, CSI ne olursa olsun ΔD pozitif büyük:
D'yi hızla artır.
Ortadaki ilginç kısım: SInC küçükken CSI büyükse, yani nokta MPP'ye hızla yaklaşıyorsa,
çıkış sıfır: "zaten geliyorsun, dokunma". Bu aşmayı engelleyen kısım.
Makale üyelik fonksiyonlarının sayısal köşe noktalarını vermiyor. Ben D'yi 0,1'den 0,9'a tarayıp
SInC ve CSI'nın aldığı değer aralıklarını ölçtüm, köşe noktalarını buradan çıkardım, sonra
küçük bir ızgara aramasıyla ayarladım.

## 9. Kontrol yüzeyi ve bir çıkarım örneği

(~1 dk) Kural tabanının bütün girdi uzayındaki karşılığı bu yüzey. SInC negatif tarafta yüzey
yukarıda, D artıyor; pozitif tarafta aşağıda. MPP civarında eğim yumuşak; bu küçük adımlar demek.
Sağda somut bir örnek: SInC 0,05, CSI 0. İki kural ateşleniyor: PS ve ZE için NM, gücü 0,56;
ZE ve ZE için ZE, gücü 0,44. Ağırlık merkezi ΔD = −0,0091 veriyor: D'yi biraz azalt.
Bu hesabı demoda kaydırıcılarla canlı göstereceğim.

## 10. Deneysel çalışma: ortam, parametreler, ölçütler

(~1,5 dk) Makale MATLAB/Simulink kullanıyor ve kod paylaşmıyor; ben her şeyi Python'da sıfırdan yazdım.
Panel: tek diyot modeli; seri ve paralel direnci veri sayfasına tam oturacak şekilde fsolve ile buldum:
210 W ve 7,62 ohm, makaleyle aynı.
Dönüştürücü: ortalama durum uzayı modeli, 10 mikrosaniye adımla Euler.
Hazır veri seti yok: senaryolar sentetik. Makalenin Şekil 17 ışınım profili: her 0,2 saniyede
200 ile 1000 arasında basamak. Bir de yük basamağı testi: 50, 20, 35 ohm; bu test hiç ayar için
kullanılmadı.
Ölçütler: ortalama verim, RMSE, RMS yüzdesi ve ±%2 banda girip kalma süresi olarak yakınsama süresi.

## 11. Makalenin sonuçları ve bizim yeniden üretimimiz

(~1,5 dk) Bu tablo makalenin Tablo 6'sı; her hücrede önce bizim değer, parantezde makalenin değeri.
Makalenin ana iddiası: önerilen denetleyici en yüksek verim, en hızlı yakınsama ve en düşük hatayı
veriyor. Bu sıralama bizde de aynen çıktı: önerilen 98,19, makalede 97,7.
Mutlak değerler yarım ile bir puan farklı. Nedenleri: ortalama dönüştürücü modeli, kendi
üyelik fonksiyonu köşe noktalarımız ve yakınsama süresinin tanımı; makale bunu tanımlamıyor.
Yakınsama sürelerimiz daha kısa çünkü biz ±%2 bandını kullandık.

## 12. Yeniden üretim: zaman yanıtı ve yük testi

(~1 dk) Solda dört denetleyicinin güç ve D yanıtı; kırmızı noktalı çizgi ulaşılabilecek en yüksek güç.
P&O ve InC'de D'deki testere dişi salınım görülüyor; bulanık denetleyicilerde daha düzgün.
1,8 saniyedeki 600'den 200'e düşüşte Alg. 3 çok yavaş toparlanıyor; CSI eklenince hızlanıyor.
Bu makalenin iddiasıyla uyumlu.
Sağda yük basamağı testi: bu test hiç ayar için kullanılmadı, yani bağımsız bir doğrulama.
1000 W/m²'de önerilen RMSE 24,4; makalede 25,2. Çok yakın.

## 13. Eleştirel değerlendirme

(~1,5 dk) Güçlü yönleri: rapor edilen iyileşme tutarlı ve biz de bağımsız olarak elde ettik;
kural tabanı yorumlanabilir; yöntem hesaplama olarak hafif.
Sınırlılıklar: üyelik fonksiyonlarının sayısal değerleri verilmemiş, bu yüzden tam aynısını
üretmek mümkün değil. Yakınsama süresi tanımlanmamış. Sadece simülasyon var, donanım yok.
Kısmi gölgelenmede güç eğrisi çok tepeli olur; SInC yerel tepede de sıfırdır, yani global MPP'yi
kaçırabilir. Bu test edilmemiş.
En önemlisi: makale kendi sonuç bölümünde ölçüm hassasiyetine ve bölmeye duyarlılığı bir sınırlılık
olarak yazıyor ama hiç test etmiyor. Benim katkım tam buradan çıkıyor.

## 14. Özgün katkı: gürültüye çok duyarlı bir denetleyici

(~1,5 dk) Neden gürültü? MPP civarında bir örnekten diğerine gerilim değişimi sadece onlarca milivolt.
Sensörde ±%0,5'lik gürültü 0,24 volt; yani ΔV neredeyse tamamen gürültü oluyor.
Bu durumda ΔI/ΔV sıfır ortalamalı rastgele bir oran olur ama I/V hep pozitif. SInC sistematik olarak
pozitife kayıyor; denetleyici sürekli "soldayım" sanıp D'yi alt sınıra itiyor. P&O'da da aynı mekanizma var.
CSI bir farkın farkı olduğu için gürültüyü bir kez daha büyütüyor.
Sonuç: %1 gürültüde önerilen denetleyicinin verimi yüzde 46,5,
P&O'nunki yüzde 37,5 düzeyine düşüyor. Gürültüyü kontrolörün gördüğü her V ve I örneğine,
tam ölçeğin yüzdesi olarak ekledim, her seviye beş farklı tohumla.

## 15. Çözüm: gürültüye dayanıklı SInC kestiricisi

(~1,5 dk) Çözümün ana fikri: bulanık kurallara ve üyelik fonksiyonlarına hiç dokunmamak;
sadece denetleyiciye giren SInC ve CSI'yı daha iyi kestirmek.
Üç parça var, her biri ayrı açılıp kapatılabiliyor, böylece ablasyon yapabildim.
F: gerilim ve akıma üstel hareketli ortalama filtresi, alfa 0,5.
D: biriktirilmiş fark ölü bölgesi. Türevi her örnekte değil, son referans örneğe göre hesaplıyorum ve
ancak gerilim farkı 0,5 voltu geçince güncelliyorum. Böylece paydadaki ΔV hiçbir zaman gürültü
seviyesine inmiyor. Bu, mekanizmadaki sapmanın kaynağını doğrudan kesiyor.
C: SInC'yi ±1,5'te kırpma.
Alfa ve delta değerlerini 100–102 tohumlarında seçtim; sonuçları farklı tohumlarda, 0–4'te raporluyorum.
Böylece ayar verisiyle test verisi ayrı.

## 16. Sonuç: %1 gürültüde verim %46'dan %93'e

(~1,5 dk) Yatay eksende gürültü seviyesi, dikeyde ortalama verim, beş tohumun ortalaması ve
standart sapması. Kesikli çizgiler makaledeki denetleyiciler, düz çizgiler dayanıklı sürümler.
Önerilen denetleyicinin verimi %0,5 gürültüde yüzde 85,9 iken
kestiriciyle yüzde 96,2; %1 gürültüde ise yüzde
46,5 iken yüzde 92,6.
Standart sapma da çok küçülüyor.
Sadece filtre eklemek P&O'yu kurtarmıyor: %1'de hâlâ %38. Yani sorun sadece gürültü genliği değil,
türevin kendisi; ölü bölge bu yüzden gerekli.
İlginç bir bulgu: gürültüde en dayanıklı olan, CSI'sız tek girdili Alg. 3'ün dayanıklı sürümü.
CSI temiz koşulda yardımcı ama gürültüde yüke dönüşüyor.

## 17. Ablasyon ve bedeli

(~1,5 dk) Ablasyon: %1 gürültüde yalnız filtre 87,2, yalnız ölü bölge
64,7, ikisi birlikte 92,6. Yani iki parça birbirini
tamamlıyor: filtre genliği düşürüyor, ölü bölge paydayı koruyor.
Kırpmanın hiçbir etkisi yok; ölü bölge paydayı sınırlayınca SInC zaten kırpma sınırına ulaşmıyor.
Bunu dürüstçe raporluyorum: üç parçadan biri gereksiz çıktı.
Bedeli: gürültüsüz koşulda verim 98,2'den 97,0'a düşüyor, ortalama yakınsama 34'ten 95 ms'ye çıkıyor;
filtre gecikmesi ve ölü bölge yüzünden. Yani bu bir ödünleşim; gürültülü ortamda değerli.
Son olarak üçgen yerine Gauss üyelik fonksiyonu denedim: %1'de 93,3 ve sapma daha küçük.

## 18. Canlı demo

(~3 dk) Komut: python -m demo.
1) Deney sekmesi: senaryo "Özel basamaklar", 1000, 300, 700; gürültü önce 0. P&O, önerilen ve
   önerilen + dayanıklıyı seç, çalıştır. Üçü de iyi.
2) Gürültüyü %0,5'e çek, tekrar çalıştır: P&O yaklaşık %41'e, önerilen %87'ye düşer; dayanıklı %94 civarı kalır.
   D grafiğinde P&O'nun alt sınıra indiğini göster: anlattığım sapma bu.
3) Bulanık çıkarım sekmesi: SInC 0,05, CSI 0 → iki kural, ΔD = −0,0091. SInC'yi negatife çek:
   ΔD pozitif olur. CSI'yı büyüt: "dokunma" kuralı devreye girer.
Hoca bir koşul sorarsa (ör. 45 °C) sıcaklık kaydırıcısıyla anında dene.

## 19. Sonuç

(~1 dk) Özetle: makalenin yöntemini sıfırdan yeniden ürettim ve ana iddiasını doğruladım.
Makalenin test etmediği gürültü zayıflığını nicel olarak gösterdim ve mekanizmasını açıkladım.
Kural tabanına dokunmayan basit bir kestiriciyle %1 gürültüde verimi %46'dan %93'e çıkardım;
bedeli gürültüsüz koşulda biraz daha yavaş yakınsama.
Gelecek çalışma: gürültü seviyesini çevrim içi kestirip ölü bölgeyi uyarlamak, kısmi gölgelenme ve
Type-2 ile kıyas, donanımda doğrulama.
Yapay zekâ kullanımını raporda ayrı bir bölümde açıkladım. Teşekkürler, sorularınızı alabilirim.
