import Cocoa
import Foundation

// --- Data Model ---
struct SensorData: Codable {
    let temperature: Double
    let humidity: Double
    let battery: Int?
    let name: String?
}

// --- Efficient File Monitor ---
class FileMonitor {
    private let url: URL
    private var fileDescriptor: Int32 = -1
    private var source: DispatchSourceFileSystemObject?
    var onFileDidChange: (() -> Void)?

    init(url: URL) { self.url = url }

    func start() {
        fileDescriptor = open(url.path, O_EVTONLY)
        guard fileDescriptor != -1 else { return }
        source = DispatchSource.makeFileSystemObjectSource(fileDescriptor: fileDescriptor, eventMask: .extend, queue: DispatchQueue.global())
        source?.setEventHandler { [weak self] in self?.onFileDidChange?() }
        source?.setCancelHandler { [weak self] in if let fd = self?.fileDescriptor { close(fd) } }
        source?.resume()
    }
}

// --- Widget UI Controller ---
class GoveeWidgetController: NSViewController {
    var tempLabel: NSTextField!
    var humLabel: NSTextField!
    var titleLabel: NSTextField!
    let dataURL = FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("govee_data.json")
    var monitor: FileMonitor?

    override func loadView() {
        self.view = NSView(frame: NSRect(x: 0, y: 0, width: 180, height: 100))
        
        titleLabel = createLabel(text: "SENSOR", size: 9, weight: .bold, color: .secondaryLabelColor)
        titleLabel.frame = NSRect(x: 12, y: 75, width: 150, height: 15)
        
        tempLabel = createLabel(text: "--.-°", size: 36, weight: .semibold, color: .white)
        tempLabel.frame = NSRect(x: 10, y: 30, width: 160, height: 45)
        
        humLabel = createLabel(text: "--%", size: 14, weight: .medium, color: NSColor.systemGreen)
        humLabel.frame = NSRect(x: 12, y: 12, width: 100, height: 20)
        
        self.view.addSubview(titleLabel)
        self.view.addSubview(tempLabel)
        self.view.addSubview(humLabel)
        
        updateUI()
        monitor = FileMonitor(url: dataURL)
        monitor?.onFileDidChange = { [weak self] in DispatchQueue.main.async { self?.updateUI() } }
        monitor?.start()
    }

    private func createLabel(text: String, size: CGFloat, weight: NSFont.Weight, color: NSColor) -> NSTextField {
        let label = NSTextField(labelWithString: text)
        label.font = NSFont.systemFont(ofSize: size, weight: weight)
        label.textColor = color
        label.isEditable = false; label.isBezeled = false; label.drawsBackground = false
        return label
    }

    func updateUI() {
        do {
            let data = try Data(contentsOf: dataURL)
            let sensor = try JSONDecoder().decode(SensorData.self, from: data)
            let tempF = (sensor.temperature * 9/5) + 32
            tempLabel.stringValue = String(format: "%.1f°", tempF)
            humLabel.stringValue = String(format: "%.0f%% HUMIDITY", sensor.humidity)
            titleLabel.stringValue = "SENSOR \(sensor.name?.components(separatedBy: "_").last ?? "GOVEE")".uppercased()
        } catch { titleLabel.stringValue = "WAITING FOR DATA..." }
    }
}

// --- Widget Window ---
class WidgetWindow: NSPanel {
    init() {
        super.init(
            contentRect: NSRect(x: 0, y: 0, width: 180, height: 100),
            styleMask: [.borderless, .nonactivatingPanel],
            backing: .buffered, defer: false
        )
        
        // desktop level + stationary flags for reveal behavior
        self.level = NSWindow.Level(rawValue: Int(CGWindowLevelForKey(.desktopWindow)))
        self.collectionBehavior = [.canJoinAllSpaces, .stationary, .ignoresCycle, .fullScreenAuxiliary]
        
        self.isFloatingPanel = false
        self.isMovableByWindowBackground = true
        self.backgroundColor = NSColor(calibratedWhite: 0.1, alpha: 0.6)
        self.isOpaque = false
        self.hasShadow = false
        self.contentView?.wantsLayer = true
        self.contentView?.layer?.cornerRadius = 16
        self.hidesOnDeactivate = false
    }
}

class AppDelegate: NSObject, NSApplicationDelegate {
    var window: WidgetWindow!
    func applicationDidFinishLaunching(_ notification: Notification) {
        window = WidgetWindow()
        window.contentViewController = GoveeWidgetController()
        
        if let screen = NSScreen.main {
            // Position on the left side with 20px padding
            let x = screen.visibleFrame.minX + 20
            let y = (screen.visibleFrame.height / 2) - (window.frame.height / 2) // Centered vertically
            window.setFrameOrigin(NSPoint(x: x, y: y))
        }
        window.makeKeyAndOrderFront(nil)
        NSApp.setActivationPolicy(.accessory)
    }
}

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.run()
