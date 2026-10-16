import AppKit
import Darwin

@main struct NativeViewerTest {
    @MainActor static func main() throws {
        let root = URL(fileURLWithPath: CommandLine.arguments[1])
        let app = NSApplication.shared
        app.setActivationPolicy(.accessory)
        let host = PreviewHost(root: root)
        app.delegate = host
        host.write("label.json", ["id": "UI acceptance"])
        host.write("state.json", ["state": "watching", "frames": 1,
            "heartbeat": Date().timeIntervalSince1970, "capturedAt": Date().timeIntervalSince1970])
        // A synthetic frame exercises drawing without reading the host desktop.
        let bitmap = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: 800, pixelsHigh: 600,
            bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false,
            colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
        for y in 0..<600 { for x in 0..<800 {
            bitmap.setColor(NSColor(calibratedRed: CGFloat(x)/800, green: CGFloat(y)/600, blue: 0.4, alpha: 1), atX: x, y: y)
        }}
        let imageData = CommandLine.arguments.count > 2
            ? try Data(contentsOf: URL(fileURLWithPath: CommandLine.arguments[2]))
            : bitmap.representation(using: .png, properties: [:])!
        try imageData.write(to: root.appendingPathComponent("frame.png"))
        chmod(root.appendingPathComponent("frame.png").path, 0o600)
        let before = NSWorkspace.shared.frontmostApplication?.processIdentifier
        let cursor = CGEvent(source: nil)!.location
        host.applicationDidFinishLaunching(Notification(name: NSApplication.didFinishLaunchingNotification))
        RunLoop.current.run(until: Date(timeIntervalSinceNow: 0.5))
        precondition(host.panel.isVisible && host.pixels.image != nil)
        precondition(!host.panel.canBecomeKey && !host.panel.canBecomeMain && !host.pixels.acceptsFirstResponder && !host.pixels.needsPanelToBecomeKey)
        // Locally dispatch into our own panel; never post a global cursor/key event.
        let click = NSEvent.mouseEvent(with: .leftMouseDown, location: NSPoint(x: 160, y: 160), modifierFlags: [], timestamp: 0,
            windowNumber: host.panel.windowNumber, context: nil, eventNumber: 0, clickCount: 1, pressure: 1)!
        host.panel.sendEvent(click)
        let ignoredAfterDispatch = host.pixels.ignoredEvents
        precondition(ignoredAfterDispatch >= 1)
        host.pixels.mouseUp(with: click);host.pixels.mouseDragged(with: click)
        host.pixels.rightMouseDown(with: click);host.pixels.rightMouseUp(with: click);host.pixels.rightMouseDragged(with: click)
        host.pixels.otherMouseDown(with: click);host.pixels.otherMouseUp(with: click);host.pixels.otherMouseDragged(with: click)
        host.pixels.scrollWheel(with: click)
        let key = NSEvent.keyEvent(with: .keyDown, location: .zero, modifierFlags: [], timestamp: 0,
            windowNumber: host.panel.windowNumber, context: nil, characters: "x", charactersIgnoringModifiers: "x", isARepeat: false, keyCode: 7)!
        host.pixels.keyDown(with: key);host.pixels.keyUp(with: key)
        host.panel.makeKeyAndOrderFront(nil)
        RunLoop.current.run(until: Date(timeIntervalSinceNow: 0.2))
        host.tick()
        precondition(host.pixels.ignoredEvents == ignoredAfterDispatch + 11)
        precondition(!host.panel.isKeyWindow && !host.panel.isMainWindow)
        precondition(NSWorkspace.shared.frontmostApplication?.processIdentifier == before)
        precondition(CGEvent(source: nil)!.location == cursor)
        let content = host.panel.contentView!
        let rendered = content.bitmapImageRepForCachingDisplay(in: content.bounds)!
        content.cacheDisplay(in: content.bounds, to: rendered)
        try rendered.representation(using: .png, properties: [:])!.write(to: root.appendingPathComponent("preview-render.png"))
        chmod(root.appendingPathComponent("preview-render.png").path, 0o600)
        // An invalid replacement must clear the old pixels too.
        try Data("bad image".utf8).write(to: root.appendingPathComponent("frame.png"))
        host.write("state.json", ["state":"watching", "frames":2, "heartbeat":Date().timeIntervalSince1970, "capturedAt":Date().timeIntervalSince1970])
        host.tick();precondition(host.pixels.image == nil)
        try imageData.write(to: root.appendingPathComponent("frame.png"))
        host.write("state.json", ["state":"watching", "frames":3, "heartbeat":Date().timeIntervalSince1970, "capturedAt":Date().timeIntervalSince1970])
        host.tick();precondition(host.pixels.image != nil)
        host.write("state.json", ["state":"waiting", "frames":3, "heartbeat":Date().timeIntervalSince1970])
        host.tick();precondition(host.pixels.image == nil)
        host.write("state.json", ["state":"watching", "frames":4, "heartbeat":Date().timeIntervalSince1970, "capturedAt":Date().timeIntervalSince1970])
        host.tick();precondition(host.pixels.image != nil)
        // The preview clears when a session ends, even if a last image remains on disk.
        host.write("state.json", ["state":"ended", "frames":1, "heartbeat":Date().timeIntervalSince1970])
        host.tick();precondition(host.pixels.image == nil)
        host.timer?.invalidate()
        host.panel.delegate = nil;host.panel.close()
        host.applicationWillTerminate(Notification(name: NSApplication.willTerminateNotification))
        precondition(!FileManager.default.fileExists(atPath: root.appendingPathComponent("frame.png").path))
        print("Native window passed: visible pixels, local input consumed, nonkey/nonmain, foreground/cursor unchanged, stale frame cleared, close removed frame.")
    }
}
