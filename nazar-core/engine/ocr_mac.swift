// nazar-core/engine/ocr_mac.swift: read the text in images with macOS's built-in Vision recogniser (offline, nothing installed).
// usage: ocr_mac image1.png [image2.png ...]    prints, per image, a line "#FILE<TAB>path" then "confidence<TAB>text" lines, top to bottom.
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
    for o in obs { if let t = o.topCandidates(1).first { print(String(format: "%.2f\t%@", t.confidence, t.string)) } }
}
