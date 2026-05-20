# InMoov Project: Chapter 3 Visual Assets

## 1. System Block Diagram
This diagram shows how all modules (Voice, Text, Database, and Physical Hand) talk to each other.

```mermaid
graph TD
    subgraph Input Sources
        V[Voice Command] --> VM[Voice Module]
        T[Text Command] --> DB_Lookup[Database Lookup]
        C[Webcam Feed] --> GM[Gesture Module]
    end

    subgraph Logic Engine
        VM --> DB_Lookup
        DB_Lookup -->|Angles| Controller[Hand Controller]
        GM -->|Real-time Tracking| Controller
    end

    subgraph Outputs
        Controller --> VH[Python Virtual Hand]
        Controller --> AD[Arduino Driver]
        AD --> PH[Physical InMoov Arm]
    end

    DB[(Keeper of Words DB)] <--> DB_Lookup
```

## 2. Gesture Pipeline (Assembly Line)
The step-by-step math journey of a single finger.

```mermaid
graph LR
    A[Image] --> B[MediaPipe]
    B --> C[Finger Ratio]
    C --> D[Normalization]
    D --> E[Servo Mapping]
    E --> F[EMA Smoothing]
    F --> G[Final Degree]
```

## 3. Database Workflow
How we save and retrieve gestures.

```mermaid
sequenceDiagram
    participant U as User
    participant G as Gesture Module
    participant D as Database (JSON)
    
    U->>G: Performs sign + Press 'K'
    G->>U: "What is the name?"
    U->>G: "Peace"
    G->>D: Save {"peace": [angles...]}
    
    Note over U,D: Later Retrieval
    
    U->>G: Speak/Type "Peace"
    G->>D: Find "peace"
    D->>G: Return angles
    G->>U: Move Hand
```
