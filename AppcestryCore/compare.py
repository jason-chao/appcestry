#!/usr/bin/env python3

# This script compares AppGene files for similiarty
# Run this script in terminal / command line to see the usage of arguments.

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
import hashlib

hashFeatureNumber = 2 ** 16
nGramRange = (16, 16)
tmpDir = os.path.curdir
jsonStopCharRe = re.compile(",|:|,|{|}|\"")


def getAllFilesOfExtension(rootDir, extension):
    """Traverse a directory tree and find all the files with a specified extension
       Args:
         rootDir: The directory to traverse
         extension: The extension
       Returns:
         A list of files
    """
    fileList = []
    for (dirPath, dirNames, fileNames) in os.walk(rootDir):
        for baseName in fileNames:
            if baseName.endswith(extension):
                fileList.append((dirPath, baseName))
    return fileList


def customTokenizer(input):
    """Tokenise transformed Smali instructions.
       Args:
         input: Lines of transformed instructions
       Returns:
         An array of transformed instructions
    """
    return re.split("\n", input)


def getHashVector(content):
    """Get hash vector of transformed Smali instructions.
       Args:
         input: Lines of transformed instructions
       Returns:
         Hash vector
    """    
    hashVectorizer = HashingVectorizer(n_features=hashFeatureNumber, tokenizer=customTokenizer,
                                       ngram_range=nGramRange)
    return hashVectorizer.transform([content])


def loadJSONFromFile(filename):
    """A generic function to read a JSON file.
       Args:
         filename: The full filename for the JSON file
       Returns:
         The object loaded from JSON
    """
    jsonFile = open(filename, "r")
    theObject = json.load(jsonFile)
    jsonFile.close()
    return theObject


def writeTextToBufferDir(baseFilename, text):
    """Write text to a file in the buffer directory.
       Args:
         baseFilename: Base filename of the target file
         text: The text to be written to the file
       Returns:
         Full filename of the target file
    """
    bufferFilename = os.path.join(tmpDir, baseFilename)
    bufferFile = open(bufferFilename, "w")
    bufferFile.write(text)
    bufferFile.close()
    return bufferFilename


def getTextSHA256(plaintext):
    """Get the SHA256 hash value of plaintext.
       Args:
         plaintext: The plaintext
       Returns:
         Hash value represneted in Hex string
    """    
    textHash = hashlib.sha256(plaintext)
    return "%s" % textHash.hexdigest()


def getHashInArray(arr):
    """Get the SHA256 hash values of elements in an array.
       Args:
         arr: The array
       Returns:
         An array of hash values (represneted in Hex string)
    """      
    return [getTextSHA256(t.encode("utf-8")) for t in arr]


def diffContentPairAsFiles(file1Content, file2Content):
    """Use the operating system's wdiff utility to compare two files.
       Args:
         file1Content: Content of the first file
         file2Content: Content of the second file
       Returns:
         Result object with properties: union, intersection and ratio
    """    
    diffResult = {"ratio": float(0), "intersection": float(0), "union": float(0)}
    try:
        tmpFilename1 = writeTextToBufferDir("_diff_tmp1_{}".format(time.time()), file1Content)
        tmpFilename2 = writeTextToBufferDir("_diff_tmp2_{}".format(time.time()), file2Content)
        diffOuput = subprocess.run("wdiff -s -1 -2 -3 {} {}".format(tmpFilename1, tmpFilename2), check=False,
                                   stdout=subprocess.PIPE, shell=True).stdout.decode("utf-8")
        
        # Parse the output of wdiff
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
    """Compare two markup (XML) files by their common attribute-value pairs and common values.
       Args:
         content1: Extracted attribute-value pairs
         content2: Extracted values
       Returns:
         Result object with properties: byAttributeValuePair and byValue (both of the same structure as the output from diffContentPairAsFiles)
    """      
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
    """Get the Jaccard similarity of two arrays
       Args:
         arr1: The first array
         arr1: The second array
       Returns:
         Result object with properties: union, intersection and ratio
    """     
    jaccardSimResult = {"ratio": float(0),
                        "intersection": float(len(numpy.intersect1d(arr1, arr2, assume_unique=True))),
                        "union": float(len(numpy.union1d(arr1, arr2)))}
    if jaccardSimResult["union"] > float(0):
        jaccardSimResult["ratio"] = jaccardSimResult["intersection"] / jaccardSimResult["union"]
    return jaccardSimResult


def getEmptyJaccardResult():
    """Get as empty Jaccard similarity result object.
       Returns:
         Result object with properties: union, intersection and ratio (all values are 0)
    """    
    return {"ratio": 0, "intersection": 0, "union": 0}


def compareGenes(gene1, gene2):
    """Compare a pair of AppGene objects
       Args:
         gene1: The first AppGene object
         gene2: The second AppGene object
       Returns: 
         Result object with properties:
           smali:
             cosineSimilarity: The cosine similarity of the hash vectors of AppGene pairs
             byLine: The union, intersection and ratio (Jaccard Similarity) of transformed Smali instructions by line
             1-gram: The union, intersection and ratio (Jaccard Similarity) of transformed Smali instructions by opcode and argument
           namespace: The union, intersection and ratio (Jaccard Similarity) of namespaces (code package names in full)
           markup: 
             names: The union, intersection and ratio (Jaccard Similarity) of attribute names in markup (XML) files
             values: The union, intersection and ratio (Jaccard Similarity) of attribute values in markup (XML) files
           media:
             exactDuplicates: The union, intersection and ratio (Jaccard Similarity) of pHash (perceptual hash) values of image files
             nearDuplicates: The union, intersection and ratio (Jaccard Similarity) of SHA256 values of all other resource files
           permission:
             android: The union, intersection and ratio (Jaccard Similarity) of Android permissions
             non-android: The union, intersection and ratio (Jaccard Similarity) of custom permissions
    """  

    result = {"smali": {}, "namespace": {}, "markup": {}, "media": {}, "permission": {}}

    try:
        print("Comparing vectorised code ...")
        result["smali"]["cosineSimilarity"] = cosine_similarity(gene1["features"]["smaliVector"],
                                                                gene2["features"]["smaliVector"]).item(0)
    except:
        print("Failed to compare vectorised code")
        result["smali"]["cosineSimilarity"] = 0

    try:
        print("Comparing disassembled code ...")
        result["smali"]["byLine"] = diffContentPairAsFiles(gene1["smali"].replace(" ", "_"),
                                                           gene2["smali"].replace(" ", "_"))

        result["smali"]["1-gram"] = diffContentPairAsFiles(gene1["smali"].replace("\n", " "),
                                                           gene2["smali"].replace("\n", " "))
    except:
        print("Failed to compare disassembled code")
        result["smali"]["byLine"] = getEmptyJaccardResult()
        result["smali"]["1-gram"] = getEmptyJaccardResult()

    try:
        print("Comparing permissions ...")
        result["permission"] = {
            "android": getJaccardSimilarity([pf for pf in gene1["permission-feature"] if pf.startswith("android.")],
                                            [pf for pf in gene2["permission-feature"] if pf.startswith("android.")]),
            "non-android": getJaccardSimilarity(
                [pf for pf in gene1["permission-feature"] if not pf.startswith("android.")],
                [pf for pf in gene2["permission-feature"] if not pf.startswith("android.")])}
    except:
        print("Failed to compare permissions")
        result["permission"]["android"] = getEmptyJaccardResult()
        result["permission"]["non-android"] = getEmptyJaccardResult()

    try:
        print("Comparing namespaces ...")
        result["namespace"] = getJaccardSimilarity(gene1["namespace"], gene2["namespace"])
    except:
        print("Failed to compare namespaces")
        result["namespace"] = getEmptyJaccardResult()

    try:
        print("Comparing media files ...")
        result["media"]["exactDuplicates"] = getJaccardSimilarity(gene1["features"]["media_sha256"],
                                                                  gene2["features"]["media_sha256"])

        result["media"]["nearDuplicates"] = getJaccardSimilarity(gene1["features"]["media_phash"],
                                                                 gene2["features"]["media_phash"])
    except:
        print("Failed to media files")
        result["media"]["exactDuplicates"] = getEmptyJaccardResult()
        result["media"]["nearDuplicates"] = getEmptyJaccardResult()

    try:
        print("Comparing markup files ...")
        result["markup"]["names"] = getJaccardSimilarity(getHashInArray(gene1["markup"]["names"]),
                                                         getHashInArray(gene2["markup"]["names"]))
        result["markup"]["values"] = getJaccardSimilarity(getHashInArray(gene1["markup"]["values"]),
                                                          getHashInArray(gene2["markup"]["values"]))
    except:
        print("Failed to markup files")
        result["markup"]["names"] = getEmptyJaccardResult()
        result["markup"]["values"] = getEmptyJaccardResult()

    return result


def computeFeatures(geneObject):
    """Vectorise and Smali code and hash the resource files.
       Args:
         geneObject: AppGene object
       Returns:
         The AppGene object with a new property "features" with properties:
           smaliVector: The hash vector of transformed Smali code
           media_phash: List of pHash (perceptual hash) values of image files 
           media_sha256: List of SHA256 values of all other resource files
    """
    geneObject["features"] = {}
    geneObject["features"]["smaliVector"] = getHashVector(geneObject["smali"])
    geneObject["features"]["media_phash"] = list(geneObject["media"]["phash"].keys())
    geneObject["features"]["media_sha256"] = list(geneObject["media"]["sha256"].keys())

    return geneObject


def dumpObjectAsJson(obj, filename):
    """Write/dump an object to a JSON file.
       Args:
         obj: The object to be dumped
         filename: The full filename of the target file
       Returns:
         None
    """
    outputFileHandler = open(filename, "w")
    json.dump(obj, outputFileHandler, indent=4, ensure_ascii=False, sort_keys=True)
    outputFileHandler.close()


def comparePair(geneFilename1, geneFilename2):
    """Load two AppGenes from JSON files and pass them to the compareGenes function.
       Args:
         geneFilename1: The object to be dumped
         geneFilename2: The full filename for the target file
       Returns:
         The same result object as the compareGenes function, supplemented by a new property "pair": an array containing the ids and version codes of the two AppGenes (see the code below for the structure).
    """
    result = None
    print("About to process {} and {}".format(geneFilename1, geneFilename2))
    try:
        gene1 = loadJSONFromFile(geneFilename1)
        gene1 = computeFeatures(gene1)
        gene2 = loadJSONFromFile(geneFilename2)
        gene2 = computeFeatures(gene2)
        print("Comparing {} to {}".format(gene1["appID"], gene2["appID"]))
        result = compareGenes(gene1, gene2)
        result["pair"] = []
        result["pair"].extend([{"id": gene1["appID"],
                                "version": gene1["appVersion"]},
                               {"id": gene2["appID"],
                                "version": gene2["appVersion"]}])
    except:
        print("Comparison failed")
    gc.collect()
    return result


def compareAppGenesInDir(geneFileList, shuffle):
    """Generate all combinations of AppGene pairs of AppGene files on a list and then compare them.
       Args:
         geneFileList: List of full filenames for AppGene files
         shuffle: (bool) Whether the combinations are shuffled
       Returns:
         A list of results of compared pairs. (See comparePair and compareGenes functions for the strucutre of the results object for each pair.)
    """    
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
    # The usage of arguemnts is self-explanatory as follows
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
