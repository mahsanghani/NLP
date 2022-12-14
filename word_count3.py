# -*- coding: utf-8 -*-
"""word_count3.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1V4p7JhO-i1wg6Lsaf_QC-zdREDTxzzru
"""

!pip install pyspark

from pyspark import SparkConf, SparkContext

conf = SparkConf().setMaster("local").setAppName("word-counts")
sc = SparkContext(conf=conf)

book = sc.textFile("/content/millions_from_waste.txt")
book.collect()[:10]

word_counts = book.flatMap(lambda x: x.split()).countByValue()

for i, (word, count) in enumerate(word_counts.items()):
    if i == 15: break
    print(word, count)

import re


def preprocess_word(word: str):
    return re.sub("[^A-Za-z0-9]+", "", word.lower())

def preprocess_words(words: str):
    return [preprocess_word(word) for word in words.split()]
    
    
preprocess_words("The Project Gutenberg eBook of Millions from Waste, by Frederick A.")

book = sc.textFile("/content/millions_from_waste.txt")

word_counts = book.flatMap(preprocess_words).countByValue()
for i, (word, count) in enumerate(word_counts.items()):
    if i == 15: break
    print(word, count)

book = sc.textFile("/content/millions_from_waste.txt")

words = book.flatMap(preprocess_words)
word_counts = words.map(lambda x: (x, 1)).reduceByKey(lambda x, y: x + y)
word_counts.collect()[:10]

word_counts_sorted = word_counts.map(lambda x: (x[1], x[0]))
word_counts_sorted.collect()[:10]

word_counts_sorted = word_counts.map(lambda x: (x[1], x[0])).sortByKey()
word_counts_sorted.collect()[:10]

word_counts_sorted = word_counts.map(lambda x: (x[1], x[0])).sortByKey(False)
word_counts_sorted.collect()[:10]

!pip install nltk

import nltk
nltk.download("stopwords")

from nltk.corpus import stopwords

stop_words = stopwords.words("english")
stop_words[:10]

def preprocess_word(word: str):
    return re.sub("[^A-Za-z0-9]+", "", word.lower())

def preprocess_words(words: str):
    preprocessed = [preprocess_word(word) for word in words.split()]
    return [word for word in preprocessed if word not in stop_words and word != ""]
    

preprocess_words("The Project Gutenberg eBook of Millions from Waste, by Frederick A.")

book = sc.textFile("/content/millions_from_waste.txt")

words = book.flatMap(preprocess_words)
word_counts = words.map(lambda x: (x, 1)).reduceByKey(lambda x, y: x + y)
word_counts_sorted = word_counts.map(lambda x: (x[1], x[0])).sortByKey(False)
word_counts_sorted.collect()[:10]

