import AVKit
import SwiftUI

struct DebriefView: View {
    @EnvironmentObject var model: AppModel

    @State private var debrief: Debrief?
    @State private var generating = false
    @State private var status = ""

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 20) {
                    if let d = debrief {
                        if let url = APIClient.shared.absoluteURL(d.videoUrl) {
                            VideoPlayer(player: AVPlayer(url: url))
                                .frame(height: 220)
                                .clipShape(RoundedRectangle(cornerRadius: 16))
                        }
                        if let script = d.script, !script.isEmpty {
                            card("Today's debrief") {
                                Text(script).font(.body)
                            }
                        }
                        statusLine(d)
                        if let share = d.shareUrl, let url = URL(string: share) {
                            ShareLink(item: url) {
                                Label("Share debrief", systemImage: "square.and.arrow.up")
                                    .frame(maxWidth: .infinity).padding(.vertical, 10)
                                    .background(RoundedRectangle(cornerRadius: 12).fill(Color.secondary.opacity(0.15)))
                            }
                        }
                    } else {
                        ContentUnavailableView("End-of-day debrief",
                                               systemImage: "play.rectangle.fill",
                                               description: Text("Generate a personalized recap of your emotional day — narrated by your Rasa avatar."))
                            .padding(.top, 60)
                    }

                    Button {
                        Task { await generate() }
                    } label: {
                        HStack(spacing: 8) {
                            if generating { ProgressView().tint(.white) }
                            Text(generating ? (status.isEmpty ? "Working…" : status) : "Generate today's debrief")
                                .fontWeight(.semibold)
                        }
                        .frame(maxWidth: .infinity).padding()
                        .background(Color.accentColor).foregroundStyle(.white)
                        .clipShape(RoundedRectangle(cornerRadius: 14))
                    }
                    .disabled(generating)
                }
                .padding()
            }
            .background(Theme.bg)
            .navigationTitle("Debrief")
        }
    }

    @ViewBuilder
    private func statusLine(_ d: Debrief) -> some View {
        switch d.status {
        case "ready":
            if d.videoUrl == nil {
                Label("Script ready (add a Tavus key for the video).", systemImage: "doc.text")
                    .font(.caption).foregroundStyle(.secondary)
            }
        case "error":
            Label(d.error ?? "Something went wrong.", systemImage: "exclamationmark.triangle")
                .font(.caption).foregroundStyle(.red)
        default:
            Label("Status: \(d.status)…", systemImage: "hourglass").font(.caption).foregroundStyle(.secondary)
        }
    }

    private func generate() async {
        generating = true
        defer { generating = false }
        do {
            status = "Writing your script…"
            let start = try await APIClient.shared.generateDebrief()
            for _ in 0..<60 {
                let d = try await APIClient.shared.getDebrief(start.debriefId)
                debrief = d
                switch d.status {
                case "scripting": status = "Writing your script…"
                case "synthesizing": status = "Finding the words…"
                case "rendering": status = "Rendering your video…"
                default: break
                }
                if d.status == "ready" || d.status == "error" { return }
                try await Task.sleep(nanoseconds: 2_500_000_000)
            }
        } catch {
            status = "Couldn't generate. Is the backend running?"
        }
    }

    private func card<Content: View>(_ title: String, @ViewBuilder content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(title).font(.headline)
            content()
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(RoundedRectangle(cornerRadius: 16).fill(Color(.secondarySystemGroupedBackground)))
    }
}
