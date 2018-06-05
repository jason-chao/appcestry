#!/usr/bin/env python3

import os
import argparse
from sklearn.feature_extraction.text import HashingVectorizer
import json
import re
from sklearn.metrics.pairwise import cosine_similarity
import numpy
import subprocess
import time
from pprint import pprint
import itertools
import gc
import random


hashFeatureNumber = 2 ** 16
nGramRange = (16, 16)
tmpDir = os.path.curdir
jsonStopCharRe = re.compile(",|:|,|{|}|\"")


def getAllFilesOfExtension(rootDir, extension):
    fileList = []
    for (dirPath, dirNames, fileNames) in os.walk(rootDir):
        for baseName in fileNames:
            if baseName.endswith(extension):
                fileList.append((dirPath, baseName))
    return fileList


def customTokenizer(input):
    return re.split("\n", input)


def getHashVector(content):
    hashVectorizer = HashingVectorizer(n_features=hashFeatureNumber, tokenizer=customTokenizer,
                                       ngram_range=nGramRange)
    return hashVectorizer.transform([content])


def loadJSONFromFile(filename):
    jsonFile = open(filename, "r")
    theObject = json.load(jsonFile)
    jsonFile.close()
    return theObject


def writeTextToBufferDir(baseFilename, text):
    bufferFilename = os.path.join(tmpDir, baseFilename)
    bufferFile = open(bufferFilename, "w")
    bufferFile.write(text)
    bufferFile.close()
    return bufferFilename


def diffContentPairAsFiles(file1Content, file2Content):
    diffResult = {"ratio": float(0), "intersection": float(0), "union": float(0)}
    try:
        tmpFilename1 = writeTextToBufferDir("_diff_tmp1_{}".format(time.time()), file1Content)
        tmpFilename2 = writeTextToBufferDir("_diff_tmp2_{}".format(time.time()), file2Content)
        diffOuput = subprocess.run("wdiff -s -1 -2 -3 {} {}".format(tmpFilename1, tmpFilename2), check=False,
                                   stdout=subprocess.PIPE, shell=True).stdout.decode("utf-8")
        diffOuput = diffOuput.replace(" word ", " words ").split("\n")
        file1ResultSegments = diffOuput[0].split(" ")
        file2ResultSegments = diffOuput[1].split(" ")
        words = int(file1ResultSegments[file1ResultSegments.index("words") - 1])

        if words > 0:
            common = float(file1ResultSegments[file1ResultSegments.index("common") - 2])
            file1Total = float(file1ResultSegments[file1ResultSegments.index("words") - 1])
            file2Total = float(file2ResultSegments[file2ResultSegments.index("words") - 1])
            diffResult["union"] = (file1Total + file2Total - common)
            diffResult["intersection"] = common
            diffResult["ratio"] = float(diffResult["intersection"]) / float(diffResult["union"])

        os.remove(tmpFilename1)
        os.remove(tmpFilename2)

    except:
        print("pair diff failed - {} {}".format(tmpFilename1, tmpFilename2))

    gc.collect(2)
    return diffResult


def diffMarkupPairs(content1, content2):
    pairResult = {"byAttributeValuePair": None, "byValue": None}
    content1 = jsonStopCharRe.sub("", content1)
    content2 = jsonStopCharRe.sub("", content2)

    if not ((not content1) and (not content2)):
        pairResult["byAttributeValuePair"] = diffContentPairAsFiles(content1.replace(" ", "_").replace("\n", " "),
                                                                    content2.replace(" ", "_").replace("\n", " "))
        pairResult["byValue"] = diffContentPairAsFiles(content1.replace("\n", " "),
                                                       content2.replace("\n", " "))
    return pairResult


def getJaccardSimilarity(arr1, arr2):
    jaccardSimResult = {"ratio": float(0),
                        "intersection": float(len(numpy.intersect1d(arr1, arr2, assume_unique=True))),
                        "union": float(len(numpy.union1d(arr1, arr2)))}
    if jaccardSimResult["union"] > float(0):
        jaccardSimResult["ratio"] = jaccardSimResult["intersection"] / jaccardSimResult["union"]
    return jaccardSimResult


def compareGenes(gene1, gene2):
    result = {"smali": {}, "namespace": {}, "markup": {}, "media": {}, "permission": {}}

    try:

        print("Comparing vectorised code ...")
        result["smali"]["cosineSimilarity"] = cosine_similarity(gene1["features"]["smaliVector"],
                                                                gene2["features"]["smaliVector"]).item(0)

        print("Comparing disassembled code ...")
        result["smali"]["byLine"] = diffContentPairAsFiles(gene1["smali"].replace(" ", "_"),
                                                           gene2["smali"].replace(" ", "_"))

        result["smali"]["1-gram"] = diffContentPairAsFiles(gene1["smali"].replace("\n", " "),
                                                           gene2["smali"].replace("\n", " "))

        print("Comparing name spaces ...")
        result["namespace"] = getJaccardSimilarity(gene1["namespace"], gene2["namespace"])

        print("Comparing markup files ...")
        result["markup"]["names"] = getJaccardSimilarity(gene1["markup"]["names"], gene2["markup"]["names"])
        result["markup"]["values"] = getJaccardSimilarity(gene1["markup"]["values"], gene2["markup"]["values"])

        print("Comparing media files ...")
        result["media"]["exactDuplicates"] = getJaccardSimilarity(gene1["features"]["media_sha256"],
                                                                    gene2["features"]["media_sha256"])

        result["media"]["nearDuplicates"] = getJaccardSimilarity(gene1["features"]["media_phash"],
                                                                   gene2["features"]["media_phash"])

        print("Comparing permissions and features ...")
        result["permission"] = {
            "android": getJaccardSimilarity([pf for pf in gene1["permission-feature"] if pf.startswith("android.")],
                                            [pf for pf in gene2["permission-feature"] if pf.startswith("android.")]),
            "non-android": getJaccardSimilarity(
                [pf for pf in gene1["permission-feature"] if not pf.startswith("android.")],
                [pf for pf in gene2["permission-feature"] if not pf.startswith("android.")])}

    except:
        print("Feature comparison failed")

    return result


def computeFeatures(geneObject):

    geneObject["features"] = {}
    geneObject["features"]["smaliVector"] = getHashVector(geneObject["smali"])
    geneObject["features"]["media_phash"] = list(geneObject["media"]["phash"].keys())
    geneObject["features"]["media_sha256"] = list(geneObject["media"]["sha256"].keys())

    return geneObject


def dumpObjectAsJson(obj, filename):
    outputFileHandler = open(filename, "w")
    json.dump(obj, outputFileHandler, indent=4, ensure_ascii=False, sort_keys=True)
    outputFileHandler.close()


def comparePair(geneFilename1, geneFilename2):
    result = None
    print("About to process {} and {}".format(geneFilename1, geneFilename2))
    try:
        gene1 = loadJSONFromFile(geneFilename1)
        gene1 = computeFeatures(gene1)
        gene2 = loadJSONFromFile(geneFilename2)
        gene2 = computeFeatures(gene2)
        print("Comparing {} to {}".format(gene1["appID"], gene2["appID"]))
        result = compareGenes(gene1, gene2)
        result["pair"] = [gene1["appID"], gene2["appID"]]
    except:
        print("Comparison failed")
    gc.collect()
    return result


def compareAppGenesInDir(geneFileList, shuffle):
    result = []
    pairList = list(itertools.combinations(geneFileList, 2))
    if shuffle:
        random.shuffle(pairList)
    for genePair in pairList:
        pairResult = comparePair(genePair[0], genePair[1])
        if pairResult is not None:
            result.append(pairResult)
            dumpObjectAsJson(pairResult, os.path.join(tmpDir, "_tmp_pair_result_{}".format(time.time())))
        else:
            print("Failed to compare pair {} {}".format(genePair[0], genePair[1]))
    return result


if __name__ == '__main__':
    argParser = argparse.ArgumentParser()
    argParser.add_argument("--mode", choices=["single-pair", "all-pairs"], help="Mode of comparison", required=True)
    argParser.add_argument("--appgene1", help="AppGene file 1 in single-pair mode")
    argParser.add_argument("--appgene2", help="AppGene file 2 in single-pair mode")
    argParser.add_argument("--geneDir", help="Directory containing AppGene files in all-pairs mode")
    argParser.add_argument("--bufferDir", help="Directory for temporary files",
                           default=os.getenv("COMPARE_TEMP_DIR", os.path.curdir))
    argParser.add_argument("--shuffle", help="Shuffle the order of AppGene pairs (applicable to all-pairs mode only)",
                           action="store_true")
    argParser.add_argument("--outputFile", help="Result file to be saved", required=True)

    args = argParser.parse_args()

    tmpDir = os.path.realpath(args.bufferDir)

    outputResult = {}

    if args.mode == "single-pair":
        outputResult = comparePair(os.path.realpath(args.appgene1), os.path.realpath(args.appgene2))
    elif args.mode == "all-pairs":
        geneRootDir = os.path.realpath(args.geneDir)
        allAppGeneFiles = list(
            os.path.join(geneFile[0], geneFile[1]) for geneFile in getAllFilesOfExtension(geneRootDir, ".appgene"))
        outputResult = compareAppGenesInDir(allAppGeneFiles, args.shuffle)

    pprint(outputResult)

    dumpObjectAsJson(outputResult, args.outputFile)
