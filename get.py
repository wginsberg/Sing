#!/usr/bin/env python

import requests

def main():
	
	args = {
		'INPUT_TEXT':"Somebody once told me the world was gonna roll me. I ain't the sharpest tool in the shed.",
		'INPUT_TYPE':'TEXT',
		'OUTPUT_TYPE':'AUDIO',
		'AUDIO':'WAVE_FILE',
		'LOCALE':'en_US'
	}

	url = "http://localhost:59125/process"
	response = requests.get(url, params=args)

	with open('allstar.wav', 'w') as out_file:
		out_file.write(response.content)

if __name__ == "__main__":
	main()
