import SwiftUI

/// Placeholder friend for the Strava-style social column.
/// Swap this out for real backend data once the friends API lands.
struct Friend: Identifiable, Hashable {
    let id = UUID()
    let name: String
    let lastFeeling: String   // emotion label, drives the emoji
    let valence: Double       // -1..1, drives the mood color
    let streakDays: Int
    let lastCheckin: String   // human-friendly "time ago"
    let kudos: Int

    var initials: String {
        let parts = name.split(separator: " ")
        let first = parts.first?.first.map(String.init) ?? ""
        let last = parts.dropFirst().first?.first.map(String.init) ?? ""
        return (first + last).uppercased()
    }
}

extension Friend {
    /// Temporary roster until the friends backend exists.
    static let placeholders: [Friend] = [
        Friend(name: "Abhi",    lastFeeling: "Excitement", valence:  0.62, streakDays: 12, lastCheckin: "8m ago",  kudos: 3),
        Friend(name: "Pooja",   lastFeeling: "Calm",       valence:  0.34, streakDays: 27, lastCheckin: "1h ago",  kudos: 7),
        Friend(name: "Patrick", lastFeeling: "Anxiety",    valence: -0.41, streakDays: 4,  lastCheckin: "3h ago",  kudos: 1),
    ]
}

struct FriendsView: View {
    private let friends = Friend.placeholders
    @State private var gaveKudos: Set<Friend.ID> = []

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 14) {
                    ForEach(friends) { friend in
                        FriendRow(friend: friend,
                                  gaveKudos: gaveKudos.contains(friend.id)) {
                            if gaveKudos.contains(friend.id) {
                                gaveKudos.remove(friend.id)
                            } else {
                                gaveKudos.insert(friend.id)
                            }
                        }
                    }
                }
                .padding()
            }
            .background(Theme.bg)
            .navigationTitle("Friends")
        }
    }
}

private struct FriendRow: View {
    let friend: Friend
    let gaveKudos: Bool
    let onKudos: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 12) {
                avatar
                VStack(alignment: .leading, spacing: 2) {
                    Text(friend.name).font(.headline)
                    Text("\(friend.lastCheckin) · \(friend.streakDays)-day streak")
                        .font(.caption).foregroundStyle(.secondary)
                }
                Spacer()
                Image(systemName: "flame.fill")
                    .foregroundStyle(.orange)
                Text("\(friend.streakDays)")
                    .font(.subheadline.bold())
            }

            HStack(spacing: 10) {
                Text(Theme.emoji(for: friend.lastFeeling)).font(.system(size: 30))
                VStack(alignment: .leading, spacing: 4) {
                    Text("Felt \(friend.lastFeeling.lowercased())").font(.subheadline)
                    ValenceBar(valence: friend.valence)
                }
                Circle().fill(Theme.valenceColor(friend.valence)).frame(width: 14, height: 14)
            }

            Divider()

            HStack {
                Button(action: onKudos) {
                    Label("\(friend.kudos + (gaveKudos ? 1 : 0))",
                          systemImage: gaveKudos ? "hands.clap.fill" : "hands.clap")
                        .font(.subheadline)
                        .foregroundStyle(gaveKudos ? Color.accentColor : .secondary)
                }
                .buttonStyle(.plain)
                Spacer()
                Text("Kudos").font(.caption).foregroundStyle(.secondary)
            }
        }
        .padding()
        .background(RoundedRectangle(cornerRadius: 16).fill(Color(.secondarySystemGroupedBackground)))
    }

    private var avatar: some View {
        Circle()
            .fill(Theme.valenceColor(friend.valence).opacity(0.85))
            .frame(width: 44, height: 44)
            .overlay(
                Text(friend.initials)
                    .font(.subheadline.bold())
                    .foregroundStyle(.white)
            )
    }
}
