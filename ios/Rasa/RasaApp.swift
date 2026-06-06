import SwiftUI

@main
struct RasaApp: App {
    @StateObject private var model = AppModel()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(model)
                .task { await model.refresh() }
        }
    }
}

struct RootView: View {
    var body: some View {
        TabView {
            HomeRecordView()
                .tabItem { Label("Check in", systemImage: "mic.circle.fill") }
            TimelineView()
                .tabItem { Label("Timeline", systemImage: "list.bullet") }
            DashboardView()
                .tabItem { Label("Stats", systemImage: "chart.xyaxis.line") }
            DebriefView()
                .tabItem { Label("Debrief", systemImage: "play.rectangle.fill") }
        }
    }
}
