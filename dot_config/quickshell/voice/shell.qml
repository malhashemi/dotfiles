// Dedicated Quickshell voice-typer HUD instance.
// Run:    qs -p ~/.config/quickshell/voice
// Driven by voice-typerd over IPC (target "voice", defined inside
// TranscriptionWindow), e.g.:
//   qs -p ~/.config/quickshell/voice ipc call voice show
//   qs -p ~/.config/quickshell/voice ipc call voice setState processing
import Quickshell

ShellRoot {
    id: root
    TranscriptionWindow {
        id: win
    }
}
