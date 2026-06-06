import SwiftUI

struct EmotionCard: View {
    let snapshot: Snapshot

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text(Theme.emoji(for: snapshot.emotionLabel)).font(.system(size: 34))
                VStack(alignment: .leading) {
                    Text(snapshot.emotionLabel).font(.title3.bold())
                    Text(snapshot.date.hm).font(.caption).foregroundStyle(.secondary)
                }
                Spacer()
                Circle().fill(Theme.valenceColor(snapshot.valence)).frame(width: 18, height: 18)
            }

            ValenceBar(valence: snapshot.valence)

            if !snapshot.topEmotions.isEmpty {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 6) {
                        ForEach(snapshot.topEmotions.prefix(4)) { e in
                            Text("\(e.name) \(Int(e.score * 100))%")
                                .font(.caption2)
                                .padding(.horizontal, 8).padding(.vertical, 4)
                                .background(Capsule().fill(Color.secondary.opacity(0.15)))
                        }
                    }
                }
            }

            if !snapshot.summary.isEmpty {
                Text(snapshot.summary).font(.footnote).foregroundStyle(.secondary)
            }
        }
        .padding()
        .background(RoundedRectangle(cornerRadius: 16).fill(Color(.secondarySystemGroupedBackground)))
    }
}

struct ValenceBar: View {
    let valence: Double  // -1..1
    var body: some View {
        GeometryReader { geo in
            ZStack(alignment: .leading) {
                Capsule().fill(Color.secondary.opacity(0.15))
                Capsule()
                    .fill(Theme.valenceColor(valence))
                    .frame(width: geo.size.width * CGFloat((valence + 1) / 2))
            }
        }
        .frame(height: 8)
    }
}

struct SnapshotRow: View {
    let snapshot: Snapshot
    var body: some View {
        HStack(spacing: 12) {
            Text(Theme.emoji(for: snapshot.emotionLabel)).font(.title2)
            VStack(alignment: .leading, spacing: 2) {
                Text(snapshot.emotionLabel).font(.headline)
                Text(snapshot.summary.isEmpty ? snapshot.contextTag : snapshot.summary)
                    .font(.caption).foregroundStyle(.secondary).lineLimit(1)
            }
            Spacer()
            VStack(alignment: .trailing, spacing: 4) {
                Text(snapshot.date.hm).font(.caption2).foregroundStyle(.secondary)
                Circle().fill(Theme.valenceColor(snapshot.valence)).frame(width: 12, height: 12)
            }
        }
        .padding(.vertical, 4)
    }
}

struct StatPill: View {
    let title: String
    let value: String
    let systemImage: String
    var body: some View {
        VStack(spacing: 6) {
            Image(systemName: systemImage).font(.title3)
            Text(value).font(.title3.bold())
            Text(title).font(.caption2).foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 14)
        .background(RoundedRectangle(cornerRadius: 14).fill(Color(.secondarySystemGroupedBackground)))
    }
}
