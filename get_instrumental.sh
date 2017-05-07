# This script is provided for reference, in case the instrumental.wav file is lost
#
# Download this song: https://www.youtube.com/watch?v=-UxD1FObOH4
# Using a tool like this one: http://www.youtube-mp3.org
#
# Make sure you have ffmpeg installed. On a Mac do:
# `brew install ffmpeg`
#
# Then, assuming you downloaded the mp3 to 'allstar.mp3' in the current directory, do:

ffmpeg -i allstar.mp3 -ar 48000 allstar.wav
sox allstar.wav -c 1 /tmp/allstar_mono.wav
sox /tmp/allstar_mono.wav instrumental.wav trim 4.03 10
