// nazar-core/engine/ocr_mac.swift: read the text in images with macOS's built-in Vision recogniser (offline, nothing installed).
// usage: ocr_mac image1.png [image2.png ...]    prints, per image, a line "#FILE<TAB>path" then "confidence<TAB>x<TAB>y<TAB>w<TAB>h<TAB>text" lines, top to bottom (box 0..1 from the top-left).
// One process reads many images, so the recognition model loads once.
import Foundation
import Vision
import AppKit

let paths = Array(CommandLine.arguments.dropFirst())
if paths.isEmpty { FileHandle.standardError.write("usage: ocr_mac image...\n".data(using: .utf8)!); exit(1) }
for path in paths {
    print("#FILE\t\(path)")
    guard let img = NSImage(contentsOfFile: path), let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else { continue }
    let req = VNRecognizeTextRequest()
    req.recognitionLevel = .accurate
    req.usesLanguageCorrection = false          // Roman Urdu is not English: don't "correct" it
    try? VNImageRequestHandler(cgImage: cg, options: [:]).perform([req])
    let obs = (req.results ?? []).sorted { $0.boundingBox.midY > $1.boundingBox.midY }
    // confidence, then the box (x, y from the TOP-left, width, height, all 0..1), then the text
    for o in obs { if let t = o.topCandidates(1).first { let b = o.boundingBox; print(String(format: "%.2f\t%.4f\t%.4f\t%.4f\t%.4f\t%@", t.confidence, b.minX, 1 - b.maxY, b.width, b.height, t.string)) } }
}
