#!/usr/bin/env python3

import argparse
import os
import json
import random
import datetime
from ruamel.yaml import YAML
from xml.etree import ElementTree as ET

thisProgramPath = os.path.realpath(os.path.curdir)
affiliatedProgramDir = thisProgramPath


def getAllFilesOfExtension(rootDir, extension):
    fileList = []
    for (dirPath, dirNames, fileNames) in os.walk(rootDir):
        for baseName in fileNames:
            if baseName.endswith(extension):
                fileList.append((dirPath, baseName))
    return fileList


def disassemble(apkFilename, disassemblyDir):
    outputDirForApk = os.path.join(disassemblyDir, os.path.basename(apkFilename))
    os.system("apktool d {} -o {} -f".format(apkFilename, outputDirForApk))
    return outputDirForApk


def mergePackageCode(apkDir, outputMergedSmaliFilename, outputExtratedNamespaceFilename):
    os.system("{} --apkDir {} --outputSmaliFile {} --outputNameSpaceFile {}".format(
        os.path.join(affiliatedProgramDir, "merge_smali.py"),
        apkDir,
        outputMergedSmaliFilename,
        outputExtratedNamespaceFilename
    ))


def transformCode(mergedSmaliFilename, outputTransformedSmaliFile):
    os.system("{} --inputFile {} --outputFile {}".format(
        os.path.join(affiliatedProgramDir, "transform_smali.py"),
        mergedSmaliFilename,
        outputTransformedSmaliFile
    ))


def mergeMarkup(apkDir, outputFile):
    os.system("{} --apkDir {} --outputFile {}".format(
        os.path.join(affiliatedProgramDir, "merge_markup.py"),
        apkDir,
        outputFile
    ))


def hashMedia(apkDir, outputFile):
    os.system("{} --apkDir {} --outputFile {}".format(
        os.path.join(affiliatedProgramDir, "transform_media.py"),
        apkDir,
        outputFile
    ))


def readFileContent(filename, mode):
    file = open(filename, mode)
    content = file.read()
    file.close()
    return content


def loadObjectFromJSONFile(filename):
    if os.path.exists(filename):
        if os.path.getsize(filename) > 0:
            fileContent = readFileContent(filename, "r")
            return json.loads(fileContent)
    return {}


def readVersionCode(toolYmalFilename):
    if os.path.exists(toolYmalFilename):
        yaml = YAML()
        fileContent = readFileContent(toolYmalFilename, "r")
        apkToolOutput = yaml.load(fileContent)
        return apkToolOutput["versionInfo"]["versionCode"]
    return "-1"


def ConvertApkToAppgeneFile(apkFilename, outputDir):
    startTime = datetime.datetime.utcnow()
    writeInfoOutput("Disassembling ...")
    apkDir = disassemble(apkFilename, outputDir)

    writeInfoOutput("Reading the package manifest ...")
    manifestDoc = ET.parse(os.path.join(apkDir, "AndroidManifest.xml"))
    manifestNode = manifestDoc.getroot()
    appID = manifestNode.attrib["package"]
    appVersionCode = readVersionCode(os.path.join(apkDir, "apktool.yml"))
    # upNodes = manifestNode.findall("uses-permission")
    permissionList = [n.attrib["{http://schemas.android.com/apk/res/android}name"] for n in
                      manifestNode.findall("uses-permission") if
                      "{http://schemas.android.com/apk/res/android}name" in n.attrib.keys()]
    permissionList.extend(
        [n.attrib["{http://schemas.android.com/apk/res/android}name"] for n in manifestNode.findall("uses-feature") if
         "{http://schemas.android.com/apk/res/android}name" in n.attrib.keys()])

    permissionList = list(set(permissionList))

    writeInfoOutput("Package is known as {}".format(appID))

    writeInfoOutput("Merging the code ...")
    mergedSmaliFilename = os.path.join(apkDir, "_mergedSmali.tmp_appgene")
    extractedNameSpacesFilename = os.path.join(apkDir, "_extractedNamespaces.tmp_appgene")
    mergePackageCode(apkDir, mergedSmaliFilename, extractedNameSpacesFilename)

    writeInfoOutput("Transforming the code ...")
    transformedSmaliFilename = os.path.join(apkDir, "_transformedSmali.tmp_appgene")
    transformCode(mergedSmaliFilename, transformedSmaliFilename)

    writeInfoOutput("Extracting XML ...")
    transformedXMLFilename = os.path.join(apkDir, "_extractedXML.tmp_appgene")
    mergeMarkup(apkDir, transformedXMLFilename)

    writeInfoOutput("Working with media files ...")
    hashedMediaFilename = os.path.join(apkDir, "_hashedMedia.tmp_appgene")
    hashMedia(apkDir, hashedMediaFilename)

    appGeneObject = {
        "version": "0.0.1",
        "appID": appID,
        "appVersion": appVersionCode,
        "smali": readFileContent(transformedSmaliFilename, "r"),
        "markup": loadObjectFromJSONFile(transformedXMLFilename),
        "media": loadObjectFromJSONFile(hashedMediaFilename),
        "namespace": loadObjectFromJSONFile(extractedNameSpacesFilename),
        "permission-feature": permissionList,
        "meta": {
            "startTime": startTime.isoformat(),
            "endTime": datetime.datetime.utcnow().isoformat()
        }
    }

    writeInfoOutput("Saving the AppGene ...")
    thisAppGeneFilename = os.path.join(outputDir, "{}-{}.appgene".format(appID, appVersionCode))
    appGeneExportFile = open(thisAppGeneFilename, "w")
    json.dump(appGeneObject, appGeneExportFile, ensure_ascii=False, separators=(",", ":"))
    appGeneExportFile.close()
    writeInfoOutput("Saved at {}".format(thisAppGeneFilename))


def writeInfoOutput(infoText):
    print(infoText)


if __name__ == '__main__':
    argParser = argparse.ArgumentParser()
    argParser.add_argument("--apkFile", help="Single APK file to be converted")
    argParser.add_argument("--dirOfApks", help="Directory containing the source APKs to be converted")
    argParser.add_argument("--shuffle", help="Shuffle the order of Apks (applicable to --dirOfApks only)",
                           action="store_true")
    argParser.add_argument("--affiliatedDir", help="Directory in which other Appcestry programmes are located",
                           default=os.getenv("APPCESTRY_CORE_DIR", thisProgramPath))
    argParser.add_argument("--outputDir", help="Directory in which the extracted and processed files should be saved",
                           default=thisProgramPath)

    args = argParser.parse_args()
    outputDir = os.path.realpath(args.outputDir)
    affiliatedProgramDir = os.path.realpath(args.affiliatedDir)

    if args.apkFile:
        apkFileFullname = os.path.realpath(args.apkFile)
        ConvertApkToAppgeneFile(apkFileFullname, outputDir)
    elif args.dirOfApks:
        apksDir = os.path.realpath(args.dirOfApks)
        apkFileTupleList = getAllFilesOfExtension(apksDir, ".apk")
        if args.shuffle:
            random.shuffle(apkFileTupleList)
        for apkFileTuple in apkFileTupleList:
            try:
                writeInfoOutput("Working on {}".format(apkFileTuple[1]))
                ConvertApkToAppgeneFile(os.path.join(apkFileTuple[0], apkFileTuple[1]), outputDir)
                writeInfoOutput("Done with {}".format(apkFileTuple[1]))
            except:
                writeInfoOutput("Failed to convert {}".format(apkFileTuple[1]))
                continue
