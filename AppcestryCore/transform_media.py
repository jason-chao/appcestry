#!/usr/bin/env python3

# This script transforms resource files into hash values.  
# For still images, pHash (perceptual hash) is used.  For all other types of files, SHA25 is used.

import argparse
import os
import re
from PIL import Image, ImageEnhance
import imagehash
import json
from operator import itemgetter
import hashlib


def getAllFilesOfExtension(rootDir, patternRegExp):
    """Traverse a directory tree and find all the files with a specified extension
       Args:
         rootDir: The directory to traverse
         patternRegExp: Regular expression for extension matching
       Returns:
         A list of files
    """
    fileList = []
    filePatternRe = re.compile(patternRegExp)
    for (dirPath, dirNames, fileNames) in os.walk(rootDir):
        for filename in fileNames:
            if filePatternRe.search(filename):
                fileList.append((dirPath, filename, os.path.getsize(os.path.join(dirPath, filename))))
    return sorted(fileList, key=itemgetter(2), reverse=True)


def getFileSHA256(fileFullPath):
    """Get the SHA256 hash value of a file
       Args:
         fileFullPath: Full filename of a file
       Returns:
         Hex hash value in string
    """
    file = open(fileFullPath, "rb")
    fileContent = file.read()
    fileHash = hashlib.sha256(fileContent)
    file.close()
    return "%s" % fileHash.hexdigest()


def getImagePHash(imgFileFullPath):
    """Get the pHash value of an image file
       Args:
         fileFullPath: Full filename of an image file
       Returns:
         Hex hash value in string
    """
    try:
        image = Image.open(imgFileFullPath)
        imageW, imageH = image.size
        if imageW >= 24 and imageH >= 24:
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(0.5)
            imgHash = imagehash.phash(image.convert(mode="L"), hash_size=16)
            #binaryHashKey = "".join("{0:b}".format(hexValue) for hexValue in imgHash.hash.tobytes())
            hexHashKey = "{}".format(imgHash)
            return hexHashKey
    except:
        return None
    return None


def getMediaHashObject(apkDir):
    """Traverse a directory tree and get the hash values of all resource files.
       Args:
         apkDir: Directory in which contents of an APK are extracted to
       Returns:
         An object with properties:
           pHash: A list of pHash values
           sha256: A list of SHA25 values
    """
    allImageFiles = getAllFilesOfExtension(apkDir, "\.(png|jpg|jpeg|bmp)$")
    allMediaFiles = getAllFilesOfExtension(apkDir, "\.(ogg|wav|mp3|mp4|png|jpg|jpeg|bmp|html|htm|js|css)$")
    transformedMedia = {"phash": {}, "sha256": {}}

    for dirPath, baseFilename, fileSize in allImageFiles:
        imgFile = os.path.join(dirPath, baseFilename)
        imgFilepHash = getImagePHash(imgFile)
        if imgFilepHash is None:
            continue
        if imgFilepHash not in transformedMedia["phash"].keys():
            transformedMedia["phash"][imgFilepHash] = []
        transformedMedia["phash"][imgFilepHash].append(os.path.relpath(imgFile, apkDir))

    for dirPath, baseFilename, fileSize in allMediaFiles:
        mediaFile = os.path.join(dirPath, baseFilename)
        mediaFileHash = getFileSHA256(mediaFile)
        if mediaFileHash not in transformedMedia["sha256"].keys():
            transformedMedia["sha256"][mediaFileHash] = []
        transformedMedia["sha256"][mediaFileHash].append(os.path.relpath(mediaFile, apkDir))

    return transformedMedia


def HashMediaFiles(apkDir, outputFile):
    """Save the hash values of resource files to a file.
       Args:
         apkDir: Directory in which contents of an APK are extracted to
         outputFile: The full filename of the target file
       Returns:
         None
    """
    medaiFilesHashObject = getMediaHashObject(apkDir)
    json.dump(medaiFilesHashObject, outputFile, sort_keys=True, indent=2)


if __name__ == '__main__':
    # The usage of arguemnts is self-explanatory as follows
    argParser = argparse.ArgumentParser()
    argParser.add_argument("--apkDir", help="Root Directory of an APK extracted using APKTOOL", required=True)
    argParser.add_argument("--outputFile", help="The output file to be saved", type=argparse.FileType("w"), required=True)

    args = argParser.parse_args()
    apkDir = os.path.realpath(args.apkDir)
    HashMediaFiles(apkDir, args.outputFile)
