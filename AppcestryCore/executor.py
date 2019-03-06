#!/usr/bin/env python3

# The HTTP interface calls the functions in this file by creating RQ jobs.
# The batch operations use Dask to run a conversion / comparsion function in multiple nodes or threads.

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
httpServerDestination = os.getenv("APPCESTRY_HTTP_SERVER", "http://127.0.0.1:8899")
fileDownloadBaseUrl = "{}/tmpFile/".format(httpServerDestination)
fileUploadBaseUrl = "{}/tmpFile".format(httpServerDestination)


def getSafeTimestamp():
    """Generate a filename-safe UTC timestamp
       Returns:
         A timestamp in string
    """
    return secure_filename(datetime.datetime.utcnow().isoformat()).replace(".", "-")


def compareAppGenePair(pair):
    """Compare a pair of AppGene files.  AppGene files are downloaded from the HTTP interface and then compared.
       Args:
         pair: A list of base filenames of two AppGene files available from the HTTP interface
       Returns:
         A comparison result object loaded from JSON
    """
    fileOne = pair[0]
    fileTwo = pair[1]
    tempGeneDir = tempfile.mkdtemp(prefix="gene_comparison")
    geneBufferDir = tempfile.mkdtemp(prefix="gene_comparison_buffer")
    os.chmod(tempGeneDir, mode=0o777)
    os.chmod(geneBufferDir, mode=0o777)

    comparisonResult = {"success": False, "comparison": ""}

    # download the two files from the HTTP interface
    localFilenameOne = os.path.join(tempGeneDir, fileOne)
    urllib.request.urlretrieve(urljoin(fileDownloadBaseUrl, fileOne), localFilenameOne)

    localFilenameTwo = os.path.join(tempGeneDir, fileTwo)
    urllib.request.urlretrieve(urljoin(fileDownloadBaseUrl, fileTwo), localFilenameTwo)

    outputFilename = os.path.join(tempGeneDir, "result_{}.json".format(os.path.join(getSafeTimestamp())))

    # Execute the comparison script as a subprocess; the paths to the two AppGene files are passed to the subprocess in the argument
    p = subprocess.Popen([os.path.join(coreDir, "compare.py"), "--mode", "single-pair",
                          "--appgene1", localFilenameOne, "--appgene2", localFilenameTwo,
                          "--bufferDir", geneBufferDir, "--outputFile", outputFilename])
    # Wait until the comparison is done
    p.wait()

    # Load the comparsion result file in JSON
    # In case of any error, let the function return the default (unsuccessful) result object
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
    """Convert a single APK file to an AppGene file.  An APK file is downloaded from the HTTP interface and then converted into AppGene file.  After the conversion, the AppGene file is uploaded to the HTTP interface.  
       Args:
         filename: The base filename of an APK file available from the HTTP interface
       Returns:
         A conversion result object containing the base filename of the AppGene file uploaded to the HTTP interface
    """
    tempApkDir = tempfile.mkdtemp(prefix="apk_conversion")
    tempProcessingDir = tempfile.mkdtemp(prefix="disassembled_apk")

    os.chmod(tempApkDir, mode=0o777)
    os.chmod(tempProcessingDir, mode=0o777)

    conversionResult = {"success": False, "genefilename": ""}
    localTempFilename = os.path.join(tempApkDir, filename)

    # Download the APK file from the HTTP interface
    urllib.request.urlretrieve(urljoin(fileDownloadBaseUrl, filename), localTempFilename)

    # Execute the conversion script as a subprocess; the path to the APK file is passed to the subprocess in the argument
    p = subprocess.Popen([os.path.join(coreDir, "conversion.py"), "--apkFile", localTempFilename,
                          "--outputDir", tempProcessingDir, "--affiliatedDir", coreDir])
    # Wait until the conversion is done
    p.wait()

    appGenefilename = ""
    # Idenify the AppGene file generated
    for baseFilename in os.listdir(tempProcessingDir):
        fullFilename = os.path.join(tempProcessingDir, baseFilename)
        if os.path.isfile(fullFilename) and fullFilename.endswith(".appgene"):
            appGenefilename = fullFilename
            break
    # If AppGene file is idenified, upload it to the HTTP interface.  If not, let the function return the default (unsuccessful) result object.
    if appGenefilename:
        conversionResult["genefilename"] = "{}___{}".format(getSafeTimestamp(), os.path.basename(appGenefilename))
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
    """Convert APK files to AppGene files in batch.  Dask creates multiple threads or use multiple nodes to execute the convertSingleApk function.
       Args: 
         apkFilenameList: A list of the base filenames of APK files available from the HTTP interface to be converted 
       Returns:
         A list of conversion result objects 
    """
    client = Client(daskSchedulerConnection)
    # One APK file per new task
    futures = client.map(convertSingleApk, apkFilenameList)
    # Await until all tasks are done
    results = client.gather(futures)
    return list(results)


def compare_genes(appGeneFilenameList):
    """Compare mutliple AppGene files.  Dask creates multiple threads or use multiple nodes to execute the compareAppGenePair function.
       Args: 
         appGeneFilenameList: A list of the base filenames of AppGene files available from the HTTP interface to be converted 
       Returns:
         A list of comparison result objects 
    """
    client = Client(daskSchedulerConnection)
    # Create all combinations of AppGene file pairs
    pairList = list(itertools.combinations(appGeneFilenameList, 2))
    # One combination per new task
    futures = client.map(compareAppGenePair, pairList)
    # Await until all tasks are done
    results = client.gather(futures)
    return list(results)
