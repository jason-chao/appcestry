#!/usr/bin/env python3


from flask import Flask, request, send_file, url_for, redirect
from werkzeug import secure_filename
import datetime
from rq import Queue
from redis import Redis
import executor
import os
import json
import zipfile
import shutil


app = Flask(__name__)


convertQueue = None
compareQueue = None
tempDir = "/tmp/appcestry/"


def saveApkFile(f):
    baseFilename = "apk_{}_{}".format(getSafeTimestamp(), secure_filename(f.filename))
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
                zf.write(os.path.join(tempDir, f), arcname=f)
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
        jobStatus["status"] = "invalid_id"
    return json.dumps(jobStatus)


@app.route("/", methods=["GET"])
def landing_page():
    return "Hi, the time now is {}\n".format(datetime.datetime.utcnow().isoformat())


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
def convert():
    resultObject = {"jobid": "no_job", "message": None, "filesOnServer": []}
    filenameList = []

    if "file[]" in request.files:
        files = request.files.getlist("file[]")
        filenameList.extend([saveAppgeneFile(f) for f in files])
    elif "file" in request.files:
        f = request.files["file"]
        filenameList.extend(unzipAppgeneFiles(f))

    if len(filenameList) > 1:
        jobIdentifier = secure_filename("{}_{}".format(request.remote_addr, getSafeTimestamp()))
        compareQueue.enqueue_call(func=executor.compare_genes, args=(filenameList,), job_id=jobIdentifier)
        resultObject["message"] = "Please open {} to check the result".format(
            url_for("comparison_result", job_id=jobIdentifier))
        resultObject["jobid"] = jobIdentifier
        resultObject["filesOnServer"] = filenameList
    elif len(filenameList) == 1:
        resultObject["message"] = "At least two files are required for comparison"
    else:
        resultObject["message"] = "No valid files or comparison"

    return json.dumps(resultObject)


@app.route("/compare/<job_id>", methods=["GET"])
def comparison_result(job_id):
    job = compareQueue.fetch_job(job_id)
    return respondToStatusEnquiry(job)


@app.route("/convert", methods=["POST"])
def convert_apk():
    filenameList = []
    if "file[]" in request.files:
        files = request.files.getlist("file[]")
        filenameList.extend([saveApkFile(f) for f in files])
    elif "file" in request.files:
        f = request.files["file"]
        filenameList.append(saveApkFile(f))
    jobIdentifier = secure_filename("{}_{}".format(request.remote_addr, getSafeTimestamp()))
    convertQueue.enqueue_call(func=executor.convert_batch, args=(filenameList,), job_id=jobIdentifier)
    resultObject = {
        "message": "Please open {} to check the result".format(
            url_for("conversion_result", job_id=jobIdentifier)), "filesOnServer": filenameList, "jobid": jobIdentifier
    }
    return json.dumps(resultObject)


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
    print("temporary director: {}\n".format(tempDir))
    redisConnection = os.getenv("APPCESTRY_REDIS_HTTP_SERVER_CONNECION", "127.0.0.1")
    httpListenOnPort = int(os.getenv("APPCESTRY_HTTP_LISTENING_PORT", "8080"))
    httpListenAtAddress = os.getenv("APPCESTRY_HTTP_LISTENING_ADDR", "127.0.0.1")
    convertQueue = Queue("convert", connection=Redis(redisConnection))
    compareQueue = Queue("compare", connection=Redis(redisConnection))
    app.run(httpListenAtAddress, httpListenOnPort, debug=True)
