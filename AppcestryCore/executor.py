#!/usr/bin/env python3


import subprocess
from dask.distributed import Client
import urllib.request
import requests
from urllib.parse import urljoin
import tempfile
import os
import datetime
import json
import shutil
from werkzeug import secure_filename
import itertools


coreDir = os.getenv("APPCESTRY_CORE_DIR", os.path.curdir)
daskSchedulerConnection = os.getenv("APPCESTRY_DASK_SCHEDULER", "127.0.0.1:8786")
httpServerDestination = os.getenv("APPCESTRY_HTTP_SERVER", "http://127.0.0.1:8080")
fileDownloadBaseUrl = "{}/tmpFile/".format(httpServerDestination)
fileUploadBaseUrl = "{}/tmpFile".format(httpServerDestination)


def getSafeTimestamp():
    return secure_filename(datetime.datetime.utcnow().isoformat()).replace(".", "-")


def compareAppGenePair(pair):
    fileOne = pair[0]
    fileTwo = pair[1]
    tempGeneDir = tempfile.mkdtemp(prefix="gene_comparison")
    geneBufferDir = tempfile.mkdtemp(prefix="gene_comparison_buffer")
    os.chmod(tempGeneDir, mode=0o777)
    os.chmod(geneBufferDir, mode=0o777)

    comparisonResult = {"success": False, "comparison": ""}

    localFilenameOne = os.path.join(tempGeneDir, fileOne)
    urllib.request.urlretrieve(urljoin(fileDownloadBaseUrl, fileOne), localFilenameOne)

    localFilenameTwo = os.path.join(tempGeneDir, fileTwo)
    urllib.request.urlretrieve(urljoin(fileDownloadBaseUrl, fileTwo), localFilenameTwo)

    outputFilename = os.path.join(tempGeneDir, "result_{}.json".format(os.path.join(getSafeTimestamp())))

    p = subprocess.Popen([os.path.join(coreDir, "compare.py"), "--mode", "single-pair",
                          "--appgene1", localFilenameOne, "--appgene2", localFilenameTwo,
                          "--bufferDir", geneBufferDir, "--outputFile", outputFilename])
    p.wait()

    if os.path.isfile(outputFilename):
        try:
            with open(outputFilename, "r") as resultF:
                comparisonResult["comparison"] = json.load(resultF)
                comparisonResult["success"] = True
        except:
            print("Failed to read the result file")

    shutil.rmtree(tempGeneDir)
    shutil.rmtree(geneBufferDir)

    return comparisonResult


def convertSingleApk(filename):
    tempApkDir = tempfile.mkdtemp(prefix="apk_conversion")
    tempProcessingDir = tempfile.mkdtemp(prefix="disassembled_apk")

    os.chmod(tempApkDir, mode=0o777)
    os.chmod(tempProcessingDir, mode=0o777)

    conversionResult = {"success": False, "genefilename": ""}
    localTempFilename = os.path.join(tempApkDir, filename)

    urllib.request.urlretrieve(urljoin(fileDownloadBaseUrl, filename), localTempFilename)
    p = subprocess.Popen([os.path.join(coreDir, "conversion.py"), "--apkFile", localTempFilename,
                          "--outputDir", tempProcessingDir, "--affiliatedDir", coreDir])
    p.wait()
    appGenefilename = ""
    for baseFilename in os.listdir(tempProcessingDir):
        fullFilename = os.path.join(tempProcessingDir, baseFilename)
        if os.path.isfile(fullFilename) and fullFilename.endswith(".appgene"):
            appGenefilename = fullFilename
            break
    if appGenefilename:
        conversionResult["genefilename"] = "{}_{}".format(getSafeTimestamp(), os.path.basename(appGenefilename))
        os.rename(appGenefilename, os.path.join(tempProcessingDir, conversionResult["genefilename"]))
        fileHandler = open(os.path.join(tempProcessingDir, conversionResult["genefilename"]), "rb")
        requests.post(url=fileUploadBaseUrl, files={"file": fileHandler})
        conversionResult["success"] = True
    else:
        print("genefile {} not found".format(appGenefilename))

    shutil.rmtree(tempProcessingDir)
    shutil.rmtree(tempApkDir)

    return conversionResult


def convert_batch(apkFilenameList):
    client = Client(daskSchedulerConnection)
    futures = client.map(convertSingleApk, apkFilenameList)
    results = client.gather(futures)
    return list(results)


def compare_genes(appGeneFilenameList):
    client = Client(daskSchedulerConnection)
    pairList = list(itertools.combinations(appGeneFilenameList, 2))
    futures = client.map(compareAppGenePair, pairList)
    results = client.gather(futures)
    return list(results)
