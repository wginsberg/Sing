#!/usr/bin/env python

import sys
import os
import requests
from copy import deepcopy
from cStringIO import StringIO
from subprocess import call

import numpy as np
from lxml import etree
from scipy.io import wavfile


SCORE = [
	[0, 1.0],
	[7, 0.5],
	[4, 0.5],
	[4, 1.0],
	[2, 0.5],
	[0, 0.5],
	[0, 0.5],
	[5, 1.0],
	[4, 0.5],
	[4, 0.5],
	[2, 0.5],
	[2, 0.5],
	[0, 0.5]
]


def get_allophones(text):
	'''
	Hit MaryTTS server to get allophone structure of text (XML)
	Input:
		text - A string to analyze
	Output:
		XML string describing the text's allophones
	'''

	args = {
		'INPUT_TEXT': text,
		'INPUT_TYPE':'TEXT',
		'OUTPUT_TYPE':'ALLOPHONES',
		'LOCALE':'en_US'
	}

	url = "http://localhost:59125/process"
	response = requests.get(url, params=args)

	return response.content

def get_audio(phonemes):
	'''
	Hit MaryTTS server to get speech from phonemes
	Input:
		phonemes - in XML format
	Output:
		WAV data
	'''

	args = {
		'INPUT_TEXT': phonemes,
		'INPUT_TYPE':'PHONEMES',
		'OUTPUT_TYPE':'AUDIO',
		'AUDIO':'WAVE_FILE',
		'LOCALE':'en_US'
	}

	url = "http://localhost:59125/process"
	response = requests.get(url, params=args)

	return response.content

def get_line_tree(leaf):
	'''
	Modify an XML tree to remove all but one leaf
	Input:
		leaf - XML node
	Output:
		Modifies the tree of the given leaf, returning an XML node such that
			1) it is the root of the tree containg the given leaf
			2) the only leaf is the given one
	'''

	parent = leaf.getparent()

	if parent is None:
		return leaf

	for sibling in parent:
		if sibling != leaf:
			parent.remove(sibling)

	return get_line_tree(parent)

def get_isolated_trees(root, element="syllable", namespace="http://mary.dfki.de/2002/MaryXML"):
	'''
	Returns a new XML tree for each syllable node in the given tree such that each tree has only one syllable
	'''

	xquery = './/{%s}%s' % (namespace, element)
	syllables = root.findall(xquery)
	for i in range(len(syllables)):
		root_copy = deepcopy(root)
		syllable = root_copy.findall(xquery)[i]
		yield get_line_tree(syllable)

def make_samples(lyrics):
	'''
	Write out a WAV file for each syllable in the supplied lyrics
	'''

	allophones = get_allophones(lyrics)
	root = etree.fromstring(allophones)
	trees = list(get_isolated_trees(root))
	for i in range(len(trees)):
		audio = get_audio(etree.tostring(trees[i]))
		yield audio


def main():

	FNULL = open(os.devnull, 'w')

	lyrics = "Somebody once told me the world was gonna roll me. I ain't the sharpest tool in the shed."
	
	notes = []
	for i, sample in enumerate(make_samples(lyrics)):
		
		raw_sample_file = 'sample_{}.wav'.format(chr(65+i))
		with open(raw_sample_file, 'w') as fout:
			fout.write(sample)

		sung_sample_file = 'sung_{}.wav'.format(chr(65+i))
		beat = min(i, len(SCORE) - 1)
		call(['rubberband', '-t', str(SCORE[beat][1]), '-p', str(SCORE[beat][0]), raw_sample_file, sung_sample_file], stderr=FNULL)

		notes.append(sung_sample_file)

	call(['sox'] + notes + ['song.wav'])

if __name__ == "__main__":
	main()