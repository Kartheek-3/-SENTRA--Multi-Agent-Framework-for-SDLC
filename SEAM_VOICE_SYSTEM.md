# SEAM Voice System

## Current State

No voice input or speech output exists in the standalone IDE.

## Target Capabilities

- Optional voice dictation into the chat input.
- Optional speech playback for agent summaries.
- No automatic voice activation.
- No recording persistence unless explicitly enabled.

## Implementation Plan

1. Add UI capability detection.
2. Add local browser speech-to-text where available.
3. Add permission notices before microphone use.
4. Keep transcript text editable before sending.
5. Attach transcript messages to conversation history only after submit.

Voice should remain an optional accessibility feature, not a required part of core workflow execution.
