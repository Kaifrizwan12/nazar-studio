# fonts/
Shipped: Space Grotesk (Light/Regular/Medium), Space Mono, Anton, all under the SIL Open Font License (OFL_*.txt). They're free for commercial use.
For each brand, drop its fonts here and map roles in brand.json -> "fonts". Use static instances: to cut one from a variable font, run
  .venv/bin/python -c "from fontTools.ttLib import TTFont; from fontTools.varLib.instancer import instantiateVariableFont as I; I(TTFont('X-VF.ttf'), {'wght': 300}).save('X-Light.ttf')"
Record every font's licence in SPEC.md. Never ship a non-commercial or unlicensed font in the client asset pack.
