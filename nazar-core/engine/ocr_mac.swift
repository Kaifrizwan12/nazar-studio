// nazar-core/engine/ocr_mac.swift: read the text in an image with macOS's built-in Vision recogniser (offline, nothing installed).
// usage: swiftc -O ocr_mac.swift -o ocr_mac   then   ./ocr_mac image.png
import Foundation
import Vision
import AppKit

guard CommandLine.arguments.count > 1, let img = NSImage(contentsOfFile: CommandLine.arguments[1]),
      let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    FileHandle.standardError.write("cannot read image\n".data(using: .utf8)!); exit(1)
}
let req = VNRecognizeTextRequest()
req.recognitionLevel = .accurate
req.usesLanguageCorrection = false          // Roman Urdu is not English: don't "correct" it
let handler = VNImageRequestHandler(cgImage: cg, options: [:])
try handler.perform([req])
// top to bottom, one line per observation
let obs = (req.results ?? []).sorted { $0.boundingBox.midY > $1.boundingBox.midY }
for o in obs { if let t = o.topCandidates(1).first { print(String(format: "%.2f\t%@", t.confidence, t.string)) } }
