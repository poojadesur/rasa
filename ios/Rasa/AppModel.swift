import Foundation

@MainActor
final class AppModel: ObservableObject {
    @Published var snapshots: [Snapshot] = []
    @Published var dashboard: DashboardResponse?
    @Published var lastError: String?
    @Published var isRefreshing = false

    func refresh() async {
        isRefreshing = true
        defer { isRefreshing = false }
        do {
            async let snaps = APIClient.shared.listCheckins()
            async let dash = APIClient.shared.getDashboard()
            self.snapshots = try await snaps
            self.dashboard = try await dash
            self.lastError = nil
        } catch {
            self.lastError = "Couldn't reach the backend at \(Config.baseURL.absoluteString). Is it running?"
        }
    }
}
