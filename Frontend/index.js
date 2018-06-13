Dropzone.autoDiscover = false;
/* var baseUrl = "http://172.18.0.5:8080";*/
/* const baseUrl = `${window.location.protocol}//${window.location.hostname}:${window.location.port}${window.location.pathname}`;*/
const baseUrl = "";
var conversionJobList = [];
var comparisonJobList = [];
var conversionJobDashboard = null;
var comparisonJobDashboard = null;
const linkToAppDetails = "http://play.google.com/store/apps/details?id=";
const uploadTimeoutMS = 50 * 60 * 1000;

function refreshComparisonJobs() {

    Array.from(comparisonJobList.keys()).forEach(function (jobKey) {
        if (!["finished", "failed"].includes(comparisonJobList[jobKey]["status"])) {
            $.get(baseUrl + "compare/" + comparisonJobList[jobKey]["jobid"], function (responseObject) {
                comparisonJobList[jobKey]["status"] = responseObject["status"];
                comparisonJobList[jobKey]["responseObject"] = responseObject;
            }).done(function () {
                comparisonJobDashboard.updateLists();
            });
        }
    });
}

function getCSVFileContent(comparisonObj) {

    let csvText = `app_id, version_code\n` +
        `${comparisonObj["pair"][0]["id"]}, ${comparisonObj["pair"][0]["version"]}\n` +
        `${comparisonObj["pair"][1]["id"]}, ${comparisonObj["pair"][1]["version"]}\n\n` +
        `measurement, similarity, intersection, union\n`;

    csvText += getCSVRowString("namespace", comparisonObj["namespace"]) + "\n";
    csvText += getCSVRowString("duplicate.exact", comparisonObj["media"]["exactDuplicates"]) + "\n";
    csvText += getCSVRowString("duplicate.near", comparisonObj["media"]["nearDuplicates"]) + "\n";
    csvText += getCSVRowString("permission.android", comparisonObj["permission"]["android"]) + "\n";
    csvText += getCSVRowString("permission.non_android", comparisonObj["permission"]["non-android"]) + "\n";
    csvText += getCSVRowString("bytecode.by_instruction", comparisonObj["smali"]["byLine"]) + "\n";
    csvText += getCSVRowString("bytecode.by_word", comparisonObj["smali"]["1-gram"]) + "\n";
    csvText += getCSVRowString("xml_attribute.names", comparisonObj["markup"]["names"]) + "\n";
    csvText += getCSVRowString("xml_attribute.values", comparisonObj["markup"]["values"]);

    return csvText;
}

function getCSVRowString(title, measurementObj) {
    if (measurementObj)
        return `${title}, ${measurementObj["ratio"]}, ${measurementObj["intersection"]}, ${measurementObj["union"]}`;
    else
        return `${title}, 0, 0, 0}`;
}

function getMeasurementTooltipText(measurementResult) {
    return `similarity ${ measurementResult["ratio"].toFixed(6) } = intersection ${ measurementResult["intersection"] } / union ${ measurementResult["union"] }`;
}

function getPercentageFromRatio(ratioValue) {
    return (ratioValue * 100).toFixed(2);
}

function getColourCodeByRatio(ratioValue) {
    if (ratioValue > 0.75)
        return "success";
    else if (ratioValue > 0.50)
        return "info";
    else if (ratioValue > 0.25)
        return "warning";
    else
        return "danger";
}

function refreshConversionJobs() {
    Array.from(conversionJobList.keys()).forEach(function (jobKey) {

        if (!["finished", "failed"].includes(conversionJobList[jobKey]["status"])) {
            $.get(baseUrl + "convert/" + conversionJobList[jobKey]["jobid"], function (resp) {
                let responseObject = resp;
                if (responseObject["status"] === "finished") {
                    conversionJobList[jobKey]["filelinks"] = [];
                    conversionJobList[jobKey]["conversionFailed"] = 0;
                    conversionJobList[jobKey]["conversionSucceeded"] = 0;
                    for (let r = 0; r < responseObject["result"].length; r++) {
                        if (responseObject["result"][r]["success"] === true) {
                            conversionJobList[jobKey]["filelinks"].push({
                                title: responseObject["result"][r]["genefilename"],
                                link: baseUrl + "tmpFile/" + responseObject["result"][r]["genefilename"],
                                filename: responseObject["result"][r]["genefilename"]
                            });
                            conversionJobList[jobKey]["conversionSucceeded"]++;
                        } else {
                            conversionJobList[jobKey]["conversionFailed"]++;
                        }
                    }
                    if (conversionJobList[jobKey]["conversionSucceeded"] > 0) {
                        conversionJobList[jobKey]["zipLink"] = baseUrl + "zip/" + conversionJobList[jobKey]["jobid"];
                        conversionJobList[jobKey]["zipFilename"] = conversionJobList[jobKey]["jobid"] + ".zip";
                    }
                }
                conversionJobList[jobKey]["status"] = responseObject["status"];
            }).done(function () {
                conversionJobDashboard.updateLists();
            });
        }
    });
}

$(document).ready(function () {

    conversionJobDashboard = new Vue({
        el: "#conversionJobsDashboard",
        data: {
            jobList: []
        },
        methods: {
            updateLists: function () {
                this.jobList = [];
                for (let i = 0; i < conversionJobList.length; i++) {
                    let displayObject = Object.assign(conversionJobList[i]);

                    let hashing = new jsSHA("SHA-256", "TEXT");
                    hashing.update(JSON.stringify(displayObject["jobid"]));
                    displayObject["jobIDHash"] = hashing.getHash("HEX");

                    if (displayObject["files"]) {
                        for (let fi = 0; fi < displayObject["files"].length; fi++) {
                            displayObject["files"][fi] = (displayObject["files"][fi]).split("___").pop();
                        }
                    }

                    if (displayObject["filelinks"]) {
                        for (let fi = 0; fi < displayObject["filelinks"].length; fi++) {
                            displayObject["filelinks"][fi]["title"] = displayObject["filelinks"][fi]["title"].split("___").pop();
                        }
                    }

                    if (["uploaded", "queued", "deferred"].includes(displayObject["status"])) {
                        displayObject["itemDisplayClass"] = "list-group-item-info";
                        displayObject["display_status"] = "Waiting"
                    } else if (displayObject["status"] === "started") {
                        displayObject["itemDisplayClass"] = "list-group-item-primary";
                        displayObject["display_status"] = "Processing"
                    } else if (displayObject["status"] === "finished") {
                        if ((displayObject["conversionSucceeded"] > 0) && (displayObject["conversionFailed"] <= 0)) {
                            displayObject["itemDisplayClass"] = "list-group-item-success";
                            displayObject["textDisplayClass"] = "text-success";
                            displayObject["display_status"] = "Completed";
                        } else if ((displayObject["conversionSucceeded"] > 0) && (displayObject["conversionFailed"] > 0)) {
                            displayObject["itemDisplayClass"] = "list-group-item-warning";
                            displayObject["textDisplayClass"] = "text-warning";
                            displayObject["display_status"] = "Completed";
                        } else if ((displayObject["conversionSucceeded"] <= 0) && (displayObject["conversionFailed"] > 0)) {
                            displayObject["itemDisplayClass"] = "list-group-item-danger";
                            displayObject["display_status"] = "Conversion failed";
                        }
                    } else if (displayObject["status"] === "failed") {
                        displayObject["itemDisplayClass"] = "list-group-item-danger";
                        displayObject["display_status"] = "Failed"
                        displayObject["conversionFailed"] = displayObject["files"].length;
                        displayObject["conversionSucceeded"] = 0;
                        displayObject["filelinks"] = null;
                        displayObject["zipLink"] = null;
                    } else {
                        displayObject["itemDisplayClass"] = "list-group-item-secondary";
                        displayObject["display_status"] = "Unknown"
                    }
                    this.jobList.push(displayObject)
                }
            }
        }
    });

    comparisonJobDashboard = new Vue({
        el: "#comparisonJobsDashboard",
        data: {
            resultList: [],
            alertList: []
        },
        methods: {
            addAlert: function (title, message, colourCode) {
                this.alertList.push({
                    title: title, message: message, colourCode: colourCode
                });
            },
            updateLists: function () {
                this.alertList = [];
                this.resultList = [];
                let tempResultList = []
                for (let i = 0; i < comparisonJobList.length; i++) {
                    let displayObject = Object.assign(comparisonJobList[i]["responseObject"]);
                    if (["uploaded", "queued", "deferred", "started", "failed"].includes(displayObject["status"])) {
                        if (["uploaded", "queued", "deferred"].includes(displayObject["status"])) {
                            this.addAlert("Waiting", `ID: ${comparisonJobList[i]["jobid"]}`, "info");
                        } else if (displayObject["status"] == "started") {
                            this.addAlert("Processing", `ID: ${comparisonJobList[i]["jobid"]}`, "primary");
                        } else {
                            this.addAlert("Failed", `ID: ${comparisonJobList[i]["jobid"]}`, "danger");
                        }
                    } else if (displayObject["status"] == "finished") {
                        if (Array.isArray(displayObject["result"])) {
                            tempResultList = tempResultList.concat(displayObject["result"].map(function (pairResult) {
                                if (pairResult["success"] !== true)
                                    return null;

                                let comparisonObj = pairResult["comparison"];
                                let hashing = new jsSHA("SHA-256", "TEXT");
                                hashing.update(JSON.stringify(comparisonObj["pair"]));
                                comparisonObj["id"] = hashing.getHash("HEX");

                                comparisonObj["pair"][0]["link"] = linkToAppDetails + comparisonObj["pair"][0]["id"];
                                comparisonObj["pair"][1]["link"] = linkToAppDetails + comparisonObj["pair"][1]["id"];

                                comparisonObj["measurementBars"] = [];

                                if (comparisonObj["namespace"]) {
                                    comparisonObj["measurementBars"].push({
                                        title: "Namespaces",
                                        value: getPercentageFromRatio(comparisonObj["namespace"]["ratio"]),
                                        colourCode: getColourCodeByRatio(comparisonObj["namespace"]["ratio"]),
                                        tooltipText: getMeasurementTooltipText(comparisonObj["namespace"])
                                    });
                                }

                                if (comparisonObj["media"]) {
                                    if (comparisonObj["media"]["exactDuplicates"]) {
                                        comparisonObj["measurementBars"].push({
                                            title: "Exact duplicate files",
                                            value: getPercentageFromRatio(comparisonObj["media"]["exactDuplicates"]["ratio"]),
                                            colourCode: getColourCodeByRatio(comparisonObj["media"]["exactDuplicates"]["ratio"]),
                                            tooltipText: getMeasurementTooltipText(comparisonObj["media"]["exactDuplicates"])
                                        });
                                    }

                                    if (comparisonObj["media"]["nearDuplicates"]) {
                                        comparisonObj["measurementBars"].push({
                                            title: "Near duplicate images",
                                            value: getPercentageFromRatio(comparisonObj["media"]["nearDuplicates"]["ratio"]),
                                            colourCode: getColourCodeByRatio(comparisonObj["media"]["nearDuplicates"]["ratio"]),
                                            tooltipText: getMeasurementTooltipText(comparisonObj["media"]["nearDuplicates"])
                                        });
                                    }
                                }

                                if (comparisonObj["permission"]) {
                                    if (comparisonObj["permission"]["android"]) {
                                        comparisonObj["measurementBars"].push({
                                            title: "Permissions (Android)",
                                            value: getPercentageFromRatio(comparisonObj["permission"]["android"]["ratio"]),
                                            colourCode: getColourCodeByRatio(comparisonObj["permission"]["android"]["ratio"]),
                                            tooltipText: getMeasurementTooltipText(comparisonObj["permission"]["android"])
                                        });
                                    }

                                    if (comparisonObj["permission"]["non-android"]) {
                                        comparisonObj["measurementBars"].push({
                                            title: "Permissions (non-Android)",
                                            value: getPercentageFromRatio(comparisonObj["permission"]["non-android"]["ratio"]),
                                            colourCode: getColourCodeByRatio(comparisonObj["permission"]["non-android"]["ratio"]),
                                            tooltipText: getMeasurementTooltipText(comparisonObj["permission"]["non-android"])
                                        });
                                    }
                                }

                                if (comparisonObj["smali"]) {
                                    if (comparisonObj["smali"]["byLine"]) {
                                        comparisonObj["measurementBars"].push({
                                            title: "Bytecode (estimate)",
                                            value: getPercentageFromRatio(comparisonObj["smali"]["byLine"]["ratio"]),
                                            colourCode: getColourCodeByRatio(comparisonObj["smali"]["byLine"]["ratio"]),
                                            tooltipText: getMeasurementTooltipText(comparisonObj["smali"]["byLine"])
                                        });
                                    }
                                }

                                if (comparisonObj["markup"]) {
                                    if (comparisonObj["markup"]["names"]) {
                                        comparisonObj["measurementBars"].push({
                                            title: "XML attribute names",
                                            value: getPercentageFromRatio(comparisonObj["markup"]["names"]["ratio"]),
                                            colourCode: getColourCodeByRatio(comparisonObj["markup"]["names"]["ratio"]),
                                            tooltipText: getMeasurementTooltipText(comparisonObj["markup"]["names"])
                                        });
                                    }

                                    if (comparisonObj["markup"]["values"]) {
                                        comparisonObj["measurementBars"].push({
                                            title: "XML attribute values",
                                            value: getPercentageFromRatio(comparisonObj["markup"]["values"]["ratio"]),
                                            colourCode: getColourCodeByRatio(comparisonObj["markup"]["values"]["ratio"]),
                                            tooltipText: getMeasurementTooltipText(comparisonObj["markup"]["values"])
                                        });
                                    }
                                }

                                let csvText = getCSVFileContent(comparisonObj);
                                let csvAsBlob = new Blob([csvText], {type: "text/csv"});
                                comparisonObj["CSV_content"] = csvText;
                                comparisonObj["CSV_url"] = URL.createObjectURL(csvAsBlob);
                                comparisonObj["CSV_filename"] = `${comparisonObj["pair"][0]["id"]}_${comparisonObj["pair"][0]["version"]}` +
                                    `_v_${comparisonObj["pair"][1]["id"]}_${comparisonObj["pair"][1]["version"]}.csv`;

                                return comparisonObj;
                            }));
                        }
                    }
                }

                this.resultList = tempResultList.filter(function (element) {
                    return ((element !== null) && (element !== undefined));
                });

                if (this.resultList.length > 0) {
                    let combinedCsvAsBlob = new Blob(comparisonJobDashboard.resultList.map(function (comparisonObj) {
                        return comparisonObj["CSV_content"] + "\n\n\n\n";
                    }), {type: "text/csv"});
                    $("#downloadAllComparisonsLink").attr("href", URL.createObjectURL(combinedCsvAsBlob));

                    $("#downloadAllComparisonsLink").attr("download", `combined_${(new Date()).toISOString().replace(/:/g, "-")}.csv`);
                    $("#downloadAllComparisonsLink").removeAttr("hidden");
                } else {
                    $("#downloadAllComparisonsLink").attr("hidden", "hidden");
                    $("#downloadAllComparisonsLink").attr("href", "#");
                }
            }
        }
    });

    var apkFileDrop = new Dropzone("#apk-uploader", {
        url: baseUrl + "convert",
        uploadMultiple: true,
        parallelUploads: 100,
        maxFilesize: 1024,
        timeout: uploadTimeoutMS
    });
    apkFileDrop.on("success", function (file, result) {
        if (conversionJobList.find(function (rj) {
            return rj["jobid"] === result["jobid"];
        }) === undefined) {
            conversionJobList.unshift({
                jobid: result["jobid"],
                status: "uploaded",
                files: result["filesOnServer"]
            });
            refreshConversionJobs();
        }
    });
    apkFileDrop.on("complete", function (file) {
        apkFileDrop.removeFile(file);
    });

    var appGeneFileDrop = new Dropzone("#appgene-uploader", {
        url: baseUrl + "compare",
        uploadMultiple: true, parallelUploads: 100,
        maxFilesize: 1024,
        timeout: uploadTimeoutMS
    });
    appGeneFileDrop.on("success", function (file, result) {
        if (comparisonJobList.find(function (rj) {
            return rj["jobid"] === result["jobid"];
        }) === undefined) {
            comparisonJobList.unshift({
                jobid: result["jobid"],
                status: "uploaded",
                files: result["filesOnServer"]
            });
            refreshComparisonJobs();
        }
    });
    appGeneFileDrop.on("complete", function (file) {
        appGeneFileDrop.removeFile(file);
    });

    $("#clearComparisonDashboardButton").click(function () {
        comparisonJobList = comparisonJobList.filter(function (element) {
            return (!["finished", "failed"].includes(element["status"]));
        });
        comparisonJobDashboard.updateLists();
    });

    $("#refreshConversionDashboardButton").click(function () {
        refreshConversionJobs();
        $("#refreshConversionDashboardButton").fadeTo(500, 0.2, function () {
            $("#refreshConversionDashboardButton").fadeTo(100, 1);
        });
    });

    $("#refreshComparisonDashboardButton").click(function () {
        refreshComparisonJobs();
        $("#refreshComparisonDashboardButton").fadeTo(500, 0.2, function () {
            $("#refreshComparisonDashboardButton").fadeTo(100, 1);
        });
    });

    $(".goToTabConvert").click(function () {
        $("#linkToTabConvert").click();
    });

    $(".goToTabCompare").click(function () {
        $("#linkToTabCompare").click();
    });


    setInterval(refreshConversionJobs, 15000);
    setInterval(refreshComparisonJobs, 10000);

    window.onbeforeunload = function (e) {
        var dialogText = "You will lose access to unsaved files.  Are you sure to quit?";
        let processingStatus = ["uploaded", "queued", "deferred", "started"];
        if ((comparisonJobList.find(function (element) {
                return processingStatus.includes(element["status"]);
            }))
            || (conversionJobList.find(function (element) {
                return processingStatus.includes(element["status"]);
            }))) {
            e.returnValue = dialogText;
            return dialogText;
        }
    };
});
