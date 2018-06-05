#!/usr/bin/env python3


import argparse
import os
import xml.etree.ElementTree as ET
import json


valuePrefixToBeKept = ["android.", "com.google"]
keyOfValuePrefixToBeKept = ["package"]
nodesToBeDropped = ["data", "meta-data"]
smaliSizeLimitInBytes = 1024 * 1024 * 5


def getAllFiles(rootDir):
    fileList = []
    for (dirPath, dirNames, fileNames) in os.walk(rootDir):
        for filename in fileNames:
            fileList.append(os.path.join(dirPath, filename))
    return fileList


def isToKeepValuePrefix(attributeValue, key):
    for prefix in valuePrefixToBeKept:
        if attributeValue.startswith(prefix) or key in keyOfValuePrefixToBeKept:
            return True
    return False


def filterAttributes(nodeAttributes):
    filteredAttributes = {}
    for key in nodeAttributes.keys():
        newKey = key.replace("{http://schemas.android.com/apk/res/android}", "")
        if not isToKeepValuePrefix(nodeAttributes[key], key):
            filteredAttributes[newKey] = nodeAttributes[key].split(".")[-1]
        else:
            filteredAttributes[newKey] = nodeAttributes[key]
    return filteredAttributes


def readPackageNameFromManifest(filename):
    xmlTree = ET.parse(filename)
    xmlRoot = xmlTree.getroot()
    return xmlRoot.attrib["package"]


def getNameSpace(fullSmaliFilename, smaliDirs):
    for smaliDir in sorted(smaliDirs, reverse=True):
        if smaliDir in fullSmaliFilename:
            nsPath = os.path.relpath(os.path.dirname(fullSmaliFilename), smaliDir)
            return nsPath.replace("/", ".")


def mergeFiles(smaliDirs, packageName, fileToBeMerged, fileForNamespace, includeAllCodes):
    allCodeFiles = []
    packageNameSegments = packageName.split(".")

    for smaliDir in smaliDirs:
        allCodeFiles.extend(getAllFiles(smaliDir))

    namespaceList = [getNameSpace(sf, smaliDirs) for sf in allCodeFiles]
    namespaceList = list(set(namespaceList))

    nsFile = open(fileForNamespace, "w")
    json.dump(namespaceList, nsFile)
    nsFile.close()

    closestNamespace = ""

    for i in range(len(packageNameSegments) + 1, 0, -1):
        namespace = ".".join(packageNameSegments[:i])
        if namespace in namespaceList:
            closestNamespace = namespace
            break

    if not includeAllCodes:
        allCodeFiles = [cf for cf in allCodeFiles if closestNamespace in getNameSpace(cf, smaliDirs)]

    smaliFilesByFileSize = sorted([f for f in allCodeFiles
                                   if os.path.isfile(f) and f.endswith(".smali")],
                                  key=lambda f: os.path.getsize(f), reverse=True)  # smali files sort by file sizes

    cumulatedSize = 0
    maxFileIndex = None
    for i in range(len(smaliFilesByFileSize)):
        cumulatedSize = cumulatedSize + os.path.getsize(smaliFilesByFileSize[i])
        if cumulatedSize > smaliSizeLimitInBytes:
            maxFileIndex = i
            break

    if maxFileIndex is not None:
        smaliFilesByFileSize = [sf for sf in smaliFilesByFileSize[0:(maxFileIndex+1)]]

    destinationFile = open(fileToBeMerged, "w")
    for smaliFile in smaliFilesByFileSize:
        # print("{}\t{}".format(os.path.getsize(smaliFile), smaliFile))  # to verify the order by file size
        sourceFile = open(smaliFile, "r")
        for line in sourceFile:
            if (not line.startswith("#")) and (not line == "\n"):
                destinationFile.write(line)
        sourceFile.close()
    destinationFile.close()


def MergeSmaliFilesIntoOne(apkRootDir, outputSmaliFilename, outputNSFilename, allCode):
    manifestFilename = os.path.join(apkRootDir, "AndroidManifest.xml")
    smaliDirs = [os.path.join(os.path.join(apkRootDir, "smali"))]
    for i in range(2, 1024):
        nextDir = os.path.join(os.path.join(apkRootDir, "smali_classes{}".format(i)))
        if os.path.exists(nextDir) and os.path.isdir(nextDir):
            smaliDirs.append(nextDir)
        else:
            break
    if os.path.exists(manifestFilename) and os.path.exists(smaliDirs[0]):
        packageName = readPackageNameFromManifest(manifestFilename)
        mergeFiles(smaliDirs, packageName, outputSmaliFilename, outputNSFilename, allCode)
    else:
        print("Not an apk root directory: {}".format(apkRootDir))


if __name__ == '__main__':
    argParser = argparse.ArgumentParser()
    argParser.add_argument("--apkDir", help="Root Directory of an APK extracted using APKTOOL", required=True)
    argParser.add_argument("--outputSmaliFile", help="The output smali file to be saved", required=True)
    argParser.add_argument("--outputNameSpaceFile", help="The output namespace file to be saved", required=True)
    argParser.add_argument("--allCode",
                           help="Include code beyond the name space of the app ID", action="store_true")
    args = argParser.parse_args()

    MergeSmaliFilesIntoOne(os.path.realpath(args.apkDir), os.path.realpath(args.outputSmaliFile),
                           os.path.realpath(args.outputNameSpaceFile), args.allCode)
