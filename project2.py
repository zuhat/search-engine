import os
import time
import re
# import shelve


class Tarama:
    def __init__(self):
        ## {makaleno1:'makaleadı1', makaleno2:'makaleadı2'...}
        self.makaleno_makaleadi = {}
        ## wordlocations[herhangi_bir_kelime] = { makaleno1:[loc1, loc2, ...., locN],   makaleno2:[loc1, loc2, ...,locM], ....... } 
        self.wordlocation = {}
        self.citations = {}
        self.citationcounts = {}
        self.pagerank = {}
        self.files = []
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
        # loop taking all paths in the directory
        for r, d, f in os.walk(path):
            for file in f:
                self.files.append(os.path.join(r, file))
        # transaction information
        print("\n*** Makaleler İndexleniyor ***")
        
        for dosya_adi in self.files:
            # get the article number
            makale_no = re.search('\d+', dosya_adi).group()
            
            # percentage completion of the transaction
            if makale_no == "9301084":
                print('\n*** %25 Tamamlandı ***')
            elif makale_no == "9310073":
                print('*** %50 Tamamlandı ***')
            elif makale_no == "9406036":
                print('*** %75 Tamamlandı ***')
                
            # reading file
            icerik = open(dosya_adi, "r").read()
            
            # pull article names
            baslik = re.search("Title:([\s\S]+)Authors?:", icerik).group(1)
            baslik = "".join(baslik.split("\n"))
            
            # creating the dictionary
            self.makaleno_makaleadi[makale_no] = baslik
            
            # capture the abstract part of the article
            ozet_ayiraci = re.compile(r"[^-]\n\\([\s\S]+)\\$")
            ozet = re.search(ozet_ayiraci, icerik).group(1)
            
            # catch the words in the title and summary, we get rid of capital letters
            kelimeler = re.findall('\w+', baslik.lower() + ozet.lower())
            
            # creating the dictionary
            for i in range(len(kelimeler)):
                self.wordlocation.setdefault(kelimeler[i], {})
                self.wordlocation[kelimeler[i]].setdefault(makale_no, [])
                self.wordlocation[kelimeler[i]][makale_no].append(i)
        
        print('\n*** Makaleler İndexlendi ***')
        # reading citations
        veriler = open('citations.txt', "r").read()
        
        # atıf verilerini tuplelar listesine dönüştürüyoruz
        atiflar = re.findall("\n(\d+)\t(\d+)", veriler)
        
        print('\n*** Atıf İndexlemesi Yapılıyor ***')
        
        # loop to process citation data one by one
        for atif_yapan, atif_alan in atiflar:
            ## transaction information
            # if atif_yapan == "9810138":
            #     print('\n*** %25 Tamamlandı ***')
            # elif atif_yapan == "105034":
            #     print('*** %50 Tamamlandı ***')
            # elif atif_yapan == "9911054":
            #     print('*** %75 Tamamlandı ***')
            ## creating the dictionary
            self.citations.setdefault(atif_alan, [])
            self.citations[atif_alan].append(atif_yapan)
            self.citationcounts.setdefault(atif_alan, 0)
            self.citationcounts[atif_alan] += 1
        
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
        # timing
        baslangic = time.time()
        results, words = self.getmatchingpages(q)
        # If the search word is not in the index, we give information and exit
        if len(results) == 0:
            print('No matching pages found!')
            return
        scores = self.getscoredlist(results, words)
        rankedscores = sorted([(score, makale) for (makale, score) in scores.items()], reverse=True)
        # passing time
        bitis = time.time()
        # how long the search took and how many articles the searched words were in
        print("\n{} Makale ({:.4f}sn'de) bulundu".format(len(rankedscores), bitis - baslangic))
        i = 1
        # giving outputs
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
        # loop to equal 1 rank of all articles cited at the beginning
        for makale in self.citationcounts:
            self.pagerank[makale] = 1.0
       
        print("\n*** Rank Hesaplanıyor ***")
        # loop to repeat the desired number of repetitions to calculate the correct rank
        for i in range(iterations):
            # The loop that will return all cited articles
            for makale in self.citationcounts:
                pr = 0.15
                # pull all articles referring to
                atif_yapan_makaleler = self.citations.get(makale)
                # If the article referring is also cited, we evaluate the rank accordingly.
                for atif_yapan_makale in atif_yapan_makaleler:
                    if atif_yapan_makale in self.citationcounts:
                        linkingpr = self.pagerank[atif_yapan_makale]
                        yapilan_atif_sayisi = self.citationcounts[atif_yapan_makale]
                        pr += 0.85 * (linkingpr / yapilan_atif_sayisi)
                # the article's rank result to the dictionary
                self.pagerank[makale] = pr
        
        print("\n*** Rank Hesaplandı ***")

def main():
    t = Tarama()
    t.query("gravity")
    print("sözlük kapatılıyor")
    t.close()
    
if __name__ == '__main__':
    main()
