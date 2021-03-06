import pickle
import os
import numpy as np
from tqdm import tqdm
import sys
sys.path.append('../')

from Preprocessing import Preprocess

from Config import config
from gensim.models.keyedvectors import KeyedVectors
from gensim.models import Doc2Vec
from gensim.models.doc2vec import TaggedDocument


class Embeddings():
    def __init__(self):
        self.scale = 0.1
        self.vec_dim = 300
        self.preprocessor = Preprocess.Preprocess()

    def word2vec(self, word_emb, word, scale, vec_dim, lang):
        unknown_word = np.random.uniform(-scale,scale,vec_dim)
        if lang == 'es':
            if word.endswith('adar'):
                if word[:-1] in word_emb:
                    res = word_emb[word[:-1]]
                    flag = 0
                elif word[:-1]+'do' in word_emb:
                    res = word_emb[word[:-1]+'do']
                    flag = 0
                elif word[:-1]+'ds' in word_emb:
                    res = word_emb[word[:-1]+'ds']
                    flag = 0
                elif word[:-1]+'os' in word_emb:
                    res = word_emb[word[:-1]+'os']
                    flag = 0
                elif word[:-1]+'o' in word_emb:
                    res = word_emb[word[:-1]+'ds']
                    flag = 0
                elif word[:-1]+'s' in word_emb:
                    res = word_emb[word[:-1]+'ds']
                    flag = 0
            else:
                if word in word_emb:
                    res = word_emb[word]
                    flag = 0
                else:
                    res = unknown_word
                    flag = 1
        if lang == 'en':
            if word in word_emb:
                res = word_emb[word]
                flag = 0
            else:
                res = unknown_word
                flag = 1
        return res,flag

    def get_embedding_matrix(self, lang='es'):
        print("Embedding!")

        path = config.cache_prefix_path + lang + "_index2vec.pkl"
        if os.path.exists(path):
            with open(path, 'rb') as pkl:
                return pickle.load(pkl)

        if lang == 'es':
            word_emb = KeyedVectors.load_word2vec_format(config.ES_EMBEDDING_MATRIX, encoding='utf-8')
        elif lang == 'en':
            word_emb = KeyedVectors.load_word2vec_format(config.EN_EMBEDDING_MATRIX, encoding='utf-8')

        word2index = self.preprocessor.es2index(lang)


        vocal_size = len(word2index)
        index2vec = np.ones((vocal_size, self.vec_dim), dtype="float32") * 0.01
        unk_count = 0
        unk_words = []

        for word in tqdm(word2index):
            index = word2index[word]
            if index <= 3:
                continue
            vec, flag = self.word2vec(word_emb, word, self.scale, self.vec_dim, lang)
            index2vec[index] = vec
            if flag == 1:
                unk_count += 1
                unk_words.append(word)

        print("emb vocab size: ", len(word_emb.vocab))
        print("unknown words count: ", unk_count)
        print("index2vec size: ", len(index2vec))

        with open(config.cache_prefix_path + lang +'_unk_words.pkl', 'wb')  as pkl:
            pickle.dump(unk_words, pkl)

        with open(path, 'wb') as pkl:
            pickle.dump(index2vec, pkl)
        return index2vec

    def doc2vec(self):
        print("doc2vec...")
        path = config.cache_prefix_path + 'doc2vec.embedding'
        dic_path = config.cache_prefix_path + 'doc2dic.pkl'

        if os.path.exists(path) and os.path.exists(dic_path):
            model = Doc2Vec.load(path)
            with open(dic_path, 'rb') as pkl:
                dic = pickle.load(pkl)
            return model, dic

        es = self.preprocessor.load_all_replace_data()[0]

        corpus = []
        for i, text in enumerate(es):
            doc = TaggedDocument(words=text, tags=[i])
            corpus.append(doc)

        model = Doc2Vec(vector_size = self.vec_dim,
                        window = 5,
                        min_count = 1,
                        sample = 1e-3,
                        negative = 5,
                        workers = 6)

        model.build_vocab(corpus)
        model.train(corpus, total_examples=model.corpus_count, epochs=20)

        model.save(path)
        with open(dic_path, 'wb') as pkl:
            pickle.dump(corpus, pkl)

        return model, corpus

if __name__ == '__main__':
    embedding = Embeddings()
    # embedding.get_embedding_matrix('en')
    # embedding.get_embedding_matrix('es')
    embedding.doc2vec()

