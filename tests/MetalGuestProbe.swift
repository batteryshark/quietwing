import Foundation
import Metal
import CoreGraphics
import ImageIO
import Darwin

// Guest-only adaptation of the earlier measured windowless Metal probe.
// Refuse execution on the host before creating any files or Metal resources.
var virtualized: Int32 = 0
var virtualizedSize = MemoryLayout<Int32>.size
guard sysctlbyname("kern.hv_vmm_present", &virtualized, &virtualizedSize, nil, 0) == 0,
      virtualized == 1 else { fputs("Refusing non-guest execution\n", stderr); exit(3) }

// Intentionally no AppKit, NSApplication, window, CAMetalLayer, capture API,
// input API, audio API, or display/session-setting API.
let width = 320
let height = 192
let bytesPerRow = width * 4 // 1280, a multiple of 256 for texture-to-buffer blits.
let byteCount = bytesPerRow * height
let frameCount = max(2, Int(CommandLine.arguments.dropFirst().first ?? "120") ?? 120)
let interval = max(0.05, Double(CommandLine.arguments.dropFirst(2).first ?? "0.5") ?? 0.5)
let outputDirectory = URL(fileURLWithPath: CommandLine.arguments.dropFirst(3).first ?? ".", isDirectory: true)
let startDate = ISO8601DateFormatter().string(from: Date())

enum ProbeError: Error, CustomStringConvertible {
    case failure(String)
    var description: String { switch self { case let .failure(message): return message } }
}

func need<T>(_ value: T?, _ message: String) throws -> T {
    guard let value = value else { throw ProbeError.failure(message) }
    return value
}

func writeJSON(_ object: [String: Any], name: String) throws {
    let data = try JSONSerialization.data(withJSONObject: object, options: [.prettyPrinted, .sortedKeys])
    try data.write(to: outputDirectory.appendingPathComponent(name), options: .atomic)
}

func savePNG(_ pixels: [UInt8], name: String) throws {
    let data = Data(pixels) as CFData
    let provider = try need(CGDataProvider(data: data), "CGDataProvider failed")
    let image = try need(CGImage(width: width, height: height, bitsPerComponent: 8,
        bitsPerPixel: 32, bytesPerRow: bytesPerRow,
        space: CGColorSpaceCreateDeviceRGB(),
        bitmapInfo: CGBitmapInfo(rawValue: CGImageAlphaInfo.last.rawValue),
        provider: provider, decode: nil, shouldInterpolate: false,
        intent: .defaultIntent), "CGImage creation failed")
    let url = outputDirectory.appendingPathComponent(name)
    let destination = try need(CGImageDestinationCreateWithURL(url as CFURL,
        "public.png" as CFString, 1, nil), "PNG destination failed")
    CGImageDestinationAddImage(destination, image, nil)
    if !CGImageDestinationFinalize(destination) { throw ProbeError.failure("PNG encoding failed") }
}

let shaderSource = """
#include <metal_stdlib>
using namespace metal;
struct VertexOut { float4 position [[position]]; };
vertex VertexOut triangleVertex(uint vid [[vertex_id]], constant float4 &u [[buffer(0)]]) {
    const float2 vertices[3] = { float2(-0.25, -0.4), float2(0.25, -0.4), float2(0.0, 0.4) };
    VertexOut out;
    out.position = float4(vertices[vid] + float2(u.x, 0.0), 0.0, 1.0);
    return out;
}
fragment float4 triangleFragment(VertexOut in [[stage_in]], constant float4 &u [[buffer(0)]]) {
    return u.y > 0.5 ? float4(1.0, 0.0, 0.0, 1.0) : float4(0.0, 1.0, 0.0, 1.0);
}
"""

do {
    try FileManager.default.createDirectory(at: outputDirectory, withIntermediateDirectories: true)
    let device = try need(MTLCreateSystemDefaultDevice(), "No default Metal device exposed to this process")
    let queue = try need(device.makeCommandQueue(), "Unable to create Metal command queue")
    let library = try device.makeLibrary(source: shaderSource, options: nil)
    let pipelineDescriptor = MTLRenderPipelineDescriptor()
    pipelineDescriptor.vertexFunction = library.makeFunction(name: "triangleVertex")
    pipelineDescriptor.fragmentFunction = library.makeFunction(name: "triangleFragment")
    pipelineDescriptor.colorAttachments[0].pixelFormat = .rgba8Unorm
    let pipeline = try device.makeRenderPipelineState(descriptor: pipelineDescriptor)

    let textureDescriptor = MTLTextureDescriptor.texture2DDescriptor(pixelFormat: .rgba8Unorm,
        width: width, height: height, mipmapped: false)
    textureDescriptor.storageMode = .private
    textureDescriptor.usage = [.renderTarget]
    let texture = try need(device.makeTexture(descriptor: textureDescriptor), "Render texture allocation failed")
    let readback = try need(device.makeBuffer(length: byteCount, options: .storageModeShared), "Readback buffer allocation failed")
    texture.label = "Offscreen test triangle 320x192"
    readback.label = "Offscreen test readback"

    var frames: [[String: Any]] = []
    var failures: [String] = []
    var checksums = Set<String>()
    var exportedImages: [String] = []
    var totalGPUSeconds = 0.0
    var maxGPUSeconds = 0.0
    var maxAllocatedBytes = device.currentAllocatedSize
    let start = ProcessInfo.processInfo.systemUptime
    print("START pid=\(getpid()) device=\(device.name) frames=\(frameCount) interval=\(interval)s no-window=true")
    fflush(stdout)

    for frame in 0..<frameCount {
        let scheduledTime = start + Double(frame) * interval
        let wait = scheduledTime - ProcessInfo.processInfo.systemUptime
        if wait > 0 { Thread.sleep(forTimeInterval: wait) }

        try autoreleasepool {
            let xOffset = Float(-0.55 + 1.10 * Double(frame % 24) / 23.0)
            let red = frame % 2 == 0
            var uniforms = SIMD4<Float>(xOffset, red ? 1.0 : 0.0, 0.0, 0.0)
            let command = try need(queue.makeCommandBuffer(), "No command buffer")
            let pass = MTLRenderPassDescriptor()
            pass.colorAttachments[0].texture = texture
            pass.colorAttachments[0].loadAction = .clear
            pass.colorAttachments[0].storeAction = .store
            pass.colorAttachments[0].clearColor = MTLClearColor(red: 4.0 / 255.0, green: 8.0 / 255.0, blue: 16.0 / 255.0, alpha: 1)
            let encoder = try need(command.makeRenderCommandEncoder(descriptor: pass), "No render encoder")
            encoder.setRenderPipelineState(pipeline)
            encoder.setVertexBytes(&uniforms, length: MemoryLayout<SIMD4<Float>>.stride, index: 0)
            encoder.setFragmentBytes(&uniforms, length: MemoryLayout<SIMD4<Float>>.stride, index: 0)
            encoder.drawPrimitives(type: .triangle, vertexStart: 0, vertexCount: 3)
            encoder.endEncoding()
            let blit = try need(command.makeBlitCommandEncoder(), "No blit encoder")
            blit.copy(from: texture, sourceSlice: 0, sourceLevel: 0, sourceOrigin: MTLOrigin(x: 0, y: 0, z: 0),
                sourceSize: MTLSize(width: width, height: height, depth: 1), to: readback,
                destinationOffset: 0, destinationBytesPerRow: bytesPerRow, destinationBytesPerImage: byteCount)
            blit.endEncoding()
            let cpuStart = ProcessInfo.processInfo.systemUptime
            command.commit()
            command.waitUntilCompleted()
            let waitSeconds = ProcessInfo.processInfo.systemUptime - cpuStart
            guard command.status == .completed else {
                throw ProbeError.failure("Frame \(frame) command failed: \(command.status.rawValue), \(String(describing: command.error))")
            }
            let gpuSeconds = max(0, command.gpuEndTime - command.gpuStartTime)
            totalGPUSeconds += gpuSeconds
            maxGPUSeconds = max(maxGPUSeconds, gpuSeconds)
            maxAllocatedBytes = max(maxAllocatedBytes, device.currentAllocatedSize)
            let pixels = Array(UnsafeBufferPointer(start: readback.contents().assumingMemoryBound(to: UInt8.self), count: byteCount))
            var markerPixels = 0, unexpectedPixels = 0
            var sumX = 0.0, sumY = 0.0
            var checksum: UInt64 = 14695981039346656037
            for y in 0..<height {
                for x in 0..<width {
                    let i = (y * width + x) * 4
                    let r = pixels[i], g = pixels[i + 1], b = pixels[i + 2], a = pixels[i + 3]
                    let isMarker = red ? (r == 255 && g == 0 && b == 0 && a == 255) : (r == 0 && g == 255 && b == 0 && a == 255)
                    if isMarker { markerPixels += 1; sumX += Double(x) + 0.5; sumY += Double(y) + 0.5 }
                    else if !(r == 4 && g == 8 && b == 16 && a == 255) { unexpectedPixels += 1 }
                    for channel in 0..<4 { checksum = (checksum ^ UInt64(pixels[i + channel])) &* 1099511628211 }
                }
            }
            let centroidX = markerPixels > 0 ? sumX / Double(markerPixels) : -1
            let centroidY = markerPixels > 0 ? sumY / Double(markerPixels) : -1
            let expectedX = (Double(xOffset) + 1) * Double(width) / 2
            let passed = markerPixels >= 3000 && markerPixels <= 3150 && abs(centroidX - expectedX) < 1.0 && unexpectedPixels == 0
            if !passed { failures.append("frame \(frame): markerPixels=\(markerPixels), centroidX=\(centroidX) expected=\(expectedX), unexpectedPixels=\(unexpectedPixels)") }
            let hex = String(checksum, radix: 16)
            checksums.insert(hex)
            frames.append([
                "frame": frame, "elapsed_seconds": ProcessInfo.processInfo.systemUptime - start,
                "gpu_command_status": "completed", "gpu_seconds": gpuSeconds, "cpu_completion_wait_seconds": waitSeconds,
                "x_offset_ndc": xOffset, "expected_centroid_x": expectedX,
                "centroid_x": centroidX, "centroid_y": centroidY,
                "marker_color": red ? "red" : "green", "marker_pixels": markerPixels,
                "unexpected_pixels": unexpectedPixels, "checksum_fnv1a64": hex, "passed": passed
            ])
            if [0, 12, 23, frameCount - 1].contains(frame) {
                let name = String(format: "frame-%03d.png", frame)
                try savePNG(pixels, name: name)
                exportedImages.append(name)
            }
            if frame % 20 == 0 || frame == frameCount - 1 {
                print("FRAME \(frame) pass=\(passed) pixels=\(markerPixels) centroidX=\(String(format: "%.2f", centroidX)) gpuMs=\(String(format: "%.3f", gpuSeconds * 1000))")
                fflush(stdout)
            }
        }
    }
    let elapsed = ProcessInfo.processInfo.systemUptime - start
    let result: [String: Any] = [
        "probe": "no-window offscreen Metal render-to-texture and GPU-to-CPU readback",
        "started_utc": startDate, "os": ProcessInfo.processInfo.operatingSystemVersionString,
        "device_name": device.name, "device_has_unified_memory": device.hasUnifiedMemory,
        "process_id": getpid(), "virtualized_guest": true, "window_created": false, "audio_used": false, "input_used": false,
        "texture_width": width, "texture_height": height, "texture_format": "rgba8Unorm",
        "texture_storage": "private", "readback_storage": "shared",
        "nominal_resource_bytes": byteCount * 2, "peak_device_allocated_bytes": maxAllocatedBytes,
        "requested_frames": frameCount, "completed_frames": frames.count, "interval_seconds": interval,
        "elapsed_seconds": elapsed, "distinct_frame_checksums": checksums.count,
        "total_gpu_seconds": totalGPUSeconds, "maximum_gpu_command_seconds": maxGPUSeconds,
        "passed": failures.isEmpty && checksums.count >= min(frameCount, 24),
        "validation_failures": failures, "pngs": exportedImages, "frames": frames,
        "limits": ["This renders purpose-built code, not an arbitrary unmodified game.",
                   "This process runs inside the separately provisioned macOS VM; the probe does not provision it.",
                   "No user desktop capture, input routing, audio routing, lock, detach or foreground-game test was performed.",
                   "Two small resources and this bounded frame cadence do not constitute a game performance benchmark."]
    ]
    try writeJSON(result, name: "results.json")
    print("DONE passed=\(result["passed"]!) completed=\(frames.count) elapsed=\(String(format: "%.2f", elapsed))s distinct=\(checksums.count) gpuTotalMs=\(String(format: "%.3f", totalGPUSeconds * 1000))")
    if !failures.isEmpty { exit(2) }
} catch {
    let message = String(describing: error)
    try? writeJSON(["passed": false, "started_utc": startDate, "error": message,
                    "window_created": false, "audio_used": false, "input_used": false], name: "failure.json")
    fputs("FAILED: \(message)\n", stderr)
    exit(1)
}
