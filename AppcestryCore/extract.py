#!/usr/bin/env python3


import os
import sys
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.externals import joblib
import re
import json

hashFeatureNumber = 2 ** 16
nGramRange = (16, 16)

def customTokenizer(input):
    return re.split("\n", input)


def getHashVector(filename):
    hashVectorizer = HashingVectorizer(input="filename", n_features=hashFeatureNumber, tokenizer=customTokenizer,
                                       ngram_range=nGramRange)
    return hashVectorizer.transform(filename)


def MakeVectorisedSmaliFile(smaliFilename, outlsputFilename):
    if os.path.isfile(smaliFilename):
        v = getHashVector([smaliFilename])
        joblib.dump(v, outputFilename)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: [transformedSmaliFile] [vectorisedSmaliFile]")
    else:
        MakeVectorisedSmaliFile(os.path.realpath(sys.argv[1]), os.path.realpath(sys.argv[2]))
