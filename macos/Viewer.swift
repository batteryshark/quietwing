import AppKit
import Darwin

// Pixels only: this app has no Virtualization, control socket, event-posting or guest-input code.
final class PreviewPanel: NSPanel {
    override var canBecomeKey: Bool { false }
    override var canBecomeMain: Bool { false }
}
final class PreviewPixels: NSView {
    var image: NSImage? { didSet { needsDisplay = true } }
    private(set) var ignoredEvents = 0
    override var acceptsFirstResponder: Bool { false }
    override func acceptsFirstMouse(for event: NSEvent?) -> Bool { true }
    override var needsPanelToBecomeKey: Bool { false }
    override func draw(_ dirtyRect: NSRect) {
        NSColor(calibratedWhite: 0.08, alpha: 1).setFill(); bounds.fill()
        guard let image, image.size.width > 0, image.size.height > 0 else { return }
        let scale = min(bounds.width / image.size.width, bounds.height / image.size.height)
        let size = NSSize(width: image.size.width * scale, height: image.size.height * scale)
        image.draw(in: NSRect(x: (bounds.width-size.width)/2, y: (bounds.height-size.height)/2, width: size.width, height: size.height))
    }
    override func mouseDown(with event: NSEvent) { ignoredEvents += 1 }
    override func mouseUp(with event: NSEvent) { ignoredEvents += 1 }
    override func mouseDragged(with event: NSEvent) { ignoredEvents += 1 }
    override func rightMouseDown(with event: NSEvent) { ignoredEvents += 1 }
    override func rightMouseUp(with event: NSEvent) { ignoredEvents += 1 }
    override func rightMouseDragged(with event: NSEvent) { ignoredEvents += 1 }
    override func otherMouseDown(with event: NSEvent) { ignoredEvents += 1 }
    override func otherMouseUp(with event: NSEvent) { ignoredEvents += 1 }
    override func otherMouseDragged(with event: NSEvent) { ignoredEvents += 1 }
    override func scrollWheel(with event: NSEvent) { ignoredEvents += 1 }
    override func keyDown(with event: NSEvent) { ignoredEvents += 1 }
    override func keyUp(with event: NSEvent) { ignoredEvents += 1 }
}

@MainActor final class PreviewHost: NSObject, NSApplicationDelegate, NSWindowDelegate {
    let root: URL
    var panel: PreviewPanel!
    let pixels = PreviewPixels(frame: .zero)
    let label = NSTextField(labelWithString: "Waiting for guest image…")
    var timer: Timer?
    var frameCount = -1
    var frontBefore: pid_t = -1
    var cursorBefore = CGPoint.zero
    var activationObserver: NSObjectProtocol?
    var becameFrontmost = false
    init(root: URL) { self.root = root }
    func file(_ name: String) -> URL { root.appendingPathComponent(name) }
    func read(_ name: String, limit: Int = 65536) throws -> Data {
        let fd = open(file(name).path, O_RDONLY | O_NOFOLLOW)
        guard fd >= 0 else { throw NSError(domain: "viewer", code: 1) }
        let stream = FileHandle(fileDescriptor: fd, closeOnDealloc: true)
        var info = stat()
        guard fstat(fd, &info) == 0, info.st_uid == getuid(), info.st_mode & 0o077 == 0,
              info.st_mode & S_IFMT == S_IFREG, info.st_size <= limit else {
            try? stream.close(); throw NSError(domain: "viewer", code: 2)
        }
        let data = try stream.readToEnd() ?? Data(); try stream.close(); return data
    }
    func json(_ name: String) throws -> [String: Any] {
        try JSONSerialization.jsonObject(with: read(name)) as? [String: Any] ?? [:]
    }
    func write(_ name: String, _ value: [String: Any]) {
        guard let data = try? JSONSerialization.data(withJSONObject: value, options: .sortedKeys) else { return }
        let temporary = file(name + "." + UUID().uuidString + ".pending")
        let fd = open(temporary.path, O_CREAT | O_EXCL | O_WRONLY | O_NOFOLLOW, 0o600)
        guard fd >= 0 else { return }
        let written = data.withUnsafeBytes { Darwin.write(fd, $0.baseAddress, $0.count) }
        close(fd)
        if written == data.count { _ = rename(temporary.path, file(name).path) }
        unlink(temporary.path)
    }
    func applicationDidFinishLaunching(_ notification: Notification) {
        var info = stat()
        guard lstat(root.path, &info) == 0, info.st_uid == getuid(), info.st_mode & 0o077 == 0,
              info.st_mode & S_IFMT == S_IFDIR else { NSApplication.shared.terminate(nil); return }
        guard !FileManager.default.fileExists(atPath: file("close.json").path),
              let initial = try? json("state.json"),
              Date().timeIntervalSince1970 - (initial["heartbeat"] as? Double ?? 0) < 15 else {
            NSApplication.shared.terminate(nil); return
        }
        frontBefore = NSWorkspace.shared.frontmostApplication?.processIdentifier ?? -1
        cursorBefore = CGEvent(source: nil)?.location ?? .zero
        let name = (try? json("label.json")["id"] as? String) ?? "Guest"
        panel = PreviewPanel(contentRect: NSRect(x: 0, y: 0, width: 640, height: 504),
            styleMask: [.titled, .closable, .resizable, .nonactivatingPanel], backing: .buffered, defer: false)
        panel.title = "QuietWing · " + name + " · Read only"
        panel.isReleasedWhenClosed = false; panel.hidesOnDeactivate = false
        panel.becomesKeyOnlyIfNeeded = true; panel.isFloatingPanel = false
        panel.level = .normal; panel.delegate = self; panel.minSize = NSSize(width: 320, height: 264)
        let content = NSView(frame: NSRect(x: 0, y: 0, width: 640, height: 504))
        pixels.frame = NSRect(x: 0, y: 24, width: 640, height: 480)
        pixels.autoresizingMask = [.width, .height]
        label.frame = NSRect(x: 10, y: 3, width: 620, height: 18)
        label.autoresizingMask = [.width]; label.font = .systemFont(ofSize: 11)
        label.textColor = .secondaryLabelColor; label.lineBreakMode = .byTruncatingTail
        content.addSubview(pixels); content.addSubview(label); panel.contentView = content
        if let screen = NSScreen.main?.visibleFrame {
            panel.setFrameTopLeftPoint(NSPoint(x: screen.maxX-panel.frame.width-24, y: screen.maxY-32))
        }
        activationObserver = NSWorkspace.shared.notificationCenter.addObserver(
            forName: NSWorkspace.didActivateApplicationNotification, object: nil, queue: .main) { [weak self] note in
                MainActor.assumeIsolated {
                    if let active = note.userInfo?[NSWorkspace.applicationUserInfoKey] as? NSRunningApplication,
                       active.processIdentifier == getpid() { self?.becameFrontmost = true }
                }
            }
        panel.orderFrontRegardless()
        tick()
        timer = Timer.scheduledTimer(withTimeInterval: 0.1, repeats: true) { [weak self] _ in
            MainActor.assumeIsolated { self?.tick() }
        }
    }
    func tick() {
        if FileManager.default.fileExists(atPath: file("close.json").path) {
            panel.close(); NSApplication.shared.terminate(nil); return
        }
        let state = try? json("state.json")
        let age = Date().timeIntervalSince1970 - (state?["heartbeat"] as? Double ?? 0)
        let phase = state?["state"] as? String ?? "starting"
        if age > 15 {
            panel.close(); NSApplication.shared.terminate(nil); return
        }
        let frameAge = Date().timeIntervalSince1970 - (state?["capturedAt"] as? Double ?? 0)
        if phase == "waiting" {
            pixels.image = nil
            label.stringValue = "Waiting for the agent's desktop · Read only"
        } else if phase == "ended" || phase == "closed" || (phase == "watching" && frameAge > 3) {
            pixels.image = nil
            label.stringValue = "Session unavailable · Close and reopen to view again · Read only"
        } else if phase == "watching", let count = state?["frames"] as? Int {
            if count != frameCount {
                pixels.image = nil
                if let data = try? read("frame.png", limit: 16*1024*1024), let image = NSImage(data: data) {
                    pixels.image = image; frameCount = count
                }
            }
            let at = Date(timeIntervalSince1970: state?["capturedAt"] as? Double ?? 0)
            label.stringValue = pixels.image == nil ? "Waiting for a displayable guest image · Read only" : "Read only · Updated " + DateFormatter.localizedString(from: at, dateStyle: .none, timeStyle: .medium)
        }
        becameFrontmost = becameFrontmost || NSWorkspace.shared.frontmostApplication?.processIdentifier == getpid()
        write("window.json", ["pid": getpid(), "windowId": panel.windowNumber, "visible": panel.isVisible,
            "key": panel.isKeyWindow, "main": panel.isMainWindow, "canBecomeKey": panel.canBecomeKey,
            "canBecomeMain": panel.canBecomeMain, "becameFrontmost": becameFrontmost,
            "frontBefore": frontBefore, "frontCurrent": NSWorkspace.shared.frontmostApplication?.processIdentifier ?? -1,
            "cursorBefore": [cursorBefore.x, cursorBefore.y],
            "cursorCurrent": [CGEvent(source: nil)?.location.x ?? -1, CGEvent(source: nil)?.location.y ?? -1],
            "displayedFrames": frameCount, "imageAvailable": pixels.image != nil,
            "frame": [panel.frame.minX, panel.frame.minY, panel.frame.width, panel.frame.height],
            "readOnly": true, "ignoredPreviewEvents": pixels.ignoredEvents])
    }
    func windowWillClose(_ notification: Notification) {
        write("close.json", ["close": true]); NSApplication.shared.terminate(nil)
    }
    func applicationWillTerminate(_ notification: Notification) {
        timer?.invalidate()
        if let activationObserver { NSWorkspace.shared.notificationCenter.removeObserver(activationObserver) }
        try? FileManager.default.removeItem(at: file("frame.png"))
        write("close.json", ["close": true]); write("window-closed.json", ["closed": true])
    }
}
#if !VIEWER_TEST
@main struct ViewerMain {
    @MainActor static func main() {
        let args = CommandLine.arguments
        guard let index = args.firstIndex(of: "--run-root"), index+1 < args.count else { exit(2) }
        let app = NSApplication.shared; app.setActivationPolicy(.accessory)
        let host = PreviewHost(root: URL(fileURLWithPath: args[index+1])); app.delegate = host
        withExtendedLifetime(host) { app.run() }
    }
}
#endif
