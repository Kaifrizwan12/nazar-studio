# Research: finding UI-style devices in design images (2026-11-21)

Backs `engine/ui_devices.py`. Tags: [SRC] read for this note, [KNOWN] standard background not re-checked today.

## What the field found
- **Old-fashioned CV vs deep learning, on 50k+ GUI images.** Chen, Xie, Xing, Chen, Xu and Zhu compared seven GUI element detectors (edge and contour methods against Faster R-CNN, YOLOv3, CenterNet). Generic detectors beat the old methods, but the best result was a GUI-specific old-fashioned pass for non-text elements (top-down, coarse to fine) plus a deep-learning text detector. Even the best model scored only F1 0.438 at IoU > 0.9: pixel-exact UI boxes are hard. [SRC] arXiv 2008.05132, ESEC/FSE 2020. https://arxiv.org/abs/2008.05132
- **UIED**, the tool built from that study, splits the job the same way: one pass for text, one for graphic elements (button, image, input bar), exported as JSON. [SRC] https://github.com/MulongXie/UIED ; https://research.monash.edu/en/publications/uied-a-hybrid-tool-for-gui-element-detection/
- **Datasets.** Rico (about 66k Android screens with view hierarchies) is the usual benchmark; a 2024 dataset paper (MUD) reports Rico-trained detectors at 63.4% for buttons at IoU 0.5 and warns that Rico's elements look dated next to modern UI. [SRC] arXiv 2405.07090. Rico itself: Deka et al., UIST 2017. [KNOWN]
- **Newer YOLO models** improve GUI detection but still need training data that matches the style of the screens. [SRC] arXiv 2408.03507

## What we took from it
1. Keep the split: text is not a device. Our pass works on flat colour layers, so type lines inside a bubble become holes in its fill, not regions of their own.
2. Use a GUI-specific non-text pass, not a generic object model: brand slides draw UI as flat, regular shapes (rounded blocks, circles, tracks), which is what the old-fashioned GUI methods are good at, and it needs no training data or downloads.
3. Expect misses and say so. If trained detectors only reach F1 0.44 at tight IoU on real screens, a heuristic pass is a list of candidates for a person to look at, not a verdict. The tool says this in its output and docstring.
4. The shape rules (pill = wide block with half-circle ends; badge = small filled circle; toggle = pill with a round knob at one end; progress bar = track plus fill on one line; chat bubble = rounded block with a tail; card = large flat block) are our own operational definitions, written for brand slides, tested on synthetic slides (PNG and JPEG q80). They have not been checked against a labelled real archive yet.

## Open
- Score it on a real archive with a hand-labelled set (count hits and misses per kind) before trusting the shares in `ui_devices.json`.
- Gradient and photo grounds have no flat layers; a learned detector (UIED's hybrid, or a small YOLO) is the route if that matters.
