#!/usr/bin/env python3

# This is the HTTP-based service of Appcestry that the web-based (HTML/JavaScript) user interface interacts with.
# The defualt configuration in the docker-compose file makes this HTTP interface sitting behind a reverse proxy powered by Nginx that also hosts static content (the UI).  
# However, the container instance that runs this script may be the endpoint exposed to the users and third-party applications, if needed.  

# The conversion of APK files to AppGene and the comparsion of AppGenes are computation-intensive tasks.
# This service creates a Redis Queue (RD) job for these two types of tasks.
# Dask scheduler and worker receive data about the jobs from Redis.  Dask will distribute the jobs to instances of rq_worker_compare and rq_worker_convert containers for execution.

from flask import Flask, request, send_file, url_for, redirect, Response
from flask_cors import CORS
from werkzeug import secure_filename
import datetime
from rq import Queue
from redis import Redis
import executor
import os
import json
import zipfile
import shutil
import socket
import logging
import string
import random
import numpy

app = Flask(__name__)
CORS(app)

convertQueue = None
compareQueue = None
tempDir = "/tmp/appcestry/"
jobExpirySec = 86400
jobTimeoutSec = 3600

alphanumericChars = string.ascii_letters + string.digits
jobIDRandomSuffixLength = 6


def saveApkFile(f):
    """Save a single APK file to local buffer directory
    Args:
      f: File object in Flask's request.files collection
    Returns:
      The base filename of the saved APK file in local buffer directory
    """
    baseFilename = "apk___{}___{}".format(getSafeTimestamp(), secure_filename(f.filename))
    filename = os.path.join(tempDir, baseFilename)
    f.save(filename)
    return baseFilename


def saveAppgeneFile(f):
    """Save an single AppGene file to local buffer directory
    Args:
      f: File object in Flask's request.files collection
    Returns:
      The base filename of the saved AppGene file in local buffer directory
    """
    baseFilename = "appgene_{}".format(getSafeTimestamp())
    filename = os.path.join(tempDir, baseFilename)
    f.save(filename)
    return baseFilename


def unzipAppgeneFiles(f):
    """Save an zip file local buffer directory and unzip it
    Args:
      f: File object in Flask's request.files collection
    Returns:
      A list of base filenames of the unzipped AppGene files in local buffer directory
    """
    extractedFilesOnServer = []
    baseFilename = "zipped_appgene_{}_{}".format(getSafeTimestamp(), secure_filename(f.filename))
    filename = os.path.join(tempDir, baseFilename)
    f.save(filename)
    # proceed if it is a zip file, otherwise return an empty collection
    if zipfile.is_zipfile(filename):
        uploadedZip = zipfile.ZipFile(filename)
        extractionDir = os.path.join(tempDir, "extracted_{}".format(getSafeTimestamp()))
        os.mkdir(extractionDir)
        os.chmod(extractionDir, mode=0o777)
        uploadedZip.extractall(extractionDir)
        # walk through the directory containing the extracted files
        # and move only the files with ".appgene" extension to local buffer directory
        for extractionRoot, extractedDirs, extractedFiles in os.walk(extractionDir):
            for extractedFile in extractedFiles:
                if extractedFile.endswith(".appgene"):
                    extractedFilenameOnServer = "appgene_{}".format(getSafeTimestamp())
                    os.rename(os.path.join(extractionRoot, extractedFile),
                              os.path.join(tempDir, extractedFilenameOnServer))
                    extractedFilesOnServer.append(extractedFilenameOnServer)
        # remove the whole directory in which the files are initially unzipped to
        shutil.rmtree(extractionDir)
    return extractedFilesOnServer


def getSafeTimestamp():
    """Generate a filename-safe UTC timestamp 
    Returns:
      A timestamp in string
    """
    return secure_filename(datetime.datetime.utcnow().isoformat()).replace(".", "-")


def zipJobFiles(jobID, filenameList):
    """Create a zip file of files generated for the job (Appgenes)
    Args:
      jobID: The unique identifier of the job
      filenameList: A collection of the base filenames of the files in the local buffer directory to be zipped
    Returns:
      The base filename of the zip file
    """
    zipFilename = secure_filename("appgenes_{}.zip".format(jobID))
    if not os.path.exists(zipFilename):
        with zipfile.ZipFile(os.path.join(tempDir, zipFilename), mode="w", compression=zipfile.ZIP_STORED) as zf:
            for f in filenameList:
                zf.write(os.path.join(tempDir, f), arcname=f.split("___").pop())
    return zipFilename


def respondToStatusEnquiry(job):
    """Respond to HTTP enquiry of the status of a job
    Args:
      job: RQ job object
    Returns:
      Flask HTTP response in JSON
    """
    jobStatus = {
        "jobID": "no_job",
        "status": "unknown",
        "result": {},
    }
    if job is not None:
        jobStatus["jobID"] = job.id
        jobStatus["status"] = job.get_status()
        if job.result is not None:
            jobStatus["result"] = job.result
    else:
        jobStatus["status"] = "invalid"
    return Response(json.dumps(jobStatus), status=200, mimetype="application/json")


@app.route("/", methods=["GET"])
def landing_page():
    """HTTP endpoint - GET /
       This endpoint is not invoked by the UI or other container instances.  It is for the service maintenance to check if the service is successfully deployed.
    Returns:
      The time now in plaintext 
    """
    return Response("Hi, the time now is {}\n".format(datetime.datetime.utcnow().isoformat()), status=200,
                    mimetype="text/plain")


@app.route("/tmpFile/<filename>", methods=["GET"])
def get_temp_file(filename):
    """HTTP endpoint - GET /tmpFile
       This endpoint is not invoked by the UI.  It is for the service maintenance to check if the service is successfully deployed.
    Args:
      filename: The filename for the file in the local buffer directory requested (Note: dot dot slash attack should not work if the interface sits behind Nginx)
    Returns:
      Flask HTTP response with the file content
    """
    return send_file(os.path.join(tempDir, filename), attachment_filename=filename)


@app.route("/tmpFile", methods=["POST"])
def upload_temp_file():
    """HTTP endpoint - POST /tmpFile
       Endpoint for container instances in other roles to upload ouput files to the local buffer directory
    Returns:
      The base filename of the uploaded file 
    """
    if "file" in request.files:
        f = request.files["file"]
        filename = os.path.join(tempDir, f.filename)
        f.save(filename)
        return os.path.basename(filename)
    return "NIL"


@app.route("/compare", methods=["POST"])
def compare_appgene():
    """HTTP endpoint - POST /compare
       Endpoint for the UI to upload Appgene files to be compared
       Files with extension ".zip" or ".appgene" are accepted
    Returns:
      Flask HTTP response about the job created in JSON 
    """
    resultObject = {"jobid": "no_job", "message": None, "filesOnServer": []}
    filenameList = []

    # Save and extract (if zipped) the uploaded files
    # Also filter out files with wrong extensions
    for fileKey in request.files:
        if request.files[fileKey].filename.lower().endswith(".appgene"):
            filenameList.append(saveAppgeneFile(request.files[fileKey]))
        elif request.files[fileKey].filename.lower().endswith(".zip"):
            filenameList.extend(unzipAppgeneFiles(request.files[fileKey]))

    # Comparsion needs more than one file
    if len(filenameList) > 1:
        jobIdentifier = secure_filename("{}_{}".format(getSafeTimestamp(), "".join(
            numpy.random.choice(list(alphanumericChars), size=jobIDRandomSuffixLength))))
        # Create a RQ job for AppGene comparison
        compareQueue.enqueue_call(func=executor.compare_genes, args=(filenameList,), job_id=jobIdentifier,
                                  result_ttl=jobExpirySec)
        resultObject["message"] = "Please open {} to check the result".format(
            url_for("comparison_result", job_id=jobIdentifier))
        resultObject["jobid"] = jobIdentifier
        resultObject["filesOnServer"] = filenameList
    elif len(filenameList) == 1:
        resultObject["message"] = "At least two files are required for comparison"
    else:
        resultObject["message"] = "No valid files or comparison"

    return Response(json.dumps(resultObject), status=200, mimetype="application/json")


@app.route("/compare/<job_id>", methods=["GET"])
def comparison_result(job_id):
    """HTTP endpoint - GET /compare
       Endpoint for the UI to check the status of a comparsion job
    Args:
      job_id: RQ job id
    Returns:
      Flask HTTP response about the job status in JSON 
    """
    job = compareQueue.fetch_job(job_id)
    return respondToStatusEnquiry(job)


@app.route("/convert", methods=["POST"])
def convert_apk():
    """HTTP endpoint - POST /convert
       Endpoint for the UI to upload APK files to be converted to AppGene files
       Files with extension ".apk" are accepted
    Returns:
      Flask HTTP response about the job created in JSON 
    """
    filenameList = []

    # Filter out files with wrong extensions
    for fileKey in request.files:
        if request.files[fileKey].filename.lower().endswith(".apk"):
            filenameList.append(saveApkFile(request.files[fileKey]))
    jobIdentifier = secure_filename("{}_{}".format(getSafeTimestamp(), "".join(
        numpy.random.choice(list(alphanumericChars), size=jobIDRandomSuffixLength))))
    if len(filenameList) > 0:
        # Create a RQ job for AppGene conversion
        convertQueue.enqueue_call(func=executor.convert_batch, args=(filenameList,), job_id=jobIdentifier,
                                  result_ttl=jobExpirySec)
    resultObject = {
        "filesOnServer": filenameList, "jobid": jobIdentifier
    }
    return Response(json.dumps(resultObject), status=200, mimetype="application/json")


@app.route("/convert/queue", methods=["GET"])
def conversion_jobs_in_queue():
    """HTTP endpoint - GET /convert/queue
       This endpoint is not invoked by the UI or other container instances.  It is for the service maintenance to check the statues of all the jobs.
    Returns:
      Statues of all the jobs in JSON
    """
    return "".join(["{} : {}\n".format(jid, convertQueue.fetch_job(jid).get_status()) for jid in convertQueue.job_ids])


@app.route("/zip/<job_id>", methods=["GET"])
def get_job_zip_file(job_id):
    """HTTP endpoint - GET /zip
       This endpoint is for the UI to download all the output files (AppGene files) of an AppGene conversion job in a single zip file
    Args:
      job_id: RQ job id of an AppGene conversion job
    Returns:
      Flask HTTP redirection to the zip file created
    """
    job = convertQueue.fetch_job(job_id)
    if job is not None:
        if job.result is not None:
            successfulGenes = list(j["genefilename"] for j in job.result if j["success"])
            zipFilename = zipJobFiles(job_id, successfulGenes)
            return redirect(url_for("get_temp_file", filename=zipFilename))
    return "NIL"


@app.route("/convert/<job_id>", methods=["GET"])
def conversion_result(job_id):
    """HTTP endpoint - GET /convert
       Endpoint for the UI to check the status of a AppGene conversion job
    Args:
      job_id: RQ job id
    Returns:
      Flask HTTP response about the job status in JSON 
    """
    job = convertQueue.fetch_job(job_id)
    return respondToStatusEnquiry(job)


if __name__ == "__main__":
    """Configure and start the RQ and Flask HTTP service 
    """
    app.logger.setLevel(logging.INFO)
    myIpAddress = socket.gethostbyname(socket.gethostname())
    app.logger.info("Temporary directory: {}\n".format(tempDir))
    redisConnection = os.getenv("APPCESTRY_REDIS_HTTP_SERVER_CONNECION", myIpAddress)
    httpListenOnPort = int(os.getenv("APPCESTRY_HTTP_LISTENING_PORT", "8899"))
    httpListenAtAddress = os.getenv("APPCESTRY_HTTP_LISTENING_ADDR", myIpAddress)
    app.logger.info("URL: http://{}:{}/\n".format(myIpAddress, httpListenOnPort))
    convertQueue = Queue("convert", connection=Redis(redisConnection), default_timeout=jobTimeoutSec)
    compareQueue = Queue("compare", connection=Redis(redisConnection), default_timeout=jobTimeoutSec)
    app.run(httpListenAtAddress, httpListenOnPort, debug=True)
