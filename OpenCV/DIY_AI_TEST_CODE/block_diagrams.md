# InMoov Portfolio: Chapter 3 Block Diagrams

You can copy and paste the code blocks below into the [Mermaid Live Editor](https://mermaid.live/) to generate high-quality images for your report and slides.

## 1. Overall System Architecture
This diagram shows how data flows from your hand/voice into the InMoov brain and out to the robot.

```mermaid
graph TD
    A[Webcam Feed] --> B[Gesture Module]
    B --> C{Decision Engine}
    C -->|Real-time| D[Virtual Hand Simulator]
    C -->|Real-time| E[Arduino Servo Driver]
    F[Text Input] --> G[Keeper of Words DB]
    H[Voice Input] --> I[Voice Module: Speech-to-Text]
    I --> F
    G --> C
    E --> J[Physical InMoov Arm]
```

## 2. The Gesture Processing Pipeline ("The Assembly Line")
This diagram explains the mathematical journey from a raw camera image to a smooth servo movement.

```mermaid
graph LR
    A[Raw Image] --> B[AI Hand Tracking]
    B --> C[Finger Curl Ratios]
    C --> D[Normalization 0.0 - 1.0]
    D --> E[Servo Mapping]
    E --> F[EMA Smoothing Filter]
    F --> G[Command Output]
```

## 3. Database: "Keeper of Words" Workflow
This diagram explains how signs are recorded and retrieved for later use.

```mermaid
sequenceDiagram
    User->>Gesture Module: Performs Gesture
    User->>Gesture Module: Press 'K' (Snapshot)
    Gesture Module->>User: "Name this gesture?"
    User->>Gesture Module: Types "Peace"
    Gesture Module->>Database: Save { "peace": [angles...] }
    Note over Database: gestures.json
```
