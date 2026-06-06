import Foundation

enum APIError: Error { case badStatus(Int), badURL }

final class APIClient {
    static let shared = APIClient()

    private let base = Config.baseURL
    private let userId = Config.userId

    private var decoder: JSONDecoder {
        let d = JSONDecoder()
        d.keyDecodingStrategy = .convertFromSnakeCase
        return d
    }

    /// Resolve a possibly-relative media/video URL (e.g. "/media/x.wav") against base.
    func absoluteURL(_ path: String?) -> URL? {
        guard let path, !path.isEmpty else { return nil }
        if path.hasPrefix("http") { return URL(string: path) }
        return URL(string: path, relativeTo: base)
    }

    // MARK: Check-ins

    func uploadCheckin(fileURL: URL) async throws -> Snapshot {
        try await uploadAudio(path: "/checkins", fileURL: fileURL, as: Snapshot.self)
    }

    func listCheckins(date: String? = nil) async throws -> [Snapshot] {
        var comps = URLComponents(url: base.appendingPathComponent("checkins"), resolvingAgainstBaseURL: false)!
        comps.queryItems = [URLQueryItem(name: "user_id", value: userId)]
        if let date { comps.queryItems?.append(URLQueryItem(name: "date", value: date)) }
        return try await get(comps.url!, as: [Snapshot].self)
    }

    // MARK: Recordings (long conversation)

    func uploadRecording(fileURL: URL) async throws -> RecordingStart {
        try await uploadAudio(path: "/recordings", fileURL: fileURL, as: RecordingStart.self)
    }

    func getRecording(_ id: String) async throws -> Recording {
        try await get(base.appendingPathComponent("recordings/\(id)"), as: Recording.self)
    }

    // MARK: Dashboard

    func getDashboard() async throws -> DashboardResponse {
        var comps = URLComponents(url: base.appendingPathComponent("dashboard"), resolvingAgainstBaseURL: false)!
        comps.queryItems = [URLQueryItem(name: "user_id", value: userId)]
        return try await get(comps.url!, as: DashboardResponse.self)
    }

    // MARK: Debrief

    func generateDebrief(script: String? = nil) async throws -> DebriefStart {
        var body: [String: Any] = ["user_id": userId]
        if let script { body["script"] = script }
        var req = URLRequest(url: base.appendingPathComponent("debrief/generate"))
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.httpBody = try JSONSerialization.data(withJSONObject: body)
        return try await send(req, as: DebriefStart.self)
    }

    func getDebrief(_ id: String) async throws -> Debrief {
        try await get(base.appendingPathComponent("debrief/\(id)"), as: Debrief.self)
    }

    // MARK: Plumbing

    private func get<T: Decodable>(_ url: URL, as type: T.Type) async throws -> T {
        try await send(URLRequest(url: url), as: type)
    }

    private func send<T: Decodable>(_ request: URLRequest, as type: T.Type) async throws -> T {
        let (data, resp) = try await URLSession.shared.data(for: request)
        guard let http = resp as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
            throw APIError.badStatus((resp as? HTTPURLResponse)?.statusCode ?? -1)
        }
        return try decoder.decode(T.self, from: data)
    }

    private func uploadAudio<T: Decodable>(path: String, fileURL: URL, as type: T.Type) async throws -> T {
        let boundary = "Boundary-\(UUID().uuidString)"
        var req = URLRequest(url: base.appendingPathComponent(String(path.dropFirst())))
        req.httpMethod = "POST"
        req.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        let filename = fileURL.lastPathComponent
        let mime = filename.hasSuffix(".wav") ? "audio/wav" : "audio/m4a"
        let audioData = try Data(contentsOf: fileURL)

        var body = Data()
        func append(_ s: String) { body.append(s.data(using: .utf8)!) }
        append("--\(boundary)\r\n")
        append("Content-Disposition: form-data; name=\"user_id\"\r\n\r\n")
        append("\(userId)\r\n")
        append("--\(boundary)\r\n")
        append("Content-Disposition: form-data; name=\"file\"; filename=\"\(filename)\"\r\n")
        append("Content-Type: \(mime)\r\n\r\n")
        body.append(audioData)
        append("\r\n--\(boundary)--\r\n")
        req.httpBody = body

        return try await send(req, as: type)
    }
}
