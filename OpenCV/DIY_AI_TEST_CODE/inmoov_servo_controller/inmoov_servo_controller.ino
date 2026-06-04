/*
 * InMoov Servo Controller for Arduino Uno/Mega + PCA9685
 * Receives comma-separated angles via Serial and drives 6 servos
 * 
 * Wiring (I2C Connections):
 * - Arduino Uno: SDA (Pin A4) / Mega: SDA (Pin 20) → PCA9685 SDA
 * - Arduino Uno: SCL (Pin A5) / Mega: SCL (Pin 21) → PCA9685 SCL
 * - Arduino 5V → PCA9685 VCC (logic power)
 * - PCA9685 V+ (green terminal) → Buck Converter 6V (servo power)
 * - ALL GROUNDS MUST BE CONNECTED TOGETHER
 * 
 * Serial Input Format:
 * "Thumb,Index,Middle,Ring,Pinky,Wrist\n"
 * Example: "20.0,160.0,160.0,155.0,145.0,90.0\n"
 */

#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

// PCA9685 I2C address (default is 0x40)
#define PCA9685_ADDR 0x40

// Calibration and math constants
const float min_pulse_width    = 500.0;
const float max_pulse_width    = 2500.0;
const float min_angle          = 0.0;
const float hardware_max_angle = 320.0; // The chip's raw conversion baseline (full physical rotation)
const float safety_max_angle   = 300.0; // Your physical mechanical cap
const float pwm_frequency      = 300.0; // Fixed refresh rate frequency

// Servo channel mapping on PCA9685
// Must match the order Python sends: Thumb,Index,Middle,Ring,Pinky,Wrist
#define CH_THUMB   0
#define CH_INDEX   1
#define CH_MIDDLE  2
#define CH_RING    3
#define CH_PINKY   4
#define CH_WRIST   5

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(PCA9685_ADDR);

// Convert angle (0 to 300) to PCA9685 step value (0 to 4095)
uint32_t angleToPulse(float angle) {
  // Enforce safety constraints (0 to 300 degrees)
  angle = constrain(angle, min_angle, safety_max_angle);
  
  // Step 1: Calculate Target Pulse Width (in microseconds)
  float pulseWidth = min_pulse_width + ((angle - min_angle) / (hardware_max_angle - min_angle)) * (max_pulse_width - min_pulse_width);

  // Step 2: Calculate Integer Step Value (at 300Hz)
  float rawStepValue = (pulseWidth * pwm_frequency * 4096.0) / 1000000.0;
  
  return (uint32_t)round(rawStepValue);
}

// Initial rest positions corresponding to min angles for fingers and center (150) for wrist
const float REST_POSITIONS[] = {
  175.0,  // CH_THUMB   (channel 0)
  90.0,   // CH_INDEX   (channel 1)
  100.0,  // CH_MIDDLE  (channel 2)
  100.0,  // CH_RING    (channel 3)
  85.0,   // CH_PINKY   (channel 4)
  150.0   // CH_WRIST   (channel 5)
};

void setup() {
  Serial.begin(9600);
  
  // Initialize I2C and PCA9685
  Wire.begin();
  pwm.begin();
  pwm.setPWMFreq(300);  // Digital servos run at 300 Hz
  
  delay(10);  // Wait for PCA9685 to stabilize
  
  // Initialize all servos to their rest position
  for (uint8_t ch = 0; ch < 6; ch++) {
    pwm.setPWM(ch, 0, angleToPulse(REST_POSITIONS[ch]));
  }
  
  Serial.println("✅ InMoov Servo Controller Ready");
}

void loop() {
  // Check for incoming serial data
  if (Serial.available() > 0) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    
    if (line.length() == 0) return;
    
    // Parse comma-separated angles: "20.0,160.0,160.0,155.0,145.0,90.0"
    float angles[6];
    int count = 0;
    int startIndex = 0;
    
    for (int i = 0; i <= line.length() && count < 6; i++) {
      if (i == line.length() || line.charAt(i) == ',') {
        String part = line.substring(startIndex, i);
        angles[count++] = part.toFloat();
        startIndex = i + 1;
      }
    }
    
    // Only update if we received all 6 angles
    if (count == 6) {
      // Map each angle to its servo channel and send PWM signal
      pwm.setPWM(CH_THUMB,  0, angleToPulse(angles[0]));
      pwm.setPWM(CH_INDEX,  0, angleToPulse(angles[1]));
      pwm.setPWM(CH_MIDDLE, 0, angleToPulse(angles[2]));
      pwm.setPWM(CH_RING,   0, angleToPulse(angles[3]));
      pwm.setPWM(CH_PINKY,  0, angleToPulse(angles[4]));
      pwm.setPWM(CH_WRIST,  0, angleToPulse(angles[5]));
      
      // Optional debug output (comment out for production)
      // Serial.print("Servos: ");
      // for (int i=0; i<6; i++) { Serial.print(angles[i]); Serial.print(" "); }
      // Serial.println();
    }
  }
}
