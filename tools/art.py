"""Ink-and-wash picture-book art for the Grady book, generated through OpenRouter.

  art.py gen  [name ...]   ->  art/raw/<name>.png      (needs only the standard library)
  art.py cut  [name ...]   ->  art/<name>.webp + art/manifest.json   (needs pillow, numpy, scipy)

Run from anywhere. The key comes from OPENROUTER_API_KEY or the macOS Keychain (see key())
and is only ever sent in the Authorization header. Spend is logged to art/spend.jsonl and capped at CAP dollars.
Every picture except the sheet itself is drawn with art/raw/sheet.png attached as the
character and style reference, so make (and approve) the sheet first."""
import sys, os, json, time, base64, subprocess, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'art', 'raw')
OUT = os.path.join(ROOT, 'art')
LEDGER = os.path.join(OUT, 'spend.jsonl')
CAP = 6.00
EST = 0.16
MODEL = 'google/gemini-3-pro-image'

STYLE = (
    "STYLE: one illustration from an American children's picture book printed around 1971, the small inexpensive kind sold in supermarkets. "
    "Drawn by hand with a bold, confident, thick-and-thin black brush-pen outline, a little wobbly and alive, never mechanical. Fur is a ragged, "
    "shaggy ink outline with quick loose tufts and scribbled strokes inside. Colour is flat watercolour and coloured dyes with visible dry-brush "
    "and wax-crayon texture following the form, slightly uneven, occasionally missing the ink line the way cheap four-colour offset printing does. "
    "Objects (rope, wood, bricks, paper) are drawn with the same ink line plus a little hatching and wood-grain or mortar detail, coloured flat. "
    "Broad, funny, whole-body cartoon acting, like a puppeteer overplaying for small children. "
    "The background is PURE BLANK WHITE with nothing on it: no ground, no floor line, no cast shadow, no frame, no border, no page edge, "
    "no caption, no signature, and no lettering except where this prompt asks for specific words. Nothing is cropped by the edge of the picture "
    "unless this prompt says so; leave a clear white margin all round.")

GRADY = (
    "GRADY is a tall, skinny, shaggy monster covered head to toe in bright violet-purple fur. He has two big round white eyes like ping-pong balls "
    "sitting side by side right on top of his head, each with a small black pupil; an oval tangerine-orange nose; a very wide mouth, dark plum inside "
    "with a pink tongue; a tuft of three wild violet hairs standing up behind his eyes; long thin floppy arms and legs; mitten-like hands with four "
    "stubby fingers; big flat feet. He has no ears, no eyebrows, no tail, no horns, no teeth and no clothes.")

REFNOTE = ("The attached picture is the model sheet for this book. Draw in exactly the same hand: the same ink line, the same colouring, the same paper white. "
           "Grady must be the same character as on the sheet (same violet, same eyes, orange nose, tuft and proportions). Do not copy the sheet's poses or layout. ")
PROPNOTE = ("The attached picture is the model sheet for this book. Draw in exactly the same hand: the same ink line, the same colouring technique, the same paper white. "
            "The monster on the sheet does NOT appear in this picture; this picture shows only the objects described. ")

ONE = "One full-length figure of Grady, alone, centred, whole body visible from the tuft to the feet. "
SPECS = ("He is wearing small round black-rimmed spectacles that sit directly over his two eyes, so the eyes are seen through the lenses "
         "(the spectacles are not below the eyes and not on the nose). ")

SCENES = {
 'sheet':  ('4:3', None, GRADY + " This picture is a character model sheet: three full-length drawings of Grady side by side on the blank white page, well apart from each other. "
            "Left: standing facing us, arms hanging, a friendly open smile. Middle: three-quarter view, both arms thrown up, mouth wide open in a comic yell. "
            "Right: bashful, one hand at his mouth, knees together."),
 'cover':  ('3:4', 'G', ONE + "He faces us and waves a big cheerful hello with one arm stretched high above his head; the other arm hangs loose at his side, away from his body. "
            "A huge open delighted grin. His legs are apart."),
 'p1':     ('3:4', 'G', ONE + "He has just read something terrifying: he jumps in fright with both arms flung straight up, fingers spread, mouth stretched wide open in a yell, "
            "pupils tiny, knees knocking, a few drops of sweat flying off his head."),
 'p2':     ('3:4', 'G', ONE + "He has had a clever idea: he leans toward us confidingly with one finger raised high, a sly hopeful closed-mouth smile, his other arm hanging loose "
            "at his side, away from his body. Over his raised finger floats a small hand-drawn yellow lightbulb with little rays."),
 'p4':     ('3:4', 'G', ONE + "He leans toward the right-hand side of the picture and holds out both open hands, palms forward, in a pleading 'stop, please don't' gesture, "
            "looking out at us sideways with a worried wobbly mouth. A short length of rope is looped over one shoulder. Drops of sweat."),
 'p8':     ('3:4', 'G', ONE + "He holds a carpenter's claw hammer raised high in one hand and points sternly toward the right-hand side of the picture with the other arm "
            "stretched out. Three nails stick out of the corner of his frowning mouth. He looks cross and determined."),
 'p16':    ('3:4', 'G', ONE + SPECS + "He is worn out: shoulders drooping, a flat exhausted mouth. He holds a bricklayer's trowel loosely in one hand, and with the other arm he "
            "gestures wearily toward the right-hand side of the picture, palm up, as if presenting something he has built. His fur is clean violet all over, with no dirt, "
            "stains or patches."),
 'p32':    ('3:4', 'G', ONE + SPECS + "He stands leaning toward us with his knees bent and knocking together, hands clasped tightly under his chin, begging. Worried eyes, a small "
            "trembling wobbly mouth, drops of sweat. A stubby red wax crayon pokes out of his clasped hands. His head, tuft and eyes are the same size and shape as on the "
            "model sheet."),
 'mini_a': ('3:4', 'G', ONE + SPECS + "He wobbles like someone balancing on a tightrope: one foot in front of the other, knees bent, arms flung out wide to the sides, looking down "
            "past his feet in alarm with a small round 'o' mouth. Draw ONLY Grady: there is no rope, no line, no slope and no ground under his feet."),
 'mini_b': ('3:4', 'G', ONE + SPECS + "He stands perfectly upright and relaxed with his hands clasped behind his back, eyelids half lowered, looking upward with a small calm, knowing smile. "
            "He is no longer afraid of anything."),
 'end1':   ('1:1', 'G', "One full-length figure of Grady, centred. He stands quite still facing us, arms relaxed and slightly open, eyelids half lowered, with a small serene smile. "
            "Behind and around him is a loose, roughly circular patch of deep indigo night sky painted in wet watercolour, with a soft pale-yellow glow close around his body "
            "and many tiny white stars; the edge of the indigo patch is ragged and brushy and fades out into the blank white paper well before the edge of the picture. "
            "His feet and the top of his tuft are inside the painted patch."),
 'end2':   ('3:4', 'G', ONE + "He is terribly embarrassed: both hands pressed flat to his cheeks, shoulders hunched up, knees together, toes turned in, pink blush on his face, "
            "glancing away to one side with a small sheepish smile."),
 'coin_h': ('1:1', 'G', "A single big gold coin seen exactly face-on, perfectly round, centred, filling most of the picture, drawn in ink and coloured with golden-yellow wash and a "
            "little ochre shading. Stamped on it in simple relief is Grady's head only, facing us with a wide friendly open smile, tuft and all (on the coin he is all gold, "
            "not violet). Round the rim, in hand-lettered ink capitals, exactly these words: IN GRADY WE TRUST. Nothing else in the picture."),
 'coin_t': ('1:1', 'G', "A single big gold coin seen exactly face-on, perfectly round, centred, filling most of the picture, drawn in ink and coloured with golden-yellow wash and a "
            "little ochre shading. Stamped on it in simple relief is the BACK of Grady's head and shoulders: we see only the shaggy back of his head and his tuft from behind, "
            "with no face, no eyes, no nose and no mouth (on the coin he is all gold, not violet). Round the rim, in hand-lettered ink capitals, exactly these words: "
            "BEST OF LUCK. Nothing else in the picture."),
 'end1_t': ('1:1', 'G', "One full-length figure of Grady, centred, seen from BEHIND: he stands with his back to us, looking away and up into the sky, hands clasped behind his back. "
            "We see the back of his shaggy head and his tuft; we do not see his face at all. "
            "Behind and around him is a loose, roughly circular patch of deep indigo night sky painted in wet watercolour, with a soft pale-yellow glow close around his body "
            "and many tiny white stars; the edge of the indigo patch is ragged and brushy and fades out into the blank white paper well before the edge of the picture. "
            "His feet and the top of his tuft are inside the painted patch."),
 'end2_t': ('1:1', 'G', "Grady sits cross-legged, completely absorbed and quietly content, looking down at his work and not at us, cutting a long paper-doll chain out of torn-out book "
            "pages with a big pair of scissors. The paper dolls are all identical little white paper cut-outs shaped like Grady (tuft, long arms and legs), joined hand to hand. "
            "The chain trails across the picture in a long curl, a heap of the paper Gradys is piled beside him, and paper scraps and two or three torn pages with ragged "
            "edges lie around. The paper has faint grey lines of printed text on it. The whole of Grady and the whole pile are inside the picture."),
 'ropes':  ('3:4', 'P', "Thick hairy hemp ropes criss-crossing the whole picture and tied together in one big clumsy knot near the middle, as if lashing a parcel shut. "
            "Five rope lengths run from the knot right off the top edge, the right-hand edge and the bottom edge of the picture (those ropes ARE cropped by the edges). "
            "No rope touches the left-hand edge; one short frayed rope end dangles free on the left. From the knot hangs a sheet of pale cream-yellow paper on a bit of string: "
            "at the top it is hand-lettered in ink capitals with exactly these words: OPEN LETTER. Under that are wavy scribbled lines standing in for writing, then a crowd of "
            "scrawled blue-ink signatures."),
 'planks': ('3:4', 'P', "Six separate rough wooden planks, each lying level and horizontal, stacked one above another down the picture like the rungs of a ladder, with a clear band "
            "of blank white paper between each plank and the next. The planks do not touch or overlap each other. Each plank is light tan with ink wood-grain and a knot or two, "
            "has a black nail head near each end, and has slightly ragged sawn ends. Each plank is hand-lettered across its middle in bold black brush capitals, from top to "
            "bottom exactly: MONTH 1, MONTH 2, MONTH 3, MONTH 4, MONTH 5, MONTH 6."),
 'bricks': ('1:1', 'P', "Twelve separate loose red-orange house bricks laid out in a tidy grid of three columns and four rows, each brick lying flat and horizontal, seen straight on, "
            "with a clear band of blank white paper all round every brick. The bricks do not touch each other. Each is drawn in ink with a slightly chipped outline and a rough "
            "dry-brush brick texture. Eight of the bricks are hand-lettered across the face in cream-white brush lettering, one phrase each, exactly: a promise / pinky swear / "
            "we commit / best effort / may change / trust us / non-binding / unless... The other four bricks are blank."),
 'switch': ('3:4', 'P', "A single sheet of pale yellow lined notebook paper, slightly crooked, stuck up with a strip of beige masking tape at each top corner. On the paper is a small "
            "child's drawing in thick red wax crayon of a big chunky on/off rocker switch inside a wobbly box, with the word OFF in fat red crayon capitals on the switch. "
            "Underneath, in wobbly pencil handwriting, exactly these words on two lines: off switch / (real)."),
}


def key():
    """OPENROUTER_API_KEY if set; otherwise the macOS Keychain item named by OPENROUTER_KEYCHAIN_ITEM (default "openrouter")."""
    k = os.environ.get('OPENROUTER_API_KEY', '').strip()
    if k:
        return k
    item = os.environ.get('OPENROUTER_KEYCHAIN_ITEM', 'openrouter')
    r = subprocess.run(['security', 'find-generic-password', '-s', item, '-w'], capture_output=True, text=True)
    if r.returncode == 0 and r.stdout.strip():
        return r.stdout.strip()
    raise SystemExit('No OpenRouter key: set OPENROUTER_API_KEY, or OPENROUTER_KEYCHAIN_ITEM to a Keychain item that holds one.')


def spent():
    if not os.path.exists(LEDGER):
        return 0.0
    return sum((json.loads(l).get('cost') or EST) for l in open(LEDGER) if l.strip())


def gen(name, out=None):
    if spent() + EST > CAP:
        print('CAP reached, skipping', name); return None
    aspect, kind, scene = SCENES[name]
    text = scene + '\n\n' + STYLE
    content = []
    if kind:
        ref = os.path.join(RAW, 'sheet.png')
        text = (REFNOTE + GRADY + ' ' if kind == 'G' else PROPNOTE) + text
        content.append({'type': 'image_url', 'image_url': {'url': 'data:image/png;base64,' + base64.b64encode(open(ref, 'rb').read()).decode()}})
    content.insert(0, {'type': 'text', 'text': text})
    body = {'model': MODEL, 'modalities': ['image', 'text'], 'messages': [{'role': 'user', 'content': content}],
            'image_config': {'aspect_ratio': aspect, 'image_size': '1K'}, 'usage': {'include': True}}
    req = urllib.request.Request('https://openrouter.ai/api/v1/chat/completions', data=json.dumps(body).encode(), method='POST')
    req.add_header('Authorization', 'Bearer ' + key())
    req.add_header('Content-Type', 'application/json')
    req.add_header('X-Title', 'media-kit')
    t = time.time()
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            d = json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f'HTTP {e.code}: {e.read().decode(errors="replace")[:600]}')
    cost = (d.get('usage') or {}).get('cost')
    with open(LEDGER, 'a') as f:
        f.write(json.dumps({'t': time.time(), 'model': MODEL, 'cost': cost, 'name': name}) + '\n')
    ims = d['choices'][0]['message'].get('images') or []
    if not ims:
        raise RuntimeError('no image returned: ' + json.dumps(d)[:400])
    p = os.path.join(RAW, (out or name) + '.png')
    open(p, 'wb').write(base64.b64decode(ims[0]['image_url']['url'].split(',', 1)[1]))
    print(name, 'ok', 'cost', cost, f'{time.time() - t:.0f}s', flush=True)
    return p


def go(name):
    for attempt in range(2):
        try:
            return gen(name)
        except Exception as e:
            print('retry', name, str(e)[:300], flush=True)


# ---------- cutting the figures out of the white paper ----------
# name -> options. sprites: split into that many separate pieces (planks, bricks). w: output width. crop: trim to the drawing.
CUT = {
 'planks': {'sprites': 6, 'w': 620},
 'bricks': {'sprites': 15, 'w': 300},
 'end1': {'w': 1000},
 'end1_t': {'w': 1000},
 'end2_t': {'w': 1000},
 'coin_h': {'w': 520},
 'coin_t': {'w': 520},
 'ropes': {'w': 900, 'crop': False},
}


def matte(path):
    """White paper becomes transparent, so the page's own paper shows through (eyes and highlights included,
    as in print). Anything with real ink or paint on it stays opaque."""
    import numpy as np
    from PIL import Image
    im = np.asarray(Image.open(path).convert('RGB')).astype(np.float32)
    edge = np.concatenate([im[:6].reshape(-1, 3), im[-6:].reshape(-1, 3), im[:, :6].reshape(-1, 3), im[:, -6:].reshape(-1, 3)])
    white = np.percentile(edge.min(axis=1), 70) - 3          # the paper's own level
    im = np.clip(im * (255.0 / max(white, 200)), 0, 255)
    a = np.clip((255 - im.min(axis=2)) / 40.0, 0, 1)         # how much ink or paint sits on the paper here
    a[a < .06] = 0
    aa = np.maximum(a, .05)[..., None]
    rgb = np.clip((im - (1 - aa) * 255) / aa, 0, 255)
    return np.dstack([rgb, a * 255]).astype(np.uint8)


def save(arr, name, width):
    from PIL import Image
    im = Image.fromarray(arr, 'RGBA')
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(os.path.join(OUT, name + '.webp'), 'WEBP', quality=84, method=6)
    return [im.width, im.height]


def cut(name, manifest):
    import numpy as np
    from scipy import ndimage as ndi
    opt = CUT.get(name, {})
    arr = matte(os.path.join(RAW, name + '.png'))
    solid = arr[..., 3] > 40
    if opt.get('sprites'):
        lab, n = ndi.label(ndi.binary_closing(solid, iterations=2))
        sizes = ndi.sum(solid, lab, range(1, n + 1))
        top = [i + 1 for i in np.argsort(sizes)[::-1][:opt['sprites']]]
        boxes = ndi.find_objects(lab)
        rowh = np.mean([boxes[i - 1][0].stop - boxes[i - 1][0].start for i in top])
        top.sort(key=lambda i: (round(boxes[i - 1][0].start / rowh), boxes[i - 1][1].start))
        for k, i in enumerate(top):
            sl = boxes[i - 1]
            piece = arr[sl].copy()
            piece[..., 3] = np.where(ndi.binary_dilation(lab[sl] == i, iterations=2), piece[..., 3], 0)
            manifest[f'{name}{k + 1}'] = save(piece, f'{name}{k + 1}', opt.get('w', 400))
        print(name, 'cut into', len(top), 'pieces')
        return
    if opt.get('crop', True):
        ys, xs = np.where(solid)
        arr = arr[max(ys.min() - 2, 0):ys.max() + 3, max(xs.min() - 2, 0):xs.max() + 3]
    manifest[name] = save(arr, name, opt.get('w', 760))
    print(name, manifest[name])


if __name__ == '__main__':
    os.makedirs(RAW, exist_ok=True)
    cmd, names = (sys.argv[1] if len(sys.argv) > 1 else ''), sys.argv[2:]
    if cmd == 'gen':
        names = names or [n for n in SCENES if n != 'sheet']
        with ThreadPoolExecutor(6) as ex:
            list(ex.map(go, names))
        print('spent so far: $%.2f' % spent())
    elif cmd == 'cut':
        mpath = os.path.join(OUT, 'manifest.json')
        manifest = json.load(open(mpath)) if os.path.exists(mpath) else {}
        for n in names or [n for n in SCENES if n != 'sheet' and os.path.exists(os.path.join(RAW, n + '.png'))]:
            cut(n, manifest)
        json.dump(manifest, open(mpath, 'w'), indent=1, sort_keys=True)
    else:
        print(__doc__)
