import Cocoa
import Foundation

// --- 1. Data Model ---
struct SensorData: Codable {
    let temperature: Double
    let humidity: Double
    let battery: Int?
}

// --- 2. Menu Bar Controller ---
class GoveeMenuBarApp: NSObject, NSApplicationDelegate {
    var statusItem: NSStatusItem!
    var timer: Timer?
    let dataURL = FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("govee_data.json")
    
    func applicationDidFinishLaunching(_ notification: Notification) {
        // Create the system status item
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        
        if let button = statusItem.button {
            button.title = "H: --%"
            button.font = NSFont.monospacedDigitSystemFont(ofSize: 13, weight: .semibold)
        }
        
        constructMenu()
        updateUI()
        
        // Refresh every 5 seconds
        timer = Timer.scheduledTimer(withTimeInterval: 5.0, repeats: true) { [weak self] _ in
            self?.updateUI()
        }
        
        print("Govee Menu Bar App is now active!")
    }
    
    func constructMenu() {
        let menu = NSMenu()
        menu.addItem(NSMenuItem(title: "Temperature: --.-°F", action: nil, keyEquivalent: ""))
        menu.addItem(NSMenuItem(title: "Battery: --%", action: nil, keyEquivalent: ""))
        menu.addItem(NSMenuItem.separator())
        let graphItem = NSMenuItem(title: "24h Graph", action: #selector(openGraph), keyEquivalent: "g")
        graphItem.target = self
        menu.addItem(graphItem)
        menu.addItem(NSMenuItem(title: "Refresh Now", action: #selector(forceRefresh), keyEquivalent: "r"))
        menu.addItem(NSMenuItem(title: "Quit", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q"))
        statusItem.menu = menu
    }

    @objc func openGraph() {
        let home = FileManager.default.homeDirectoryForCurrentUser.path
        let scriptPath = "\(home)/govee_graph.py"
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/opt/homebrew/bin/uv")
        process.arguments = ["run", "--with", "redis", "python3", scriptPath]
        try? process.run()
    }
    
    @objc func forceRefresh() {
        updateUI()
    }
    
    func updateUI() {
        do {
            let data = try Data(contentsOf: dataURL)
            let sensor = try JSONDecoder().decode(SensorData.self, from: data)
            
            DispatchQueue.main.async {
                if let button = self.statusItem.button {
                    button.title = String(format: "H: %.0f%%", sensor.humidity)
                }
                
                if let menu = self.statusItem.menu {
                    let tempF = (sensor.temperature * 9/5) + 32
                    menu.item(at: 0)?.title = String(format: "Temperature: %.1f°F", tempF)
                    let battery = sensor.battery ?? 0
                    menu.item(at: 1)?.title = "Battery: \(battery)%"
                }
            }
        } catch {
            DispatchQueue.main.async {
                self.statusItem.button?.title = "H: ERR"
            }
        }
    }
}

// --- 3. App Initialization ---
let app = NSApplication.shared
let delegate = GoveeMenuBarApp()
app.delegate = delegate

// Set policy to .accessory to hide from Dock and allow Menu Bar existence
app.setActivationPolicy(.accessory)

// Start the event loop
app.run()
