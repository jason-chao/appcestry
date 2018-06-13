#!/usr/bin/env python3


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
    baseFilename = "apk___{}___{}".format(getSafeTimestamp(), secure_filename(f.filename))
    filename = os.path.join(tempDir, baseFilename)
    f.save(filename)
    return baseFilename


def saveAppgeneFile(f):
    baseFilename = "appgene_{}".format(getSafeTimestamp())
    filename = os.path.join(tempDir, baseFilename)
    f.save(filename)
    return baseFilename


def unzipAppgeneFiles(f):
    extractedFilesOnServer = []
    baseFilename = "zipped_appgene_{}_{}".format(getSafeTimestamp(), secure_filename(f.filename))
    filename = os.path.join(tempDir, baseFilename)
    f.save(filename)
    if zipfile.is_zipfile(filename):
        uploadedZip = zipfile.ZipFile(filename)
        extractionDir = os.path.join(tempDir, "extracted_{}".format(getSafeTimestamp()))
        os.mkdir(extractionDir)
        os.chmod(extractionDir, mode=0o777)
        uploadedZip.extractall(extractionDir)
        for extractionRoot, extractedDirs, extractedFiles in os.walk(extractionDir):
            for extractedFile in extractedFiles:
                if extractedFile.endswith(".appgene"):
                    extractedFilenameOnServer = "appgene_{}".format(getSafeTimestamp())
                    os.rename(os.path.join(extractionRoot, extractedFile),
                              os.path.join(tempDir, extractedFilenameOnServer))
                    extractedFilesOnServer.append(extractedFilenameOnServer)
        shutil.rmtree(extractionDir)
    return extractedFilesOnServer


def getSafeTimestamp():
    return secure_filename(datetime.datetime.utcnow().isoformat()).replace(".", "-")


def zipJobFiles(jobID, filenameList):
    zipFilename = secure_filename("appgenes_{}.zip".format(jobID))
    if not os.path.exists(zipFilename):
        with zipfile.ZipFile(os.path.join(tempDir, zipFilename), mode="w", compression=zipfile.ZIP_STORED) as zf:
            for f in filenameList:
                zf.write(os.path.join(tempDir, f), arcname=f.split("___").pop())
    return zipFilename


def respondToStatusEnquiry(job):
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
    return Response("Hi, the time now is {}\n".format(datetime.datetime.utcnow().isoformat()), status=200,
                    mimetype="text/plain")


@app.route("/tmpFile/<filename>", methods=["GET"])
def get_temp_file(filename):
    return send_file(os.path.join(tempDir, filename), attachment_filename=filename)


@app.route("/tmpFile", methods=["POST"])
def upload_temp_file():
    if "file" in request.files:
        f = request.files["file"]
        filename = os.path.join(tempDir, f.filename)
        f.save(filename)
        return os.path.basename(filename)
    return "NIL"


@app.route("/compare", methods=["POST"])
def compare_appgene():
    resultObject = {"jobid": "no_job", "message": None, "filesOnServer": []}
    filenameList = []

    for fileKey in request.files:
        if request.files[fileKey].filename.lower().endswith(".appgene"):
            filenameList.append(saveAppgeneFile(request.files[fileKey]))
        elif request.files[fileKey].filename.lower().endswith(".zip"):
            filenameList.extend(unzipAppgeneFiles(request.files[fileKey]))

    if len(filenameList) > 1:
        jobIdentifier = secure_filename("{}_{}".format(getSafeTimestamp(), "".join(
            numpy.random.choice(list(alphanumericChars), size=jobIDRandomSuffixLength))))
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
    job = compareQueue.fetch_job(job_id)
    return respondToStatusEnquiry(job)


@app.route("/convert", methods=["POST"])
def convert_apk():
    filenameList = []

    for fileKey in request.files:
        if request.files[fileKey].filename.lower().endswith(".apk"):
            filenameList.append(saveApkFile(request.files[fileKey]))

    jobIdentifier = secure_filename("{}_{}".format(getSafeTimestamp(), "".join(
        numpy.random.choice(list(alphanumericChars), size=jobIDRandomSuffixLength))))
    if len(filenameList) > 0:
        convertQueue.enqueue_call(func=executor.convert_batch, args=(filenameList,), job_id=jobIdentifier,
                                  result_ttl=jobExpirySec)
    resultObject = {
        "filesOnServer": filenameList, "jobid": jobIdentifier
    }
    return Response(json.dumps(resultObject), status=200, mimetype="application/json")


@app.route("/convert/queue", methods=["GET"])
def conversion_jobs_in_queue():
    return "".join(["{} : {}\n".format(jid, convertQueue.fetch_job(jid).get_status()) for jid in convertQueue.job_ids])


@app.route("/zip/<job_id>", methods=["GET"])
def get_job_zip_file(job_id):
    job = convertQueue.fetch_job(job_id)
    if job is not None:
        if job.result is not None:
            successfulGenes = list(j["genefilename"] for j in job.result if j["success"])
            zipFilename = zipJobFiles(job_id, successfulGenes)
            return redirect(url_for("get_temp_file", filename=zipFilename))
    return "NIL"


@app.route("/convert/<job_id>", methods=["GET"])
def conversion_result(job_id):
    job = convertQueue.fetch_job(job_id)
    return respondToStatusEnquiry(job)


if __name__ == "__main__":
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
