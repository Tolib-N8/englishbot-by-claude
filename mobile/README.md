# English Tutor — mobile (Flutter)

A Flutter client for the English Tutor backend. Talks to your FastAPI server
over the network — set the backend URL in the app's Settings.

## Screens

- **Home** — IELTS/CEFR level, CEFR scale, target band selector, roadmap, card stats
- **Chat** — conversations with the tutor (streamed replies, correction panel), "save session"
- **Grammar** — generate & answer exercises (topics suggested from your roadmap)
- **Cards** — SRS flashcard review (Again / Hard / Good / Easy)
- **Settings** — backend URL + connection test

## Connecting to the backend

The backend must run on your computer (`englishbot start`) where Claude Code is
logged in. The phone reaches it via **Tailscale**:

1. Install Tailscale on the computer and the phone (same account), bring both up.
2. Find the computer's Tailscale IP: `tailscale ip -4` → e.g. `100.x.y.z`.
3. In the app → Settings → backend URL: `http://100.x.y.z:8000` → "Проверить связь".

> On the same Wi-Fi you can instead use the LAN IP, e.g. `http://192.168.1.42:8000`.

Cleartext `http://` to private IPs is allowed (set in AndroidManifest).

## Develop / run

```bash
# Uses the user-local Flutter SDK at ~/flutter
~/flutter/bin/flutter pub get
~/flutter/bin/flutter run            # on a connected device/emulator
~/flutter/bin/flutter analyze
~/flutter/bin/flutter test
```

## Build an Android APK

Requires the Android SDK (`~/flutter/bin/flutter doctor` will tell you what's
missing — typically install Android Studio or the command-line tools, then
`flutter doctor --android-licenses`).

```bash
~/flutter/bin/flutter build apk --release
# output: build/app/outputs/flutter-apk/app-release.apk  → copy to your phone
```

## Notes

- This client is for personal use against your own backend. Publishing publicly
  would require switching the backend's AI layer from the Claude Pro/Agent-SDK
  login to the paid Anthropic API, plus multi-user auth and hosting.
