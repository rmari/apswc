#!/opt/local/bin/python

import sys
import string
import re
import subprocess
import Image
import pyPdf

usage = '''
Usage:
apswc latex_file

'''

def init():
    if len(sys.argv) != 2:
        sys.stderr.write(usage)
        exit(1)
    in_file = open(sys.argv[1], 'r')
    return in_file


def getIncludedTex(line):
    fname = line[line.find('{')+1:line.find('}')]+'.tex'
    print "Including ", fname, "in the word count"
    return open(fname, 'r')

def getPDFAspectRatio(fname):
    pdf = pyPdf.PdfFileReader(open(fname, 'rb'))
    page = pdf.getPage(0)
    width, height = page.mediaBox[2], page.mediaBox[3]
    aspect_ratio = width/float(height)
    return aspect_ratio

def getImageAspectRatio(fname):
    img = Image.open(open(fname, 'rb'))
    width, height= img.size
    aspect_ratio = width / float(height)
    return aspect_ratio



def wcFig(line):
    for key in figinc_keywords:
        if line.find(key) != -1:
            fname = line[line.find('{')+1:line.find('}')]
            if line.find('\\columnwidth') != -1:
                width_factor = 150
                width_offset = 20
            if line.find('\\textwidth') != -1:
                width_factor = 600
                width_offset = 40

            if fname.rfind('.pdf') == len(fname)-4:
                aspect = getPDFAspectRatio(fname)
            else:
                aspect = getImageAspectRatio(fname)
                
            wc= int(width_factor/aspect + width_offset)
            print "Figure: ", fname, ", Aspect Ratio: ",aspect, ", Word Count: ", wc

            return wc
        
    return 0

def wcText(line):
    wc = len(re.findall(r'\w+', line))
#    print wc, line
    return wc 

def wcBiblio(line):
    return 0 

def wcEquation(line):
    return 0


def cleanLine(line):
    max_pos = -1
    for key in excluded_keywords:
        if line.find(key) > max_pos: 
            max_pos = line.find(key)

    return line[:max_pos]
    

    

beg='\\begin'
end='\\end'

excluded_keywords = ['%','\\maketitle', '\\title', '\\author', '\\affiliation', '\\date', '\\pacs', '\\bibliography', beg+'{abstract}', end+'{abstract}', end+'{document}']
biblio_keywords = [beg+'{thebibliography}', end+'{thebibliography}']
texinc_keywords = ['\\input', '\\include{']
figinc_keywords = ['\\includegraphics']


env_wc_dict = dict()
env_wc_dict['thebibliography'] = wcBiblio
env_wc_dict['figure'] = wcFig
env_wc_dict['figure*'] = wcFig
env_wc_dict['text'] = wcText
env_wc_dict['equation'] = wcEquation

in_file = init()
tex_files = [ in_file ]

in_doc=False
environment = 'text'
total_wc = 0

for tfile in tex_files:
    for line in tfile:

        # remove as much as possible uncounted parts of the .tex
        cleaned_line = cleanLine(line)


        # check if we passed \begin{document}
        if cleaned_line.find(beg+'{document}') != -1:
            in_doc = True

        if in_doc:
            
            # if an include/input is encountered, add the .tex to the analysis, and remove the input/include
            for key in texinc_keywords:
                if cleaned_line.find(key) != -1:
                    tex_files.append(getIncludedTex(cleaned_line))
                    cleaned_line = cleaned_line[0:cleaned_line.find(key)]

            # check environment switches
            for env in env_wc_dict:

                if cleaned_line.find(beg+'{'+env+'}') != -1:
                    environment = env
                if cleaned_line.find(end+'{'+env+'}') != -1:
                    environment = 'text'

            total_wc += env_wc_dict[environment](cleaned_line)


print "Total Word Count: ", total_wc
