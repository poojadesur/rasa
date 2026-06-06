import Charts
import SwiftUI

struct DashboardView: View {
    @EnvironmentObject var model: AppModel

    var body: some View {
        NavigationStack {
            ScrollView {
                if let d = model.dashboard, d.checkinCount > 0 {
                    VStack(spacing: 18) {
                        statRow(d)
                        valenceChart(d)
                        heatmap(d)
                        triggers(d)
                        labels(d)
                    }
                    .padding()
                } else {
                    ContentUnavailableView("Your stats will appear here",
                                           systemImage: "chart.xyaxis.line",
                                           description: Text("Log a few check-ins to build your emotional fitness report."))
                        .padding(.top, 80)
                }
            }
            .background(Theme.bg)
            .navigationTitle("Stats")
            .refreshable { await model.refresh() }
        }
    }

    private func statRow(_ d: DashboardResponse) -> some View {
        HStack(spacing: 12) {
            StatPill(title: "Day streak", value: "\(d.streakDays)", systemImage: "flame.fill")
            StatPill(title: "Moments", value: "\(d.checkinCount)", systemImage: "waveform")
            StatPill(title: "Avg mood", value: String(format: "%+.2f", d.avgValence), systemImage: "face.smiling")
        }
    }

    private func valenceChart(_ d: DashboardResponse) -> some View {
        card("Mood through the day") {
            Chart(d.series) { p in
                LineMark(x: .value("Time", p.date), y: .value("Valence", p.valence))
                    .interpolationMethod(.catmullRom)
                PointMark(x: .value("Time", p.date), y: .value("Valence", p.valence))
                    .foregroundStyle(Theme.valenceColor(p.valence))
            }
            .chartYScale(domain: -1...1)
            .frame(height: 160)
        }
    }

    private func heatmap(_ d: DashboardResponse) -> some View {
        card("Emotional heatmap") {
            VStack(alignment: .leading, spacing: 6) {
                HStack(spacing: 3) {
                    ForEach(d.heatmap) { b in
                        RoundedRectangle(cornerRadius: 3)
                            .fill(b.count == 0 ? Color.secondary.opacity(0.12) : Theme.valenceColor(b.avgValence))
                            .frame(height: 26)
                    }
                }
                HStack {
                    Text("12a").font(.system(size: 8)); Spacer()
                    Text("12p").font(.system(size: 8)); Spacer()
                    Text("11p").font(.system(size: 8))
                }
                .foregroundStyle(.secondary)
            }
        }
    }

    private func triggers(_ d: DashboardResponse) -> some View {
        card("What moved you") {
            if d.topTriggers.isEmpty {
                Text("No clear patterns yet.").font(.footnote).foregroundStyle(.secondary)
            } else {
                VStack(spacing: 10) {
                    ForEach(d.topTriggers) { t in
                        HStack {
                            Text(t.contextTag.capitalized).font(.subheadline)
                            Spacer()
                            Text("\(t.count)×").font(.caption).foregroundStyle(.secondary)
                            Circle().fill(Theme.valenceColor(t.avgValence)).frame(width: 12, height: 12)
                        }
                    }
                }
            }
        }
    }

    private func labels(_ d: DashboardResponse) -> some View {
        card("Feelings logged") {
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    ForEach(d.labelsBreakdown) { l in
                        HStack(spacing: 4) {
                            Text(Theme.emoji(for: l.label))
                            Text("\(l.label) ×\(l.count)").font(.caption)
                        }
                        .padding(.horizontal, 10).padding(.vertical, 6)
                        .background(Capsule().fill(Color.secondary.opacity(0.12)))
                    }
                }
            }
        }
    }

    private func card<Content: View>(_ title: String, @ViewBuilder content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(title).font(.headline)
            content()
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(RoundedRectangle(cornerRadius: 16).fill(Color(.secondarySystemGroupedBackground)))
    }
}
