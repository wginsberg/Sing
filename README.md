# Sing

Ever wanted to make your computer sing song parodies of Smashmouth's hit single "All Star"? I did.

## Setup

Install python package dependencies:

`pip install -r requirements.txt`

Get audio processing command line tools:

`brew install rubberband`

`brew install sox`

## Example
`python sing.py repetoire/allstar.txt allstar.wav && open allstar.wav`
