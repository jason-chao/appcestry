#!/usr/bin/env python3


import argparse
import os
import logging
import json
from xml.etree import ElementTree as ET
import gc


def getAllFilesOfExtension(rootDir, extension):
    fileList = []
    for (dirPath, dirNames, fileNames) in os.walk(rootDir):
        for filename in fileNames:
            if filename.endswith(extension):
                fileList.append((dirPath, filename))
    return fileList


def readFile(fullPathToFile):
    fileHandler = open(fullPathToFile, "r")
    content = fileHandler.read()
    fileHandler.close()
    return content


def extractValuePairs(rootDir):
    attributeName = []
    attributeValue = []
    allMarkupFiles = getAllFilesOfExtension(rootDir, ".xml")
    for mlFile in allMarkupFiles:
        try:
            doc = ET.parse(os.path.join(mlFile[0], mlFile[1]))
            for node in doc.getiterator():
                if node.tag:
                    attributeName.append(node.tag)
                if node.text:
                    trimmedText = node.text.strip().replace("\n", " ")
                    if trimmedText:
                        attributeValue.append(trimmedText)
                for attribKey in node.attrib.keys():
                    attributeName.append(attribKey)
                    if node.attrib[attribKey]:
                        attributeValue.append(node.attrib[attribKey])
            attributeName = list(set(attributeName))
            attributeValue = list(set(attributeValue))
        except:
            continue
        finally:
            gc.collect()
    return {
        "names": sorted(attributeName), "values": sorted(attributeValue)
    }


if __name__ == '__main__':
    argParser = argparse.ArgumentParser()
    argParser.add_argument("--apkDir", help="Root Directory of an APK extracted using APKTOOL", required=True)
    argParser.add_argument("--outputFile", help="The output file to be saved", type=argparse.FileType("w"), required=True)

    args = argParser.parse_args()
    apkRootDir = os.path.realpath(args.apkDir)

    exportDict = {}
    exportDict = extractValuePairs(apkRootDir)

    if len(exportDict) > 0:
        json.dump(exportDict, args.outputFile, sort_keys=True, indent=-1, separators=(" , ", " : "),
                  ensure_ascii=False)
        logging.info("Merged {} files".format(len(exportDict.keys())))
    else:
        logging.info("No admissible files are found")
