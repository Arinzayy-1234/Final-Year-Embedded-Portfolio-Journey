# InMoov Portfolio Documentation & Presentation

This folder contains the diagrams and interactive materials for your Chapter 3 and presentation.

## 📊 System Block Diagrams

### 1. Overall System Architecture
The "brain" of the project, showing how data flows from the camera and voice to the servos.

![System Architecture](https://mermaid.ink/img/pako:eNptkU1LAzEQhv-KmEPBvXjzB-zBkxZBehB6EZpM2mlscpuEJCvL_nebZre6ZWFm5nnfyWSGEuO8E8aY_f2XpC4XzltYm6o6OunW1EUn3Yq6-N6Uha09f-F6K7WvG-fM_XUf-qZ9b-6uT97vR76pT-W375fS-2PnzD9476839v4onDl6Zz76pnY6OmdO-6Y_OnW_WTo798589037Y6f-DqfXNn_P1qM08e7n-1U-fS8-6F-bT-H63W5pY_3_x75X88_v9Y3-1Pq6_vO92mZpY0f9z_8VvQv_6M_v9W2WJv_u7726P4mB59_6X0G_?type=png)

### 2. Processing Pipeline (The Assembly Line)
The step-by-step math from raw image to smooth movement.

![Pipeline](https://mermaid.ink/img/pako:eNptkdFLAzEQhv-KmEPBvXjzB-zBkxZBehB6EZpM2mlscpuEJCvL_nebZre6ZWFm5nnfyWSGEuO8E8aY_f2XpC4XzltYm6o6OunW1EUn3Yq6-N6Uha09f-F6K7WvG-fM_XUf-qZ9b-6uT97vR76pT-W375fS-2PnzD9476839v4onDl6Zz76pnY6OmdO-6Y_OnW_WTo798589037Y6f-DqfXNn_P1qM08e7n-1U-fS8-6F-bT-H63W5pY_3_x75X88_v9Y3-1Pq6_vO92mZpY0f9z_8VvQv_6M_v9W2WJv_u7726P4mB59_6X0G_?type=png)

## 🌐 Interactive Presentation Tools

### Normalization Explorer
Use `presentation_tool.html` to demonstrate the logic of 0.0 (closed) to 1.0 (open) scaling during your defense.

## 📂 Project Structure
- `gesture_module.py`: Main Brain.
- `python_virtual_hand.py`: The Simulator.
- `voice_module.py`: The Ear.
- `arduino_to_servo_driver.py`: The Bridge.
- `gestures.json`: The "Keeper of Words".
