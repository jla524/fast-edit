#/bin/env zsh
HandBrakeCLI -Z "Fast 1080p30" -i "${1}.mov" -o "${1}.mp4" && ffmpeg -i "${1}.mp4" "${1}.mp3"
