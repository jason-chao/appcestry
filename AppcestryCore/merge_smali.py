#!/usr/bin/env python3

# This script merges Smali code files into a single file.

import argparse
import os
import xml.etree.ElementTree as ET
import json


smaliSizeLimitInBytes = 1024 * 1024 * 5


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
            fileList.append(os.path.join(dirPath, filename))
    return fileList


def readPackageNameFromManifest(filename):
    """Read the application ID from AndroidManifest.xml.
       Args:
         filename: Full filename of the AndroidManifest.xml
       Returns:
         The application ID
    """
    xmlTree = ET.parse(filename)
    xmlRoot = xmlTree.getroot()
    return xmlRoot.attrib["package"]


def getCleanNamespace(namespace):
    """Clean the namespace that is inferred from a directory structure.
       Args:
         namesapce: the namespace
       Returns:
         Clean namespace
    """
    nslevels = namespace.split(".")
    finalLevel = len(nslevels)
    for i in range(len(nslevels) - 1, -1, -1):
        if len(nslevels[i]) > 1:
            finalLevel = i
            break
    return ".".join(nslevels[:(finalLevel + 1)])


def getNamespace(fullSmaliFilename, smaliDirs):
    """Get the namespace of a Smali code file.  apktool extracts Smali code files into a directory strucutre named using namespaces.
       Reading a namespace means reading the names of nested directories.
       Args:
         fullSmaliFilename: Full filename of Smali code file
         smaliDirs: List of directories containing Smali code
       Returns:
         The matching namespace
    """
    for smaliDir in sorted(smaliDirs, reverse=True):
        if smaliDir in fullSmaliFilename:
            nsPath = os.path.relpath(os.path.dirname(fullSmaliFilename), smaliDir)
            return getCleanNamespace(nsPath.replace("/", "."))


def mergeFiles(smaliDirs, packageName, fileToBeMerged, fileForNamespace, includeAllCodes):
    """The main flow to merge Smali code files into a single file.
       Args:
         smaliDirs: The directory in which the contents of an APK are extracted to
         packageName: The application ID read from the Manifest file
         fileToBeMerged: Full filename for a target file of merged Smali code
         fileForNamespace: Full filename for a target file containing a list of namespaces
         includeAllCodes: Whether ALL Smali code files are merged
                          (The purpose of AppGene extraction is to study Apps' similarity.
                          Keeping top 5 MBs of aggregated Smali code files, sorted in descending order by size, should be sufficient.
                          So, by default, the not all codes files are included.)
    """

    # For the format of the application ID, see https://developer.android.com/studio/build/application-id
    # The application ID matches with Java package name.
    # The Smali code files (classes) in the namespace of application ID are more likely the code written by the app's developer.
    # For the purpose of studying apps' similarity, Appcestry give top priority to the classes (as represented in individual Smali files) in the namespace as close as possible to the application ID.
    # For more details, see page 21 of http://dx.doi.org/10.13140/RG.2.2.12499.02081

    allCodeFiles = []
    packageNameSegments = packageName.split(".")

    for smaliDir in smaliDirs:
        allCodeFiles.extend(getAllFiles(smaliDir))

    namespaceList = [getNamespace(sf, smaliDirs) for sf in allCodeFiles]

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

    print("Code in closest namespace: {}".format(closestNamespace))

    # By default, top 5 MBs of code is used study apps' similarity.
    # However, this function may be called to use all code files.
    if not includeAllCodes:
        allCodeFiles = [cf for cf in allCodeFiles if closestNamespace in getNamespace(cf, smaliDirs)]

    # Sort Smali files by file sizes
    smaliFilesByFileSize = sorted([f for f in allCodeFiles
                                   if os.path.isfile(f) and f.endswith(".smali") and (
                                       not os.path.basename(f).startswith("R$"))], key=lambda f: os.path.getsize(f),
                                  reverse=True)  

    # Find the 5 MB threshold in an array of filenames
    maxFileIndex = None
    accumulatedSize = 0
    for i in range(len(smaliFilesByFileSize)):
        accumulatedSize = accumulatedSize + os.path.getsize(smaliFilesByFileSize[i])
        if accumulatedSize > smaliSizeLimitInBytes:
            maxFileIndex = i
            break

    # Remove the filenames on the list beyond the 5 MB threshold
    if maxFileIndex is not None:
        smaliFilesByFileSize = [sf for sf in smaliFilesByFileSize[0:(maxFileIndex + 1)]]

    # Merge the Smali code files on the list into a single file
    destinationFile = open(fileToBeMerged, "w", encoding="utf-8")
    for smaliFile in smaliFilesByFileSize:
        sourceFile = open(smaliFile, "r")
        for line in sourceFile:
            if (not line.startswith("#")) and (not line == "\n"):
                destinationFile.write(line)
        sourceFile.close()
    destinationFile.close()


def MergeSmaliFilesIntoOne(apkRootDir, outputSmaliFilename, outputNSFilename, allCode):
    """Prepare directory data and pass them to the main Smali code merger flow.
       Args:
         apkRootDir: The directory in which the contents of an APK are extracted to
         outputSmaliFilename: Full filename for a target file of merged Smali code
         outputNSFilename: Full filename for a target file containing a list of namespaces
         allCode: Whether all code files are included. (See mergeFiles function for details)
        Returns:
          None
    """

    # Get a list of directories containing Smali code files
    manifestFilename = os.path.join(apkRootDir, "AndroidManifest.xml")
    smaliDirs = [os.path.join(os.path.join(apkRootDir, "smali"))]

    # apktool stores Smali code files in multiple directories: smali_classes2, smali_classes3...
    # Check the existence a next directory by chaning the numbered suffix
    for i in range(2, 1024):
        nextDir = os.path.join(os.path.join(apkRootDir, "smali_classes{}".format(i)))
        if os.path.exists(nextDir) and os.path.isdir(nextDir):
            smaliDirs.append(nextDir)
        else:
            break
    
    if os.path.exists(manifestFilename) and os.path.exists(smaliDirs[0]):
        packageName = readPackageNameFromManifest(manifestFilename)
        # data passed to the main merger flow
        mergeFiles(smaliDirs, packageName, outputSmaliFilename, outputNSFilename, allCode)
    else:
        print("Not an apk root directory: {}".format(apkRootDir))


if __name__ == '__main__':
    # The usage of arguemnts is self-explanatory as follows
    argParser = argparse.ArgumentParser()
    argParser.add_argument("--apkDir", help="Root Directory of an APK extracted using APKTOOL", required=True)
    argParser.add_argument("--outputSmaliFile", help="The output smali file to be saved", required=True)
    argParser.add_argument("--outputNameSpaceFile", help="The output namespace file to be saved", required=True)
    argParser.add_argument("--allCode",
                           help="Include code beyond the name space of the app ID", action="store_true")
    args = argParser.parse_args()

    MergeSmaliFilesIntoOne(os.path.realpath(args.apkDir), os.path.realpath(args.outputSmaliFile),
                           os.path.realpath(args.outputNameSpaceFile), args.allCode)
