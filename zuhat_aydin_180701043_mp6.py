import os
import time
import re
# import shelve


class Tarama:
    def __init__(self):
        # ekrana istenildiği gibi makale adlarını yazdırmak için {makaleno1:'makaleadı1',...}
        self.makaleno_makaleadi = {}
        # işlemler için kullanılacak olan sözlükler
        self.wordlocation = {}
        self.citations = {}
        self.citationcounts = {}
        self.pagerank = {}
        # dosyaları tek tek okuyabilmek için
        self.files = []
        # konsolda fonksiyonları tek tek çağırmamak için
        self.indexleme()
        self.calculatepagerank()
        # # {word:{makale:[loc1, loc2, ..., locN]}}
        # self.wordlocation = shelve.open('wordlocation', writeback=False, flag='c')
        #
        # # {makale:[makaleye atıf yapan makale,...],...}
        # self.citations = shelve.open('citations', writeback=False, flag='c')
        #
        # # {makale: 'atıf yapılan makale sayısı',...}
        # self.citationcounts = shelve.open('citationcounts', writeback=False, flag='c')

    # def __del__(self):
    #     self.close()
    #
    # # def close(self):
    #     if hasattr(self, 'wordlocation'):
    #         self.wordlocation.close()
    #     if hasattr(self, 'citations'):
    #         self.citations.close()
    #     if hasattr(self, 'citationcounts'):
    #         self.citationcounts.close()

    def indexleme(self, path='metadata'):
        # istenilen dizindeki tüm dosya yollarını alan döngü
        for r, d, f in os.walk(path):
            for file in f:
                self.files.append(os.path.join(r, file))
        # kullanıcıya yapılacak olan işlem bilgisini veriyoruz
        print("\n*** Makaleler İndexleniyor ***")
        # dosya yollarını tek tek alıp işlemler sokacak olan döngü
        for dosya_adi in self.files:
            # makale numarasını alıyoruz
            makale_no = re.search('\d+', dosya_adi).group()
            # yapılan işlemin "tamamlanması" hakkında kullanıcıya bilgi veren koşullar
            if makale_no == "9301084":
                print('\n*** %25 Tamamlandı ***')
            elif makale_no == "9310073":
                print('*** %50 Tamamlandı ***')
            elif makale_no == "9406036":
                print('*** %75 Tamamlandı ***')
            # dosyaları okutuyoruz
            icerik = open(dosya_adi, "r").read()
            # dosyaların içinde makale adlarını çekebilmek için
            baslik = re.search("Title:([\s\S]+)Authors?:", icerik).group(1)
            baslik = "".join(baslik.split("\n"))
            # istenilen çıktıyı verebilmek için başlıkları sözlüğe atıyoruz
            self.makaleno_makaleadi[makale_no] = baslik
            # makalenin özet kısmını yakalıyoruz
            ozet_ayiraci = re.compile(r"[^-]\n\\([\s\S]+)\\$")
            ozet = re.search(ozet_ayiraci, icerik).group(1)
            # başlık ve özetteki kelimeleri yakalıyoruz, büyük harflerden kurtuluyoruz
            kelimeler = re.findall('\w+', baslik.lower() + ozet.lower())
            # kelimeleri işlem yapacağımız sözlüklere istenildiği gibi yerleştiriyoruz
            for i in range(len(kelimeler)):
                self.wordlocation.setdefault(kelimeler[i], {})
                self.wordlocation[kelimeler[i]].setdefault(makale_no, [])
                self.wordlocation[kelimeler[i]][makale_no].append(i)
        # kullanıcıya yapılan işlemin sonlandığı bilgisini veriyoruz
        print('\n*** Makaleler İndexlendi ***')
        # atıf verilerinin olduğu dosyayı okuyoruz
        veriler = open('citations.txt', "r").read()
        # atıf verilerini tuplelar listesine dönüştürüyoruz
        atiflar = re.findall("\n(\d+)\t(\d+)", veriler)
        # kullanıcıya yapılacak olan işlem bilgisini veriyoruz
        print('\n*** Atıf İndexlemesi Yapılıyor ***')
        # atıf verilerini tek tek işleyecek döngü
        for atif_yapan, atif_alan in atiflar:
            # kullanıcıya yapılan işlemin "tamamlanması" hakkında bilgi verme amaçlı koşullar
            # if atif_yapan == "9810138":
            #     print('\n*** %25 Tamamlandı ***')
            # elif atif_yapan == "105034":
            #     print('*** %50 Tamamlandı ***')
            # elif atif_yapan == "9911054":
            #     print('*** %75 Tamamlandı ***')
            # atıf verilerini işlem yapılacak sözlüklere istenildiği gibi yerleştiriyoruz
            self.citations.setdefault(atif_alan, [])
            self.citations[atif_alan].append(atif_yapan)
            self.citationcounts.setdefault(atif_alan, 0)
            self.citationcounts[atif_alan] += 1
        # kullanıcıya yapılan işlemin sonlandığı bilgisini veriyoruz
        print('\n*** İndexleme İşlemleri Bitti ***')

    def getmatchingpages(self, q):
        results = {}
        # Split the words by spaces
        words = [word.lower() for word in q.split()]
        if words[0] not in self.wordlocation:
            return results, words
        makale_set = set(self.wordlocation[words[0]].keys())
        for word in words[1:]:
            if word not in self.wordlocation:
                return results, words
            makale_set = makale_set.intersection(self.wordlocation[word].keys())
        for makale in makale_set:
            results[makale] = []
            for word in words:
                results[makale].append(self.wordlocation[word][makale])
        return results, words

    def getscoredlist(self, results, words):
        totalscores = dict([(makale, 0) for makale in results])
        # This is where you'll later put the scoring functions
        # word frequency scoring
        weights = [(1.0, self.pagerankscore(results)), (1.0, self.frequencyscore(results)),
                   (1.0, self.locationscore(results))]
        for (weight, scores) in weights:
            for makale in totalscores:
                totalscores[makale] += weight * scores.get(makale, 0)
        return totalscores

    def query(self, q):
        # işlem başladığındaki zamanı alıyoruz
        baslangic = time.time()
        results, words = self.getmatchingpages(q)
        # aranılan kelime indexte yoksa bilgi verip çıkıyoruz
        if len(results) == 0:
            print('No matching pages found!')
            return
        scores = self.getscoredlist(results, words)
        rankedscores = sorted([(score, makale) for (makale, score) in scores.items()], reverse=True)
        # işlemler bittiğindeki zamanı alıyoruz
        bitis = time.time()
        # arama işleminin ne kadar sürdüğü ve aranan kelimelerin ne kadar makalede bulunduğu bilgisini
        print("\n{} Makale ({:.4f}sn'de) bulundu".format(len(rankedscores), bitis - baslangic))
        i = 1
        # çıktıların istenildiği gibi verilmesi için
        print("\nSIRA NO{}MAKALE BAŞLIĞI{} MAKALE SKORU".format('\t'*2, '\t'*35))
        print("{:<12}{:<153}{}".format('-' * 7, '-' * 148, '-' * 13))
        for (score, makale) in rankedscores:
            print("{:<11}{:<154}{:.4f}".format(i, self.makaleno_makaleadi[makale], score))
            i += 1
            if i == 11 or i == 21 or i == 31 or i == 41:
                input("\n*** Sonraki 10 Sonucu Görmek İçin Enter Tuşuna Basın ***\n")
            if i == 51:
                break

    def normalizescores(self, scores, smallisbetter=0):
        vsmall = 0.00001  # Avoid division by zero errors
        if smallisbetter:
            minscore = min(scores.values())
            minscore = max(minscore, vsmall)
            return dict([(u, float(minscore) / max(vsmall, l)) for (u, l) in scores.items()])
        else:
            maxscore = max(scores.values())
            if maxscore == 0:
                maxscore = vsmall
            return dict([(u, float(c) / maxscore) for (u, c) in scores.items()])

    def frequencyscore(self, results):
        counts = {}
        for makale in results:
            score = 1
            for wordlocations in results[makale]:
                score *= len(wordlocations)
            counts[makale] = score
        return self.normalizescores(counts, smallisbetter=False)

    def fairfrequencyscore(self, results):
        counts = {}
        url_words = {}
        for word in self.wordlocation.keys():
            for url in self.wordlocation[word].keys():
                url_words.setdefault(url, 0)
                url_words[url] += 1
        for url in results:
            score = 1
            for wordlocations in results[url]:
                score *= len(wordlocations)
            counts[url] = score/url_words[url]
        return self.normalizescores(counts, smallisbetter=False)

    def locationscore(self, results):
        locations = dict([(url, 1000000) for url in results])
        for url in results:
            score = 0
            for wordlocations in results[url]:
                score += min(wordlocations)
            locations[url] = score
        return self.normalizescores(locations, smallisbetter=True)

    def worddistancescore(self, result):
        urller = result.keys()
        listoflist = result.values()
        counts = {}
        mesafe = 1000000
        if (len(listoflist)) < 2 or (len(urller)) < 2:
            for url in result:
                counts[url] = 1.0
            return counts
        for url in urller:
            for i in range(len(result[url]) - 1):
                for j in range(len(result[url][i])):
                    for k in range(len(result[url][i + 1])):
                        if mesafe > abs(result[url][i][j] - result[url][i + 1][k]):
                            mesafe = abs(result[url][i][j] - result[url][i + 1][k])
            counts[url] = mesafe
        return self.normalizescores(counts, smallisbetter=1)

    def pagerankscore(self, results):
        pageranks = dict([(url, self.pagerank[url]) for url in results if url in self.pagerank])
        maxrank = max(pageranks.values())
        normalizedscores = dict([(url, float(score)/maxrank) for (url, score) in self.pagerank.items()])
        # return self.normalizescores(self.pageranks)
        return normalizedscores

    def calculatepagerank(self, iterations=20):
        # başta atıf almış tüm makalelerin rank ini 1 eşitleyecek döngü
        for makale in self.citationcounts:
            self.pagerank[makale] = 1.0
        # kullanıcıya yapılacak olan işlem bilgisini veriyoruz
        print("\n*** Rank Hesaplanıyor ***")
        # doğru rank i hesaplamak için istenilen tekrar kadar tekrar edecek olan döngü
        for i in range(iterations):
            # atıf almış tüm makaleleri dönderecek olan döngü
            for makale in self.citationcounts:
                pr = 0.15
                # atıf yapan tüm makaleleri çekiyoruz
                atif_yapan_makaleler = self.citations.get(makale)
                # atıf yapan makaleye de atıf yapılmışsa rank i ona göre değerlendiriyoruz
                for atif_yapan_makale in atif_yapan_makaleler:
                    if atif_yapan_makale in self.citationcounts:
                        linkingpr = self.pagerank[atif_yapan_makale]
                        yapilan_atif_sayisi = self.citationcounts[atif_yapan_makale]
                        pr += 0.85 * (linkingpr / yapilan_atif_sayisi)
                # makalenin rank sonucunu sözlüğüne kaydediyor
                self.pagerank[makale] = pr
        # kullanıcıya yapılan işlemin sonlandığı bilgisini veriyoruz
        print("\n*** Rank Hesaplandı ***")


# t = Tarama()
# t.query("gravity")
# print("sözlük kapatılıyor")
# t.close()


#    ******************************************** YORUM SORUSU *********************************************************
#    mysearchengine, links sözlüğünün value'larını(sayfadan çıkan linklerin) bir sözlükte veya set'te saklanmasındaki
#    amaç; girilen sayfadan bulunan linklerin, tekrar tekrar geçiyor olabileciğini, bununda işlem tekrarlarına neden
#    olacağını öngördüğümüz ve buna engel olmak için, set veya sözlük kullanmamız gerekiyordu. Ancak citations
#    sözlüğünde; bir makale, başka bir makaleye birden fazla atıf yapmayacağından value'ları sözlükte veya set'te
#    tutmamıza gerek yok, her makale için atıf yaptığı makaleleri(value'ları) bir listede tutmamız yeterli olacaktır.
