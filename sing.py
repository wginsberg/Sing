#!/usr/bin/env python

import sys
import os
import argparse
import requests
from copy import deepcopy
from cStringIO import StringIO
from subprocess import call
from lxml import etree

HOST='localhost'
PORT=59125

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


def get_allophones(text, host=None, port=None):
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

	url = "http://{}:{}/process".format(host or HOST, port or PORT)
	response = requests.get(url, params=args)

	return response.content


def get_audio(input_text, input_type, host=None, port=None):
	'''
	Hit MaryTTS server to get speech from phonemes
	Input:
		phonemes - in XML format
	Output:
		WAV data
	'''

	args = {
		'INPUT_TEXT': input_text,
		'INPUT_TYPE': input_type,
		'OUTPUT_TYPE':'AUDIO',
		'AUDIO':'WAVE_FILE',
		'LOCALE':'en_US'#,'VOICE':'cmu-bdl'
	}

	url = "http://{}:{}/process".format(host or HOST, port or PORT)
	response = requests.get(url, params=args)

	return response.content

def get_audio_phonemes(phonemes, host=None, port=None):
	return get_audio(phonemes, "PHONEMES", host, port)

def get_audio_text(text, host=None, port=None):
	return get_audio(text, "TEXT", host, port)

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


def get_samples(lyrics, host=None, port=None, long_word_indices=None):
	'''
	long_word_indices denotes where a single word should be sung as a note,
						otherwise each syllable is sung as its own note
	'''

	allophones = get_allophones(lyrics, host, port)

	with open('trace.xml', 'w') as f:
		f.write(allophones)

	root = etree.fromstring(allophones)

	count = 0
	for word in get_isolated_trees(root, element='t'):
		text = word.find('.//{http://mary.dfki.de/2002/MaryXML}t').text
		if text != '.':
			if count in (long_word_indices or []):
				yield get_audio_text(word.find('.//{http://mary.dfki.de/2002/MaryXML}t').text, host, port)
			else:
				for syllable in get_isolated_trees(word, element='syllable'):
					yield get_audio_phonemes(etree.tostring(syllable), host, port)
		count += 1


def make_singing(lyrics, host, port, long_word_indices=None):
	'''
	Write out a WAV file for each syllable in the supplied lyrics
	'''

	num_samples = 0
	for audio in get_samples(lyrics, host, port, long_word_indices):
		num_samples += 1
		yield audio
		if num_samples > len(SCORE):
			break

	# When in doubt - sing it out!
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
	for i, sample in enumerate(make_singing(lyrics, args.host, args.port, [5, 15])):

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
parser.add_argument('--lyrics', help='path to the file containing song lyrics')
parser.add_argument('destination', nargs="?", default='song.wav', help='path to write the audio file')
parser.add_argument('--wip-dir', default='/tmp', help='where to write intermediate files')
parser.add_argument('--instrumental', default='instrumental.wav')

if __name__ == "__main__":
	args = parser.parse_args()
	main(args)