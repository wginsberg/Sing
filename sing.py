#!/usr/bin/env python

import sys
import os
import argparse
import requests
from copy import deepcopy
from cStringIO import StringIO
from subprocess import call
from lxml import etree

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
	[0, 1.0],
	[0, 0.5],
	[7, 0.5],
	[4, 0.5],
	[4, 0.5],
	[2, 0.5],
	[2, 0.5],
	[0, 0.5],
	[0, 0.5],
	[-3, 2.5]
]


def get_allophones(text, host, port):
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

	url = "http://{}:{}/process".format(host, port)
	response = requests.get(url, params=args)

	return response.content


def get_audio(phonemes, host, port):
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
		'LOCALE':'en_US'#,'VOICE':'cmu-bdl'
	}

	url = "http://{}:{}/process".format(host, port)
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


def make_samples(lyrics, host, port):
	'''
	Write out a WAV file for each syllable in the supplied lyrics
	'''

	allophones = get_allophones(lyrics, host, port)
	root = etree.fromstring(allophones)
	
	num_samples = 0
	for tree in get_isolated_trees(root):
		audio = get_audio(etree.tostring(tree), host, port)
		num_samples += 1
		yield audio
		if num_samples > len(SCORE):
			break

	while num_samples < len(SCORE):
		num_samples += 1
		yield audio


def main(args):

	FNULL = open(os.devnull, 'w')

	if args.lyrics:
		with open(args.lyrics) as f:
			lyrics = f.read()
	else:
		lyrics = sys.stdin.read()

	notes = []
	for i, sample in enumerate(make_samples(lyrics, args.host, args.port)):

		raw_sample_file = os.path.join(args.wip_dir, 'sample_{}.wav'.format(i))
		with open(raw_sample_file, 'w') as fout:
			fout.write(sample)

		trimmed_file = os.path.join(args.wip_dir, 'trimmed_{}.wav'.format(i))
		call(['sox', raw_sample_file, trimmed_file, 'silence', '1', '0.05', '1%', '-1', '0.05', '1%',])

		normalized_file = os.path.join(args.wip_dir, 'normalized_{}.wav'.format(i))
		call(['rubberband', '--duration', '0.6', trimmed_file, normalized_file], stderr=FNULL)

		sung_file = os.path.join(args.wip_dir, 'sung_{}.wav'.format(i))
		beat = min(i, len(SCORE) - 1)
		call(['rubberband', '-t', str(SCORE[beat][1]), '-p', str(SCORE[beat][0]), normalized_file, sung_file], stderr=FNULL)		

		notes.append(sung_file)

	raw_vocals = os.path.join(args.wip_dir, 'raw_vocals.wav')
	vocals = os.path.join(args.wip_dir, 'vocals.wav')
	call(['sox'] + notes + [raw_vocals])
	call(['rubberband', '-D', '9', raw_vocals, vocals])
	call(['sox', '-m', vocals, args.instrumental, args.destination])



parser = argparse.ArgumentParser()
parser.add_argument('--host', default="localhost", help='host of the MaryTTS server')
parser.add_argument('--port', default=59125, help='port of the MaryTTS server')
parser.add_argument('lyrics', nargs="?", help='path to the file containing song lyrics')
parser.add_argument('destination', nargs="?", default='song.wav', help='path to write the audio file')
parser.add_argument('--wip-dir', default='/tmp', help='where to write intermediate files')
parser.add_argument('--instrumental', default='instrumental.wav')

if __name__ == "__main__":
	args = parser.parse_args()
	main(args)