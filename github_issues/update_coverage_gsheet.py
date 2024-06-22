import six
import gspread
import sys
import re
import time
import argparse

from github_issues import callhub

gsheet_columns = {'IssueID':'issueid', 'GithubURL':'url', 'Curator':'assignedto', 'Region':'region', 'Name':'name', 'EvidenceTags':'evidence', 'Status':'status',
                  'Coverage':'coverage', 'Centromere':'centromere', 'Content':'content', 'Errors':'errors', 'Clipped':'clipped', 'FlaggedBy':'programs', 'Diagnosis':'diagnosis'}
                      
def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        usage="%(prog)s [OPTION] [FILE]...",
        description="Retrieve all issues from a github repository and update the associated google spreadsheet"
    )
    parser.add_argument(
        "-v", "--version", action="version",
        version = f"{parser.prog} version 1.0.0"
    )
    parser.add_argument('-o', '--output', type=str, metavar='file to which to write issue data', default=None, required=False)
    parser.add_argument('-s', '--source', type=str, metavar='directory of checkout of source github repository', required=True)

    return parser

def main() -> None:
    parser = init_argparse()
    args = parser.parse_args()

    checkoutdir = args.source

    allissues = callhub.retrieve_all_issues(checkoutdir)
    github_issues = {}
    for issue in allissues:
        programs = issue["programs"]
        coveragematch = re.match(r'.*coverage_pri.*', programs)
        if coveragematch is None:
            continue
        issueid = issue["issueid"]
        github_issues[issueid] = issue

    # retrieve spreadsheet data:
    sa = gspread.service_account()
    sh = sa.open("HG002 Coverage Polishing Issues")
    wks = sh.worksheet("Sheet1")
    allsheetrows = wks.get_all_records()

    # keep track of which issues are already in the spreadsheet
    seen = {}
    rowid = 1
    headers = wks.row_values(1)
    headervars = list()
    for header in headers:
        if header in gsheet_columns.keys():
            headervars.append(gsheet_columns[header])
        else:
            headervars.append('None')
    for row in allsheetrows: # log issues that are already in the Google spreadsheet:
        rowid = rowid + 1
        rowAissueid = str(row["IssueID"])
        url = str(row["GithubURL"])
        idmatch = re.search(r'.*/(\d+)', url)
        if idmatch is None:
            print("Couldn\'t parse " + url)
            continue
        issueid = idmatch.group(1)
        #print("Examining issue id " + issueid)
        if rowAissueid != issueid:
            print("Column A " + rowAissueid + " is not equal to URL derived " + issueid)
        seen[issueid] = True # dictionary key is a string

        githubval = {}
        gsheetval = {}
        if issueid in github_issues.keys():
            for header in headers:
                githubval[header] = github_issues[issueid][gsheet_columns[header]]
                gsheetval[header] = str(row[header])
                if githubval[header] != gsheetval[header]:
                    print("Issue " + str(issueid) + " has the wrong " + header + " values " + githubval[header] + "/" + gsheetval[header])
                    colid = headervars.index(gsheet_columns[header])
                    wks.update_cell(rowid, colid+1, githubval[header])
                    time.sleep(10)
             
    # look for new issues to put in the spreadsheet
    for githubissueid in sorted(github_issues.keys()):
        githubissueid = str(githubissueid)
        if githubissueid not in seen:
            #time.sleep(10)
            newrow = []
            #for header in headers:
                #if header in gsheet_columns.keys():
                    #newrow.append(github_issues[githubissueid][gsheet_columns[header]])
                #else:
                    #newrow.append('')
            print("Issue " + githubissueid + " not in spreadsheet!")
            #wks.append_row(newrow)

if __name__ == '__main__':
    main()
