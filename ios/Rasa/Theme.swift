import SwiftUI

enum Theme {
    /// Valence -1 (red) → 0 (amber) → +1 (green).
    static func valenceColor(_ v: Double) -> Color {
        let t = max(0, min(1, (v + 1) / 2))
        return Color(hue: 0.0 + t * 0.33, saturation: 0.72, brightness: 0.92)
    }

    static func emoji(for label: String) -> String {
        switch label.lowercased() {
        case let l where l.contains("joy") || l.contains("ecstasy") || l.contains("amus"): return "😄"
        case let l where l.contains("satisf") || l.contains("content") || l.contains("calm") || l.contains("relief"): return "🙂"
        case let l where l.contains("excit") || l.contains("triumph") || l.contains("pride"): return "🤩"
        case let l where l.contains("love") || l.contains("ador") || l.contains("romance"): return "🥰"
        case let l where l.contains("sad") || l.contains("disappoint") || l.contains("grief"): return "😔"
        case let l where l.contains("anx") || l.contains("fear") || l.contains("distress") || l.contains("horror"): return "😰"
        case let l where l.contains("anger") || l.contains("contempt") || l.contains("disgust"): return "😠"
        case let l where l.contains("tired") || l.contains("bored"): return "😴"
        case let l where l.contains("pain") || l.contains("suffer"): return "😣"
        default: return "🎭"
        }
    }

    static var bg: Color { Color(.systemGroupedBackground) }
}

extension Date {
    var hm: String {
        let f = DateFormatter()
        f.dateFormat = "h:mm a"
        return f.string(from: self)
    }
}
