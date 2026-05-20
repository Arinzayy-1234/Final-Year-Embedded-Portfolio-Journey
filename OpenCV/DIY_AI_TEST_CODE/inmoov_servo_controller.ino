/*
 * InMoov Servo Controller for Arduino Mega + PCA9685
 * Receives comma-separated angles via Serial and drives 6 servos
 * 
 * Wiring:
 * - Arduino SDA (Pin 20) → PCA9685 SDA
 * - Arduino SCL (Pin 21) → PCA9685 SCL
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

// Servo PWM pulse range - ADJUST FOR YOUR SERVOS
// Most hobby servos: 150-600 at 60Hz = 0-180°
// Test and tune these values!
#define SERVO_MIN_PULSE  150   // Pulse for 0° (or your servo's min)
#define SERVO_MAX_PULSE  600   // Pulse for 180° (or your servo's max)

// Servo channel mapping on PCA9685
// Must match the order Python sends: Thumb,Index,Middle,Ring,Pinky,Wrist
#define CH_THUMB   0
#define CH_INDEX   1
#define CH_MIDDLE  2
#define CH_RING    3
#define CH_PINKY   4
#define CH_WRIST   5

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(PCA9685_ADDR);

// Convert angle (0-180) to PWM pulse width
uint32_t angleToPulse(float angle) {
  // Constrain angle to valid range
  angle = constrain(angle, 0, 180);
  // Linear map: 0°→SERVO_MIN_PULSE, 180°→SERVO_MAX_PULSE
  return map(angle, 0, 180, SERVO_MIN_PULSE, SERVO_MAX_PULSE);
}

void setup() {
  Serial.begin(9600);
  
  // Initialize I2C and PCA9685
  Wire.begin();
  pwm.begin();
  pwm.setPWMFreq(60);  // Analog servos run at ~60 Hz
  
  delay(10);  // Wait for PCA9685 to stabilize
  
  // Optional: Initialize all servos to neutral position
  for (uint8_t ch = 0; ch < 6; ch++) {
    pwm.setPWM(ch, 0, angleToPulse(90));
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
