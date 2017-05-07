## Setup

Install python package dependencies:

`pip install -r requirements.txt`

Get audio processing command line tools:

`brew install rubberband`

`brew install sox`

Furthermore, you need access to a MaryTTS server. Instructions for spinning one up can be found here:

https://github.com/marytts/marytts

## Example
`python sing.py allstar.txt allstar.wav && open allstar.wav`
