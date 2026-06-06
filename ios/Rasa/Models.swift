import Foundation

struct EmotionScore: Codable, Identifiable, Hashable {
    let name: String
    let score: Double
    var id: String { name }
}

struct Snapshot: Codable, Identifiable, Hashable {
    let id: String
    let userId: String
    let timestamp: String
    let emotionLabel: String
    let valence: Double
    let arousal: Double
    let intensity: Double
    let contextTag: String
    let transcript: String?
    let summary: String
    let audioUrl: String?
    let topEmotions: [EmotionScore]
    let source: String
    let provider: String

    var date: Date { ISO8601DateFormatter().date(from: timestamp) ?? Date() }
}

struct HeatmapBucket: Codable, Identifiable, Hashable {
    let hour: Int
    let avgValence: Double
    let count: Int
    var id: Int { hour }
}

struct SeriesPoint: Codable, Identifiable, Hashable {
    let timestamp: String
    let valence: Double
    let arousal: Double
    var id: String { timestamp }
    var date: Date { ISO8601DateFormatter().date(from: timestamp) ?? Date() }
}

struct TriggerStat: Codable, Identifiable, Hashable {
    let contextTag: String
    let count: Int
    let avgValence: Double
    var id: String { contextTag }
}

struct LabelCount: Codable, Identifiable, Hashable {
    let label: String
    let count: Int
    var id: String { label }
}

struct DashboardResponse: Codable {
    let userId: String
    let date: String
    let streakDays: Int
    let checkinCount: Int
    let avgValence: Double
    let avgArousal: Double
    let heatmap: [HeatmapBucket]
    let series: [SeriesPoint]
    let topTriggers: [TriggerStat]
    let labelsBreakdown: [LabelCount]
}

struct Debrief: Codable {
    let id: String
    let userId: String
    let date: String
    let status: String
    let script: String?
    let audioUrl: String?
    let videoUrl: String?
    let shareUrl: String?
    let error: String?
}

struct DebriefStart: Codable {
    let debriefId: String
    let status: String
}

struct RecordingStart: Codable {
    let recordingId: String
    let status: String
}

struct Recording: Codable {
    let id: String
    let status: String
    let chunkCount: Int
    let chunksDone: Int
    let snapshotIds: [String]
    let error: String?
}
