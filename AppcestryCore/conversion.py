#!/usr/bin/env python3

# This script converts APK files to AppGene files.
# Run this script in terminal / command line to see the usage of arguments.

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


def disassemble(apkFilename, disassemblyDir):
    """Disassemble an APK file using apktool
       Args:
         apkFilename: The full filename of the APK file
         disassemblyDir: The parent directory in which the directory for the APK will be created
       Returns:
         The name of directory that contains the files of an APK file extracted by apktool
    """
    outputDirForApk = os.path.join(disassemblyDir, os.path.basename(apkFilename))
    os.system("apktool d {} -o {} -f".format(apkFilename, outputDirForApk))
    return outputDirForApk


def mergePackageCode(apkDir, outputMergedSmaliFilename, outputExtractedNamespaceFilename):
    """Merge Smali files into a single one, by invoking script merge_smali.py.
       Args:
         apkDir: Directory in which contents of an APK are extracted to
         outputMergedSmaliFilename: Full filename for the output file for merged Smali code
         outputExtractedNamespaceFilename: Full filename for the output file for a list of namespaces discovered
       Return:
         None
    """
    os.system("{} --apkDir {} --outputSmaliFile {} --outputNameSpaceFile {}".format(
        os.path.join(affiliatedProgramDir, "merge_smali.py"),
        apkDir,
        outputMergedSmaliFilename,
        outputExtractedNamespaceFilename
    ))


def transformCode(mergedSmaliFilename, outputTransformedSmaliFile):
    """Transform Smali instructions, by invoking script transform_smali.py.
       Args:
         mergedSmaliFilename: Full filename for the input Smali code file
         outputTransformedSmaliFile: Full filename for the output file for transformed Smali code
       Return:
         None
    """
    os.system("{} --inputFile {} --outputFile {}".format(
        os.path.join(affiliatedProgramDir, "transform_smali.py"),
        mergedSmaliFilename,
        outputTransformedSmaliFile
    ))


def mergeMarkup(apkDir, outputFile):
    """Extract elements from markup files and write them to a file, by invoking script merge_markup.py.
       Args:
         apkDir: Directory in which contents of an APK are extracted to
         outputFile: Full filename for the output file
       Return:
         None
    """
    os.system("{} --apkDir {} --outputFile {}".format(
        os.path.join(affiliatedProgramDir, "merge_markup.py"),
        apkDir,
        outputFile
    ))


def hashMedia(apkDir, outputFile):
    """Get the hash values of all resources and write them to a file, by invoking script transform_media.py.
       Args:
         apkDir: Directory in which contents of an APK are extracted to
         outputFile: Full filename for the output file
       Return:
         None
    """
    os.system("{} --apkDir {} --outputFile {}".format(
        os.path.join(affiliatedProgramDir, "transform_media.py"),
        apkDir,
        outputFile
    ))


def readFileContent(filename, mode):
    """A generic function to read the content of a file.
       Args:
         filename: The full filename
         mode: Python's file opening mode
       Return:
         The content
    """
    file = open(filename, mode)
    content = file.read()
    file.close()
    return content


def loadObjectFromJSONFile(filename):
    """A generic function to read a JSON file.
       Args:
         filename: The full filename for the JSON file
       Return:
         The object loaded from JSON
    """
    if os.path.exists(filename):
        if os.path.getsize(filename) > 0:
            fileContent = readFileContent(filename, "r")
            return json.loads(fileContent)
    # Return an empty object if the file does not exist
    return {}


def readVersionCode(toolYmalFilename):
    """Read the APK's version code from apktool's Yaml output file.
       Args:
         filename: The full filename for the Yaml output file created by apktool
       Return:
         The version code in string
    """    
    if os.path.exists(toolYmalFilename):
        yaml = YAML()
        fileContent = readFileContent(toolYmalFilename, "r")
        apkToolOutput = yaml.load(fileContent)
        return apkToolOutput["versionInfo"]["versionCode"]
    return "-1"


def ConvertApkToAppgeneFile(apkFilename, outputDir):
    """The main flow of converting an APK to AppGene.  Discrete steps are carried out by invoking respective scripts.
       Args:
          apkFilename: The full filename for the APK file
          outputDir: The directory in which the contents of an APK file will be extracted to and the AppGene file will be saved to.
       Returns:
          None
    """
    startTime = datetime.datetime.utcnow()

    # Use apktool to disassemble the APK
    writeInfoOutput("Disassembling ...")
    apkDir = disassemble(apkFilename, outputDir)

    # Read the version code from Yaml output file generated by apktool
    appVersionCode = readVersionCode(os.path.join(apkDir, "apktool.yml"))

    # Read the AndroidManifest.xml file to get the app's ID and the list of permissions
    writeInfoOutput("Reading the package manifest ...")
    manifestDoc = ET.parse(os.path.join(apkDir, "AndroidManifest.xml"))
    manifestNode = manifestDoc.getroot()
    appID = manifestNode.attrib["package"]

    permissionList = [n.attrib["{http://schemas.android.com/apk/res/android}name"] for n in
                      manifestNode.findall("uses-permission") if
                      "{http://schemas.android.com/apk/res/android}name" in n.attrib.keys()]
    permissionList.extend(
        [n.attrib["{http://schemas.android.com/apk/res/android}name"] for n in manifestNode.findall("uses-feature") if
         "{http://schemas.android.com/apk/res/android}name" in n.attrib.keys()])

    permissionList = list(set(permissionList))

    writeInfoOutput("Package is known as {}".format(appID))

    # Merge the Smali code files into a single one
    writeInfoOutput("Merging the code ...")
    mergedSmaliFilename = os.path.join(apkDir, "_mergedSmali.tmp_appgene")
    extractedNameSpacesFilename = os.path.join(apkDir, "_extractedNamespaces.tmp_appgene")
    mergePackageCode(apkDir, mergedSmaliFilename, extractedNameSpacesFilename)

    # Transform the Smali instructions in the merged Smali file
    writeInfoOutput("Transforming the code ...")
    transformedSmaliFilename = os.path.join(apkDir, "_transformedSmali.tmp_appgene")
    transformCode(mergedSmaliFilename, transformedSmaliFilename)

    # Extract elements from XML files
    writeInfoOutput("Extracting XML ...")
    transformedXMLFilename = os.path.join(apkDir, "_extractedXML.tmp_appgene")
    mergeMarkup(apkDir, transformedXMLFilename)

    # Get the hash values of resource files (pHash for images and SHA256 for all other types)
    writeInfoOutput("Working with media files ...")
    hashedMediaFilename = os.path.join(apkDir, "_hashedMedia.tmp_appgene")
    hashMedia(apkDir, hashedMediaFilename)

    # Create an AppGene object
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

    # Write the AppGene object to a JSON file
    writeInfoOutput("Saving the AppGene ...")
    thisAppGeneFilename = os.path.join(outputDir, "{}-{}.appgene".format(appID, appVersionCode))
    appGeneExportFile = open(thisAppGeneFilename, "w")
    json.dump(appGeneObject, appGeneExportFile, ensure_ascii=False, separators=(",", ":"))
    appGeneExportFile.close()
    writeInfoOutput("Saved at {}".format(thisAppGeneFilename))


def writeInfoOutput(infoText):
    """A generic function to print log to screen.  This wrapper function is created in case a new logging method is required in the future.
       Args:
         infoText: The text
       Return:
         None
    """
    print(infoText)


if __name__ == '__main__':
    # The usage of arguemnts is self-explanatory as follows
    argParser = argparse.ArgumentParser()
    argParser.add_argument("--apkFile", help="Single APK file to be converted")
    argParser.add_argument("--dirOfApks", help="Directory containing the source APKs to be converted")
    argParser.add_argument("--shuffle", help="Shuffle the order of Apks (applicable to --dirOfApks only)",
                           action="store_true")
    argParser.add_argument("--affiliatedDir", help="Directory in which other Appcestry programmes are located",
                           default=os.getenv("APPCESTRY_CORE_DIR", thisProgramPath))
    argParser.add_argument("--outputDir", help="Directory in which the extracted and processed files should be saved to",
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
