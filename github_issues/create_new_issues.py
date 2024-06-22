import gspread
import subprocess
import sys
import os
import re
import time
import argparse

from github_issues import callhub

# defaults
defaultassemblyversion = "v0.7"
defaultsleeptime = 20
censat_bedfile = "/data/Phillippy/projects/HG002_diploid/annotation/browsertracks/HG002v0.7_censat.9col.bed"

issue_directory = os.getcwd()

# sleep time to avoid github blocking:

def read_issue_vcffile(issue_file: str) -> list:
    issue_vcfrecord = {}
    region_list = []

    with open(issue_file, 'r') as fh_issues:
        for line in fh_issues:
            fields = line.split("\t")
            chrom = fields[0]
            if chrom[0] == "#":
                continue
            # region boundaries are strings, *not* zero-based
            regionstart = fields[1]
            regionend = str(int(fields[1]) + len(fields[3]) - 1)
            ref = fields[3]
            alt = fields[4]

            regionstring = chrom + ":" + regionstart + "-" + regionend
            if regionstring not in issue_vcfrecord.keys():
                issue_vcfrecord[regionstring] = line
                region_list.append(regionstring)
    
    return [issue_vcfrecord, region_list]

def check_region_list(all_regions: list, checkoutdir: str) -> None:

    currentissueregions = {}
    currentissues = callhub.retrieve_all_issues(checkoutdir)
    for issue in currentissues:
        issueregion = issue["region"]
        m = re.match(r"(\S+):(\d+)\-(\d+)", issueregion)
        if not m:
            print("Can\'t parse existing issue region: " + issueregion)
            continue
        else:
            chrom = m.group(1)
            start = int(m.group(2)) 
            end = int(m.group(3)) 
            print("Issue region: " + issueregion)
            if chrom not in currentissueregions.keys():
                currentissueregions[chrom] = []
            currentissueregions[chrom].append([start, end])

    for regionstring in all_regions:
        m = re.match(r"(\S+):(\d+)\-(\d+)", regionstring)
        if not m:
            print("Can\'t parse VCF region: " + regionstring)
            exit(1)
        chrom = m.group(1)
        start = int(m.group(2)) 
        end = int(m.group(3)) 
        # New issue region chr14_MATERNAL:81767103-81767104 overlaps with existing issue chr14_MATERNAL:85121934-85123552
        for limits in currentissueregions[chrom]:
            if not (start > limits[1] or end < limits[0]):
                print("New issue region " + regionstring + " overlaps with existing issue " + chrom + ":" + str(limits[0]) + "-" + str(limits[1]))
                exit(1)

def read_censat_annotations(centro_file: str, all_regions: list) -> dict:
    centro_regions = {}

    # read in censat annotations:
    with open(centro_file, 'r') as fh_annots:
        for line in fh_annots:
            line = line.replace("\n", "")
            fields = line.split("\t")
            if len(fields) < 4:
                continue 
            chrom = fields[0]
            regionstart = int(fields[1]) + 1
            regionend = int(fields[2])
            annot = fields[3]

            if annot not in centro_regions.keys():
                centro_regions[annot] = {}
            if chrom not in centro_regions[annot].keys():
                centro_regions[annot][chrom] = []
            centro_regions[annot][chrom].append([regionstart, regionend])

    region_labels = {}
    for regionstring in all_regions:
        m = re.match(r"(\S+):(\d+)\-(\d+)", regionstring)
        if not m:
            print("Can\'t parse censat region: " + regionstring + " from file " + centro_file)
            exit(1)
        chrom = m.group(1)
        start = int(m.group(2)) 
        end = int(m.group(3)) 

        for annot in centro_regions.keys(): 
            lc_annot = annot
            if annot=="HSat2" or annot=="HSat3":
                lc_annot = annot.replace("HS", "hs")
            if annot=="alphasat":
                lc_annot = "alpha_sat"

            if chrom not in centro_regions[annot].keys():
                continue
            for limits in centro_regions[annot][chrom]:
                if not (start > limits[1] or end < limits[0]):
                    if regionstring not in region_labels.keys():
                        region_labels[regionstring] = {}
                    region_labels[regionstring][lc_annot] = True
                if end < limits[0]:
                    break

    return region_labels

def padded_region(regionstring: str):
    m = re.search(r'(\S+)\:(\d+)\-(\d+)', regionstring)
    [chrom, start, end] = m.groups()
    chrom = chrom.replace("chrX", "chr23")
    chrom = chrom.replace("chrY", "chr24")
    chrom = chrom.replace("chrM", "chr25_MATERNAL")
    chrom = chrom.replace("chrEBV", "chr26_PATERNAL")

    return chrom.zfill(50) + start.zfill(12) + end.zfill(12)

def create_github_issue(issuevcfline: dict, centrodict: dict, region: str, issuetypetags: list, githubdir: str, dryrun: bool, version: str) -> int:
    name = "Issue: " + region
    centrotags = list(centrodict.keys())
    all_labels = issuetypetags + centrotags

    issuecomment = "### Assembly Region\n\n" + region + "\n\n" + "### Assembly Version\n\n" + version + "\n\n" + "### DeepVariant Call\n\n" + issuevcfline + "\n\n"
      
    labelstring = ' '.join(all_labels)

    if dryrun:
        print(issuecomment + labelstring) 
    else:
        issueid = callhub.create_new_issue(githubdir, name, issuecomment, all_labels)
        if issueid == -1:
            print("Something went wrong creating issue " + name)
            exit(1)
        else:
            print("Created issue with id " + str(issueid))

def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        usage="%(prog)s [OPTION] [VCF FILE]...",
        description="Load new issues from a VCF file to github"
    )
    parser.add_argument(
        "-v", "--version", action="version",
        version = f"{parser.prog} version 1.0.0"
    )
    parser.add_argument('vcffile', type=str, metavar='VCF file with issues to add')
    parser.add_argument('-s', '--source', type=str, metavar='directory of checkout of source github repository', required=True)
    parser.add_argument('-a', '--assembly', type=str, default=defaultassemblyversion, metavar='assembly version', required=False)
    parser.add_argument('-d', '--dryrun', action='store_true', help='just print info about issue--dont actually create it')
    parser.add_argument('-w', '--wait', type=int, default=defaultsleeptime, help='number of seconds to wait after creating an issue', required=False)
    parser.add_argument('-l', '--labels', type=str, default="", help='comma-delimited string of labels to apply to all issues', required=False)

    return parser

def main() -> None:
    parser = init_argparse()
    args = parser.parse_args()
 
    vcffile = args.vcffile
    checkoutdir = args.source
    dryrun = args.dryrun
    version = args.assembly
    sleeptime = args.wait
    labels = args.labels.split(',')

    [vcfline_dict, region_list] = read_issue_vcffile(vcffile)
    check_region_list(region_list, checkoutdir) 
    censat_dict = read_censat_annotations(censat_bedfile, region_list)

    region_list.sort(key=padded_region)

    for region in region_list:
        if region in censat_dict.keys():
            censatdict = censat_dict[region]
        else:
            censatdict = {}
        create_github_issue(vcfline_dict[region], censatdict, region, labels, checkoutdir, dryrun, version)
        if not dryrun:
            time.sleep(sleeptime)

if __name__ == '__main__':
    main()
