#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import plac
import codecs
import re
from collections import defaultdict
from itertools import izip

import logging
logging.basicConfig(format='%(asctime)s [%(process)d] [%(levelname)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)



def convert_alignment(a):
    return map(lambda x: tuple(map(lambda y: int(y), x.split('-'))), a.split())

def postclean(text):
    return text.replace(u'\u200b', '')

def whitespace_tokenizer(text):
    return re.sub(r'\s+', ' ', postclean(text)).split()

def phrase_extraction(srctext, trgtext, alignment):
    srctext = srctext.split()
    trgtext = trgtext.split()
    srclen = len(srctext)
    trglen = len(trgtext)

    if not isinstance(alignment, list):
        alignment = convert_alignment(alignment)    

    # Hack
    e_maps = defaultdict(set)
    i_, j_ = 0, 0
    for i, j in alignment:
        e_maps[min([i_, i])].add(max(j_, j))
        if i_ + 1 != i:
            i_, j_ = i, j

    e_aligned = [i for i, _ in alignment]
    f_aligned = [j for _, j in alignment]

    for e_start in e_maps.keys():
        e_end = max(e_maps[e_start])
        f_start = trglen-1
        f_end = -1
        for e, f in alignment:
            if e_start <= e <= e_end:
                f_start = min(f, f_start)
                f_end = max(f, f_end)

        if f_end < 0:
            break

        for e, f in alignment:
            if ((f_start <= f <= f_end) and (e < e_start or e > e_end)):
                break

        fs = f_start
        while True:
            fe = f_end
            while True:
                try:
                    src_phrase = " ".join(srctext[i] for i in range(e_start, e_end+1))
                    trg_phrase = " ".join(trgtext[i] for i in range(fs, fe+1))
                    yield (src_phrase, trg_phrase)
                except:
                    pass

                fe += 1
                if fe in f_aligned or fe == trglen:
                    break
            fs -=1 
            if fs in f_aligned or fs < 0:
                break


@plac.annotations(
    input_file=plac.Annotation("Input file", 'option', 's', str),
    alignment_file=plac.Annotation("Alignment file", 'option', 'a', str),
    output_file=plac.Annotation("Output file", 'option', 'o', str),
    max_ngram=plac.Annotation("Max N-gram length", 'option', 'm', int)
)
def main(input_file, alignment_file, output_file, max_ngram=10):
    assert input_file and alignment_file and output_file, 'missing arguments'
    with codecs.open(output_file, 'w', 'utf-8') as out, \
        codecs.open(input_file, 'r', 'utf-8') as input_f, \
        codecs.open(alignment_file, 'r', 'utf-8') as alignment_f:
        for pair, alignment in izip(input_f, alignment_f):
            source, target = pair.split(' ||| ')

            for a, b in phrase_extraction(source, target, alignment):
                a, b = whitespace_tokenizer(a), whitespace_tokenizer(b)
                if 1 <= len(a) <= max_ngram and 1 <= len(b) <= max_ngram:
                    out.write('{0} ||| {1}\n'.format(' '.join(a), ' '.join(b)))

    logging.info((output_file))

if __name__ == '__main__':
    plac.call(main)
