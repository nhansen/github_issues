import subprocess
import sys
import os
import re
import time
import argparse

from github_issues import callhub

# defaults
defaultassemblyversion = "v1.0"

def retrieve_issues(checkoutdir: str, assembly: str, labels: str) -> None:

    regiondict = {}
    currentissues = callhub.retrieve_all_issues(checkoutdir)
    for issue in currentissues:
        skip = False
        #print("Desired labels: " + labels)
        issuelabels = issue["labels"]
        for label in labels.split(","):
            if label not in issuelabels:
                skip = True

        if not skip:
            issuename = issue["name"]
            issueid = issue["issueid"]
            issueregion = issue["region"]
            m = re.match(r"(\S+):(\d+)\-(\d+)", issueregion)
            if not m:
                print("Can\'t parse existing issue region: " + issueregion)
                continue
            else:
                regiondict[issueregion] = {"issuename":issuename, "issueid":issueid}

    return regiondict

def padded_region(regionstring: str):
    m = re.search(r'(\S+)\:(\d+)\-(\d+)', regionstring)
    [chrom, start, end] = m.groups()
    chrom = chrom.replace("chrX", "chr23")
    chrom = chrom.replace("chrY", "chr24")
    chrom = chrom.replace("chrM", "chr25_MATERNAL")
    chrom = chrom.replace("chrEBV", "chr26_PATERNAL")

    return chrom.zfill(50) + start.zfill(12) + end.zfill(12)

def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        usage="%(prog)s [OPTION] ...",
        description="Retrieve issues for a repo from github and print a BED file"
    )
    parser.add_argument(
        "-v", "--version", action="version",
        version = f"{parser.prog} version 1.0.0"
    )
    parser.add_argument('-s', '--source', type=str, metavar='directory of checkout of source github repository', required=True)
    parser.add_argument('-a', '--assembly', type=str, default=defaultassemblyversion, metavar='assembly version', required=False)
    parser.add_argument('-l', '--labels', type=str, default="", help='required labels, comma-delimited, to filter issues', required=False)

    return parser

def main() -> None:
    parser = init_argparse()
    args = parser.parse_args()
 
    checkoutdir = args.source
    version = args.assembly
    labels = args.labels

    region_dict = retrieve_issues(checkoutdir, version, labels) 
    region_keys = list(region_dict.keys())

    region_keys.sort(key=padded_region)

    for region in region_keys:
        m = re.search(r'(\S+)\:(\d+)\-(\d+)', region)
        [chrom, start, end] = m.groups()
        start = str(int(start) - 1)
        issuename = region_dict[region]["issuename"]
        issueid = region_dict[region]["issueid"]
        print(chrom + "\t" + start + "\t" + end + "\t" + issuename + "\t1000\t+\t" + start + "\t" + end + "\t0,0,100\t" + issuename + "\t" + "<a href=\"https://github.com/marbl/HG002-issues/issues/" + issueid + "\">https://github.com/marbl/HG002-issues/issues/" + issueid + "</a>" )

if __name__ == '__main__':
    main()
