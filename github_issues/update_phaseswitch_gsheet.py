import six
import gspread
import sys
import re
import time
import argparse

from github_issues import callhub

gsheet_columns = {'IssueID':'issueid', 'GithubURL':'url', 'Curator':'assignedto', 'Region':'region', 'Name':'name', 'EvidenceTags':'evidence', 'Status':'status', 'Centromere':'centromere', 'FlaggedBy':'programs', 'Diagnosis':'diagnosis'}
                      
def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        usage="%(prog)s [OPTION] [FILE]...",
        description="Retrieve all phase switch issues from a github repository and update the associated google spreadsheet"
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
        phaseswitchmatch = re.match(r'.*phase_switch.*', programs)
        if phaseswitchmatch is None:
            continue
        issueid = issue["issueid"]
        github_issues[issueid] = issue

    # retrieve spreadsheet data:
    sa = gspread.service_account()
    sh = sa.open("HG002 Phase Switch Polishing Issues")
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
    for row in allsheetrows:
        rowid = rowid + 1
        issueid = str(row["IssueID"])
        seen[issueid] = True

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
        if githubissueid not in seen:
            time.sleep(10)
            newrow = []
            for header in headers:
                if header in gsheet_columns.keys():
                    newrow.append(github_issues[githubissueid][gsheet_columns[header]])
                else:
                    newrow.append('')
            wks.append_row(newrow)

if __name__ == '__main__':
    main()
