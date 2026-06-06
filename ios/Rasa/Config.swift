import Foundation

enum Config {
    /// The iOS Simulator shares the Mac's network, so localhost reaches the backend.
    /// For a real device, set this to your Mac's LAN IP (e.g. http://192.168.1.20:8000).
    static let baseURL = URL(string: "http://127.0.0.1:8000")!
    static let userId = "demo-user"
}
