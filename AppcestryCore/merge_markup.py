#!/usr/bin/env python3

# This script extracts the attribute names and values from markup (XML) files and merges them into a single file.

import argparse
import os
import logging
import json
from xml.etree import ElementTree as ET
import gc


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
        for filename in fileNames:
            if filename.endswith(extension):
                fileList.append((dirPath, filename))
    return fileList


def readFile(fullPathToFile):
    """A generic function to read the content of a file.
       Args:
         fullPathToFile: The full filename for the file
       Return:
         The content
    """
    fileHandler = open(fullPathToFile, "r")
    content = fileHandler.read()
    fileHandler.close()
    return content


def extractValuePairs(rootDir):
    """Traverse a directory tree and find all XML files.  Extract the attribute names and values from these files.
       Args:
         rootDir: The directory
       Returns:
         An object with two properties:
           names: Sorted list of attribute names 
           values: Sorted list of attribute values
    """
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
    # The usage of arguemnts is self-explanatory as follows
    argParser = argparse.ArgumentParser()
    argParser.add_argument("--apkDir", help="Root Directory of an APK extracted using APKTOOL", required=True)
    argParser.add_argument("--outputFile", help="The output file to be saved", type=argparse.FileType("w"),
                           required=True)

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
