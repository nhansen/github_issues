import re
import os
import subprocess
import tempfile

def close_issue(issueid:str, sourcedir:str):
    
    bashcommand = "hub issue update " + issueid + " -s closed"
    process = subprocess.run(bashcommand.split(), cwd=sourcedir)

def transfer_issue(issueid:str, sourcedir:str, destinationrepo:str):
    
    bashcommand = "hub issue transfer " + issueid + " " + destinationrepo
    process = subprocess.run(bashcommand.split(), cwd=sourcedir)

def retrieve_issue_ids(sourcedir:str):

    bashcommand = "hub issue -f \"%I+\""
    processoutput = subprocess.run(bashcommand.split(), cwd=sourcedir, capture_output=True, text=True)

    issueoutput = processoutput.stdout
    issueoutput = issueoutput.replace('+', "\n")
    issueoutput = issueoutput.replace('"', "")

    return issueoutput

def retrieve_all_issues(sourcedir:str):

    bashcommand = "hub issue -f \"%I|%U|%S|%t|%L|%as|%b+\""
    #print(bashcommand)
    processoutput = subprocess.run(bashcommand.split(), cwd=sourcedir, capture_output=True, text=True)
    
    issueoutput = processoutput.stdout
    issueoutput = issueoutput.replace('"', "")

    issuelist = issueoutput.split("+")

    processedlist = []
    for issuestring in issuelist:
        issuestring = issuestring.replace("\n", "+")
        issuefields = issuestring.split("|")
        numberfields = len(issuefields)
        #print(str(numberfields) + " fields in string:")

        if numberfields >= 7:
            body = issuefields[6]
            #print(body)
            m = re.match(r".*Region\+\+(\S+:([\d,]+)\-([\d,]+)).*", body)
            mreg = re.match(r".*\+(\S+:([\d,]+)\-([\d,]+))\+.*", body)
            msingle = re.match(r".*\+(\S+):([\d,]+)\+.*", body)
            if m:
                region = m.group(1)
                region = region.replace(",", "")
                start = m.group(2).replace(",", "")
                end = m.group(3).replace(",", "")
                size = int(end) - int(start) + 1
            elif mreg:
                region = mreg.group(1)
                region = region.replace(",", "")
                start = mreg.group(2).replace(",", "")
                end = mreg.group(3).replace(",", "")
                size = int(end) - int(start) + 1
            elif msingle:
                chrom = msingle.group(1)
                pos = msingle.group(2).replace(",", "")
                region = chrom + ":" + pos + "-" + pos
                size = 1
            else:
                region = "unparsable"
                size = "unknown"

            # fields parsed from labels:
            labels = issuefields[4].split(", ")
            centrotags = []
            covgtags = []
            evidencetags = []
            nuctags = []
            errortags = []
            cliptags = []
            programtags = []
            diagnosistags = []

            for label in labels:
                if label == "alpha_sat" or re.match(r"hsat.*", label):
                    centrotags.append(label)
                elif re.match(r".*_cov_.*", label):
                    covgtags.append(label)
                elif re.match(r".*evidence", label):
                    evidencetags.append(label)
                elif re.match(r"^[atgc_]+$", label):
                    nuctags.append(label)
                elif label == "clipped":
                    cliptags.append(label)
                elif label == "error_kmer":
                    errortags.append(label)
                elif label == "coverage_pri":
                    programtags.append(label)
                elif label == "flagger_intersect":
                    programtags.append(label)
                elif label == "merqury":
                    programtags.append(label)
                elif label == "phase_switch":
                    programtags.append(label)
                elif label == "priority":
                    diagnosistags.append(label)
                elif label == "false_positive":
                    diagnosistags.append(label)
                elif label == "help_wanted":
                    diagnosistags.append(label)

            if len(centrotags) > 0:
                centromere = ",".join(centrotags)
            else:
                centromere = "no"

            if len(covgtags) > 0:
                coverage = ",".join(covgtags)
            else:
                coverage = "unflagged"

            if len(evidencetags) > 0:
                evidence = ",".join(evidencetags)
            else:
                evidence = "none"

            if len(nuctags) > 0:
                content = ",".join(nuctags)
            else:
                content = "unflagged"

            if len(programtags) > 0:
                programs = ",".join(programtags)
            else:
                programs = "none"

            if len(cliptags) > 0:
                clipped = "yes"
            else:
                clipped = "no"

            if len(errortags) > 0:
                errors = ",".join(errortags)
            else:
                errors = "no"

            if len(diagnosistags) > 0:
                diagnosis = ",".join(diagnosistags)
            else:
                diagnosis = "none"

            if len(issuefields[5]) != 0:
                assignedto = issuefields[5]
                assignedto = assignedto.replace(' ', '')
            else:
                assignedto = "unassigned"

            issuedict = {"issueid":issuefields[0],
                         "url":issuefields[1],
                         "status":issuefields[2],
                         "name":issuefields[3],
                         "labels":labels,
                         "assignedto":assignedto,
                         "region":region,
                         "size":size,
                         "coverage":coverage,
                         "evidence":evidence,
                         "centromere":centromere,
                         "clipped":clipped,
                         "errors":errors,
                         "content":content,
                         "programs":programs,
                         "diagnosis":diagnosis
                         }

            processedlist.append(issuedict) 

    return processedlist

def create_new_issue(sourcedir:str, name:str, comment:str, labels:list)->int:

    [handle, tmpfile] = tempfile.mkstemp()
    with os.fdopen(handle, "w") as fh:
        fh.write(name + "\n\n" + comment)

    labelstring = ",".join(labels)
    bashcommand = "hub issue create --file " + tmpfile + " -l " + labelstring
    processoutput = subprocess.run(bashcommand.split(), cwd=sourcedir, capture_output=True, text=True)
    print(processoutput)

    os.remove(tmpfile)

    m = re.match(r"https:.*/([0-9]+)$", processoutput.stdout)
    if m:
        return int(m.group(1))
    else:
        return -1

def replace_labels_for_issue(sourcedir:str, issueid:str, newlabels:list)->int:

    labelstring = ",".join(newlabels)
    bashcommand = "hub issue update " + issueid + " -l " + labelstring
    processoutput = subprocess.run(bashcommand.split(), cwd=sourcedir, capture_output=True, text=True)

    return str(processoutput)

def replace_assignees_for_issue(sourcedir:str, issueid:str, username:str)->int:

    bashcommand = "hub issue update " + issueid + " --assign " + username
    processoutput = subprocess.run(bashcommand.split(), cwd=sourcedir, capture_output=True, text=True)

    return str(processoutput)
