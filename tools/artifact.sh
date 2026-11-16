#!/bin/sh
# Writes build/artifact.html: the parts of index.html between the <!--page--> markers.
# claude.ai artifacts supply their own <html>/<head>/<body>, so they are published from this copy.
cd "$(dirname "$0")/.." && mkdir -p build &&
awk '/<!--\/page-->/{on=0} on{print} /<!--page-->/{on=1}' index.html > build/artifact.html &&
echo "wrote build/artifact.html ($(wc -c < build/artifact.html | tr -d ' ') bytes)"
