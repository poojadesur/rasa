import SwiftUI

struct TimelineView: View {
    @EnvironmentObject var model: AppModel

    var body: some View {
        NavigationStack {
            Group {
                if let err = model.lastError, model.snapshots.isEmpty {
                    ContentUnavailableView("Can't load your day", systemImage: "wifi.slash", description: Text(err))
                } else if model.snapshots.isEmpty {
                    ContentUnavailableView("No moments yet", systemImage: "waveform",
                                           description: Text("Record a check-in and it'll show up here."))
                } else {
                    List {
                        Section {
                            ForEach(model.snapshots.sorted { $0.timestamp > $1.timestamp }) { snap in
                                SnapshotRow(snapshot: snap)
                            }
                        } header: {
                            Text("\(model.snapshots.count) moments today")
                        }
                    }
                }
            }
            .navigationTitle("Timeline")
            .refreshable { await model.refresh() }
        }
    }
}
