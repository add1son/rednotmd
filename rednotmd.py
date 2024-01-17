# -*- coding: utf-8 -*-
"""
Python 3.9 on Windows 10
"""

from pathlib import Path


## script configuration

df = './input-rednotebook-copy/'
dout = './output/'
silent = False # ask for confirmations



## configure txt2tags
import txt2tagsmw as t2t

t2tcfg = {'target': 'md',
          'preproc': '',
          'enum-title': '',
          'toc': False}



def parserednotfile(pf):
    """
    Initial parse of a single RedNoteBook file (month containing several dates)

    Parameters
    ----------
    pf : pathlib.Path or str
        Filename with path.

    Returns
    -------
    dict
        Dictionary containing all date blocks in the file.

    """
    # print()
    # print(pf)
    # print('>>>', end=' ')
    with open(pf, 'r', encoding='utf8') as fin:
        prevtyp = 0
        blks = []
        blkdescrs = [None] # first block is a 'null' block
        blk = []
        for ln in fin:
            # print(len(ln))
            
            # check that all lines read have 'reproducible' behavior
            assert len(ln) > 0, 'zero line length detected'
            assert ord(ln[-1])==10, 'no terminating LF in line'
            ln = ln[:-1] # strip terminating LF
            
            if len(ln)==0:
                blk.append(ln) # do not throw away empty lines
            else:
                if not (ln[0]==" " or ln[0]=="'"):
                    blks.append(blk) # add last block before beginning new
                    
                    lnml = ln.split(':', maxsplit = 1)
                    # for lnm in lnml:
                    #     print('>>>>', lnm)
                    # print(int(lnml[0]), end =', ') # day of month
                    blkdescrs.append(fp.stem+'-'+'{0:02d}'.format(int(lnml[0])))
                    
                    lnm1strip = lnml[1].lstrip()
                    if len(lnm1strip) > 0:
                        assert lnm1strip[0] == '{', 'does not start with "{"'
                        # print('**************TYPE 1***************')
                        if prevtyp == 2:
                            # print('!!!! TYPE CHANGE WITHIN SAME FILE')
                            prevtyp = 1
                    else:
                        # print('**************TYPE 2***************')
                        if prevtyp == 1:
                            #  print('!!!! TYPE CHANGE WITHIN SAME FILE')
                            prevtyp = 2
                    # start new block
                    if len(lnm1strip)>0:
                        blk=[lnm1strip]
                    else:
                        blk=[]
                else:
                    blk.append(ln.lstrip())
   
    # print('LAST TYPE = ', prevtyp)
    
    blks.append(blk)
    return dict(zip(blkdescrs[1:], blks[1:]))



class RawBlock:
    def __init__(self, blkdescr, blktype, blkhead, blklns):
        self.descr = blkdescr
        self.blktype = blktype
        self.head = blkhead
        self.data = blklns


def proc_blktype1(blklns):
    """
    Process a raw single-date RedNoteBook block of type 1

    Parameters
    ----------
    blklns : list of str
        Raw line data.

    Raises
    ------
    NotImplementedError
        This will be raised if unexpected characters/codes
        show up.

    Returns
    -------
    list of str
        Processed/parsed line data.

    """
    # trim end of block
    if blklns[-1].endswith("'}"):
        blklns[-1] = blklns[-1][:-2] # strip end
    elif blklns[-1].endswith("'"):
        blklns[-1] = blklns[-1][:-1] # strip end
    elif blklns[-1].endswith(': null}'): # this is a quick hack, we may lose data
        print('nullend detected: ', blklns[-1])    
        blklns[-1] = blklns[-1][:-7]
    else:
        print(blklns[-1])
        raise NotImplementedError('blktype 1: unrecognized ending for last line')
    if len(blklns[-1])==0:
        blklns=blklns[:-1] # strip line if empty
    
    newblklns = []
    st = 1
    for ln in blklns:
        if st == 1:
            if len(ln) > 0:
                xln = ln+' ' # start new line
                st = 2
            else:
                newblklns.append('') # insert empty line
        elif st == 2:
            if len(ln) > 0:
                xln += ln+' ' # continue line
            else:
                # store line
                #    strip last space
                #    do 'escape code' processing
                xxln = xln[:-1].replace("''", "'")
                newblklns.append(xxln) 
                st = 1

    return newblklns


def proc_blktype2(blklns):
    """
    Process a raw single-date RedNoteBook block of type 2   

    Parameters
    ----------
    blklns : list of str
        Raw line data.

    Raises
    ------
    NotImplementedError
        This will be raised if unexpected characters/codes
        show up.
    ValueError
        Unimplemented escape code. We need to precisely know all escape codes
        used, and have suitable translations for each of them.

    Returns
    -------
    newblklns : TYPE
        DESCRIPTION.

    """
                                        
    if blklns[-1].endswith('"}'):
        blklns[-1] = blklns[-1][:-2] # strip end
    elif blklns[-1][-1]=='"':
        blklns[-1] = blklns[-1][:-1] # strip end
    elif blklns[-1].endswith(': null}'): # this is a quick hack, we may lose data
        print('nullend detected: ', blklns[-1])    
        blklns[-1] = blklns[-1][:-7]
    else:
        print(blklns[-1])
        raise NotImplementedError('blktype 2: unrecognized ending for last line')
        
    # stitch lines together 
    bigln = ''
    for ln in blklns:
        bigln += ln+' '
    bigln = bigln[:-1] # last space was one too many
    
    newblklns = []
    for ln in  bigln.split(r'\n'): # list of strings
        # decode escape sequences
        xln = ''
        escact = False # two-state machine
        for c in ln:
            if escact:
                if c == '\\':
                    oc = '\\'
                elif c == 't':
                    oc = '\t'
                elif c == 'f':
                    oc = ''
                elif c == 'r':
                    oc = ''
                elif c == '"':
                    oc = '"'
                elif c == ' ':
                    oc = ' '
                else:
                    # UNKNOWN ESCAPE CODE
                    print(ord(c))
                    raise ValueError('\\'+c+'   UNKNOWN')
                    oc = ''
                escact = False
            else:
                if c == '\\':
                    oc = ''
                    escact = True
                else:
                    oc = c
            xln += oc
        newblklns.append(xln)
    return newblklns
    

    
def blockprocess(blkdescr, blkdata):
    # print('{:s}\t{:3d}'.format(blkdescr, len(blkdata)), end='\t\t')
    blkhead = []
    blklns = []
    blktype = -1
    inheader = True
    for ln in blkdata:
        if inheader:
            if (ln.count("text: '") > 0):
                blktype = 1
                # fix blktype 1 header
                lnelem = ln.split("text: '")
                assert len(lnelem) == 2, 'not implemented'
                blkhead.append(lnelem[0])
                blklns.append(lnelem[1])
                inheader = False
            elif (ln.count('text: "') > 0):
                blktype = 2
                lnelem = ln.split('text: "')
                assert len(lnelem) == 2, 'not implemented'
                blkhead.append(lnelem[0])
                blklns.append(lnelem[1])
                inheader = False
            elif (ln.count('{text: ') > 0):
                blktype = 3
                lnelem = ln.split('{text: ')
                assert len(lnelem) == 2, 'not implemented'
                blkhead.append(lnelem[0])
                blklns.append(lnelem[1])
                inheader = False
            else:
                inheader = True # still in header (reconfirm for clarity)
                blkhead.append(ln)
        else:
            assert ln.count('text: ')==0, 'not implemented (but probably not a problem)'
            blklns.append(ln)
            
    # remove initial '{' in header lines
    # remove empty header lines
    newblkhead = []
    for ln in blkhead:
        sln = ln.strip()
        if len(sln)>0:
            if sln[0]=='{':
                sln = sln[1:]
            if len(sln) > 0:
                sln = sln.replace(': null','')
                if sln[-1]==',':
                    sln = sln[:-1]
        if not sln=='':
            newblkhead.append(sln)
    blkhead = newblkhead
     
    # detect empty ill-formatted blocks
    if len(blklns)==0:
        print('badblock detected: ', blkdescr)
        blktype = 666 # bad block
       
    if blktype <= 0:
        print(blkdescr, blktype, len(blkhead), len(blklns))
        raise ValueError('unrecognized block type')
     
    # post process different block types
    if blktype == 1:
        blklns = proc_blktype1(blklns)
    elif blktype == 2:
        blklns = proc_blktype2(blklns)
    elif blktype == 3:
        if blklns[-1][-1] == '}':
            blklns[-1] = blklns[-1][:-1] # strip end
        else:
            raise NotImplementedError()
        pass # for the rest, do nothing
    elif blktype == 666:
        pass
    else:
        raise ValueError('unknown blocktype')

    return RawBlock(blkdescr, blktype, blkhead, blklns)


def blockwrite(opf, rb):
    """
    Write a block to a file. WILL OVERWRITE.

    Parameters
    ----------
    opf : pathlib.Path or str
        File pathnamme.
    rb : RawBlock instance
        Block data.

    Returns
    -------
    None.

    """
    with open(opf, 'w',
              encoding='utf8',
              newline='\n') as f:
        f.write('# {:s}\n'.format(ofn))
        f.write('\n________________________________________\n\n')
        f.write('stamp    : '+rb.descr+'\n')
        # f.write('datestamp: '+rb.descr+'\n')
        f.write('blktype  : {0:1d}\n'.format(rb.blktype))
        f.write('keywords :\n')
        for hln in rb.head:
            f.write('    {:s}\n'.format(hln))
        f.write('\n________________________________________\n\n')
        
        # Let's try out txt2tags -> markdown here!
        t2tcnv, t2ttoc = t2t.convert(rb.data, t2tcfg)
        # toc is not used        
        for ln in t2tcnv:
            f.writelines(ln+'\n')        
    




## File walker/reader

inpath = Path(df)

fplist = [f for f in inpath.iterdir()]

# read files
# and first-step processing
allblks = []
for fp in fplist:
    if fp.is_file():
        if fp.suffix.lower()=='.txt':
            blkdic = parserednotfile(fp)
            allblks.append(blkdic)
            
            
# second-step processing
# scan all blocks, dissect, get header if any and discover type of block
#
# block type 1 => OK
# block type 2 => OK
# block type 3 => RAW OUTPUT (only 3 dates have this format)
#
rawblks = []
for blks in allblks:
    for blkdescr, blkdata in blks.items():
        rawblks.append(blockprocess(blkdescr, blkdata))



# create year, month subdirectories and write blocks to file
for rb in rawblks:
    # parse date in filename
    ofn = rb.descr.split(' ')[0] # split at first space
    assert len(ofn)==10, 'filename: unexpected length'
    oyr, omnth, oday = [int(oo) for oo in ofn.split('-')]
    if not ((1970 <= oyr <= 2100) \
            and (1 <= omnth <= 12) \
            and (1 <= oday <= 31)):
        print('file name : '+ofn)
        print('decoded as {:d} - {:d} - {:d}'.format(oyr, omnth, oday))
        raise ValueError('filename: unexpected decoded date')

    osubd = '{0:04d}/{0:04d}-{1:02d}'.format(oyr, omnth)
    ofn = 'mw{0:02d}{1:02d}{2:02d}'.format(oyr%100, omnth, oday)
    # print(osubd, ofn)

    # create subdirectory if needed by program and wanted by user
    op = Path(dout, osubd)
    if not(op.exists()):
        createdir = True
        if not silent:
            answer = ""
            while answer not in ["y", "n", "a"]:
                answer = input("Directory '{:s}' does not exist. "\
                    "Create? [Y]es [N]o [A]ll: ".format(str(op))).lower()
            if (answer=='y' or answer=='a'):
                silent =  answer=='a'
            else:
                createdir = False
        if createdir:
            op.mkdir(parents='True')
    if op.exists(): # need to check again: it may or may not have been created
        opf = Path(op, ofn+'.md')
        blockwrite(opf, rb)



