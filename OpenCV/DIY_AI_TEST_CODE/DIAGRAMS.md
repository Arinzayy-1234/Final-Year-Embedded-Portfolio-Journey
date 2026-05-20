# Chapter 3: Block Diagrams for InMoov Portfolio

## 1. Overall System Architecture
```mermaid
graph TD
    A[Webcam Feed] --> B[Gesture Module]
    B --> C{Decision Engine}
    C -->|Real-time| D[Virtual Hand Sync]
    C -->|Real-time| E[Arduino Servo Driver]
    F[Text Input] --> G[Keeper of Words DB]
    H[Voice Input] --> I[Speech-to-Text]
    I --> F
    G --> C
    E --> J[Physical InMoov Arm]
```

## 2. The Gesture Processing Pipeline (The "Assembly Line")
```mermaid
graph LR
    A[Raw Image] --> B[AI Landmark Detection]
    B --> C[Finger Ratios & Wrist Angle]
    C --> D[Normalization 0.0 - 1.0]
    D --> E[Servo Mapping 20 - 160]
    E --> F[EMA Smoothing Filter]
    F --> G[Servo Command Output]
```

## 3. Voice Module Workflow
```mermaid
graph TD
    A[User speaks 'Peace'] --> B[Microphone]
    B --> C[SpeechRecognition Engine]
    C --> D[Text: 'peace']
    D --> E{Check Database}
    E -->|Found| F[Retrieve Servo Angles]
    F --> G[Move Virtual & Physical Hand]
    E -->|Not Found| H[Prompt: 'Add this sign?']
```

## 4. Database "Keeper of Words" Sequence
```mermaid
sequenceDiagram
    User->>Gesture Module: Performs Sign
    User->>Gesture Module: Press 'K' (Snapshot)
    Gesture Module->>User: "Name this gesture?"
    User->>Gesture Module: Types "Peace"
    Gesture Module->>Database: Save { "peace": [angles...] }
    Note over Database: Gestures.json
```
