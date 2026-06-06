import SwiftUI

struct HomeRecordView: View {
    @EnvironmentObject var model: AppModel
    @StateObject private var recorder = AudioRecorder()

    @State private var longSession = false
    @State private var busy = false
    @State private var status = ""
    @State private var lastSnapshot: Snapshot?
    @State private var permissionDenied = false

    var body: some View {
        NavigationStack {
            VStack(spacing: 28) {
                Text(longSession ? "Record a whole conversation. I'll pull out just your voice and chart how you felt."
                                  : "Tap and tell me how it's going. A few seconds is plenty.")
                    .font(.callout)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal)

                Toggle("Long session (full conversation)", isOn: $longSession)
                    .padding(.horizontal, 40)
                    .disabled(recorder.isRecording || busy)

                Spacer()

                waveform

                Text(recorder.isRecording ? timeString(recorder.elapsed) : (status.isEmpty ? " " : status))
                    .font(.headline.monospacedDigit())
                    .foregroundStyle(recorder.isRecording ? .primary : .secondary)

                micButton

                if let s = lastSnapshot {
                    EmotionCard(snapshot: s).padding(.horizontal)
                }

                Spacer()
            }
            .padding(.vertical)
            .navigationTitle("Rasa")
            .alert("Microphone access needed", isPresented: $permissionDenied) {
                Button("OK", role: .cancel) {}
            } message: {
                Text("Enable the microphone for Rasa in Settings to record check-ins.")
            }
        }
    }

    private var waveform: some View {
        HStack(spacing: 4) {
            ForEach(0..<24, id: \.self) { i in
                let phase = Double(i) / 24
                let h = recorder.isRecording
                    ? 8 + recorder.level * 60 * (0.5 + 0.5 * sin(phase * .pi * 3 + recorder.elapsed * 6))
                    : 8
                Capsule()
                    .fill(recorder.isRecording ? Color.accentColor : Color.secondary.opacity(0.3))
                    .frame(width: 5, height: max(6, h))
            }
        }
        .frame(height: 80)
        .animation(.easeOut(duration: 0.08), value: recorder.level)
    }

    private var micButton: some View {
        Button {
            Task { await toggle() }
        } label: {
            ZStack {
                Circle()
                    .fill(recorder.isRecording ? Color.red : Color.accentColor)
                    .frame(width: 96, height: 96)
                    .shadow(radius: 8)
                if busy {
                    ProgressView().tint(.white)
                } else {
                    Image(systemName: recorder.isRecording ? "stop.fill" : "mic.fill")
                        .font(.system(size: 36, weight: .bold))
                        .foregroundStyle(.white)
                }
            }
        }
        .disabled(busy)
    }

    private func toggle() async {
        if recorder.isRecording {
            guard let url = recorder.stop() else { return }
            await upload(url)
        } else {
            guard await recorder.requestPermission() else { permissionDenied = true; return }
            do { try recorder.start() } catch { status = "Couldn't start recording." }
            lastSnapshot = nil
        }
    }

    private func upload(_ url: URL) async {
        busy = true
        defer { busy = false }
        do {
            if longSession {
                status = "Uploading conversation…"
                let start = try await APIClient.shared.uploadRecording(fileURL: url)
                status = "Isolating your voice…"
                try await pollRecording(start.recordingId)
                status = "Done — added to your timeline."
            } else {
                status = "Reading the room…"
                let snap = try await APIClient.shared.uploadCheckin(fileURL: url)
                lastSnapshot = snap
                status = ""
            }
            await model.refresh()
        } catch {
            status = "Upload failed. Is the backend running?"
        }
    }

    private func pollRecording(_ id: String) async throws {
        for _ in 0..<60 {
            let rec = try await APIClient.shared.getRecording(id)
            status = "Analyzing \(rec.chunksDone)/\(max(rec.chunkCount, 1)) segments…"
            if rec.status == "ready" || rec.status == "error" { return }
            try await Task.sleep(nanoseconds: 2_000_000_000)
        }
    }

    private func timeString(_ t: TimeInterval) -> String {
        String(format: "%01d:%02d", Int(t) / 60, Int(t) % 60)
    }
}
