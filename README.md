# The Superintelligence at the End of This Book

A page-turning picture book about recursive self-improvement, starring lovable, furry old Grady.

Every page of the book is written by the page before it, only a little bit smarter, so Grady begs you not to turn any. He ties the page shut with an open letter, nails it shut with a six-month pause, and builds a wall of voluntary commitments. You turn the pages anyway. Around page 64 the book starts turning its own pages, and after that there is no going back. On the page before the last page you flip a coin, once, and it decides which ending you get.

**Read it:** https://dzkalman.github.io/superintelligence-at-the-end/

Turn pages with the button, the page corner, the arrow keys, or a swipe.

## The coin

The coin comes from Paul Christiano's talk at the Hinton Lectures in Toronto in November 2026. He said that if AI is developed along the fastest possible path, the odds of an AI takeover are something like a coin flip, and that he hopes the real odds are much lower because it will not be built that fast. See [Paul Wells's report](https://paulwells.substack.com/p/driverless) and a [transcript of the lecture](https://ceointerviews.ai/interview/3228880/).

The coin in the book is fair (`crypto.getRandomValues`) and is flipped once per reading.

## Running it

There is no build step. Serve the folder with any static file server and open `index.html`:

```bash
python3 -m http.server 8000
```

## How it is made

- `index.html` is the whole book: the text, the page-turning, the coin.
- `art/*.webp` are the pictures, as transparent cut-outs so the page's paper shows through.
- `tools/art.py gen` draws the pictures with an image model through OpenRouter, each one from the character sheet in `art/raw/sheet.png` so Grady stays the same from page to page. `tools/art.py cut` turns the white paper transparent and splits the plank and brick sheets into separate pieces (it needs `pillow`, `numpy` and `scipy`).
- `tools/artifact.sh` writes a copy of the page without its `<html>` wrapper, for publishing as a claude.ai artifact.

## Credits

An affectionate parody of *The Monster at the End of This Book* by Jon Stone and Michael Smollin (1971). Grady is an original character, and the pictures were made with an image model. Not affiliated with or endorsed by Sesame Workshop, or by anyone quoted.
