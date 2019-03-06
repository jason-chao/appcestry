#!/usr/bin/env python3

# This script reads result JSON files and rank pairs by similarity.

import json
import os
import argparse


def getAllFiles(rootDir):
    """Traverse a directory tree and find all the files.
       Args:
         rootDir: The directory to traverse
       Returns:
         A list of full filenames for the files
    """
    fileList = []
    for (dirPath, dirNames, fileNames) in os.walk(rootDir):
        for filename in fileNames:
            fileList.append((dirPath, filename))
    return fileList


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
    theObject["filename"] = os.path.basename(filename)
    return theObject


def getScore(individualResult):
    """Read a result object and then return a score.  The following weights are experimental.
       Args:
         individualResult: AppGene comparison result object
       Returns:
         A score
    """
    score = 0
    score = score + individualResult["smali"]["cosineSimilarity"] * float(0.15)
    score = score + individualResult["namespace"]["ratio"] * float(0.15)

    score = score + individualResult["smali"]["byLine"]["ratio"] * float(0.05)
    score = score + individualResult["smali"]["1-gram"]["ratio"] * float(0.05)

    if individualResult["media"]:
        if "exactDuplicates" in individualResult["media"].keys():
            score = score + individualResult["media"]["exactDuplicates"]["ratio"] * float(0.2)
        if "nearDuplicates"in individualResult["media"].keys():
            score = score + individualResult["media"]["nearDuplicates"]["ratio"] * float(0.1)

    if individualResult["permission"]:
        if "android" in individualResult["permission"].keys():
            score = score + individualResult["permission"]["android"]["ratio"] * float(0.1)
        if "non-android" in individualResult["permission"].keys():
            score = score + individualResult["permission"]["non-android"]["ratio"] * float(0.05)

    if individualResult["markup"]:
        if "names" in individualResult["markup"].keys():
            score = score + individualResult["markup"]["names"]["ratio"] * float(0.05)
        if "values" in individualResult["markup"].keys() is not None:
            score = score + individualResult["markup"]["values"]["ratio"] * float(0.1)

    return score


def rankedReslts(resultList):
    """Rank result objects by socre.
       Args:
         resultList: A list of result objects
       Returns:
         A list of result objects sorted by scores
    """
    for i in range(len(resultList)):
        resultList[i]["score"] = getScore(resultList[i])
    return sorted(resultList, key=lambda r: r["score"], reverse=True)


def listTopResults(resultList):
    """Print the ranked results.
       Args:
         resultList: A list of result objects
       Returns:
         None
    """
    ranked = rankedReslts(resultList)
    for r in ranked:
        print("Score: {} (smali: {}, namespace: {}) for {} - {} in {}".format(r["score"],
                                                                              r["smali"]["cosineSimilarity"],
                                                                              r["namespace"]["ratio"], r["pair"][0],
                                                                              r["pair"][1], r["filename"]))


if __name__ == '__main__':
    argParser = argparse.ArgumentParser()
    argParser.add_argument("--resultDir", help="A directory containing result files")
    argParser.add_argument("--resultListFile", help="File of a list of results")
    argParser.add_argument("--resultFile", help="Individual result file")

    args = argParser.parse_args()

    resultList = None

    if args.resultDir:
        dirFullPath = os.path.realpath(args.resultDir)
        if os.path.isdir(dirFullPath):
            filesTuples = getAllFiles(dirFullPath)
            resultList = [loadJSONFromFile(os.path.join(ft[0], ft[1])) for ft in filesTuples]
    elif args.resultListFile:
        if os.path.isfile(args.resultListFile):
            resultList = loadJSONFromFile(args.resultListFile)
    elif args.resultFile:
        if os.path.isfile(args.resultFile):
            resultList = [loadJSONFromFile(args.resultFile)]

    if resultList is not None:
        listTopResults(resultList)
