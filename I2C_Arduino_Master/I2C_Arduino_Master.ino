// Master Reader Arduino Demo

#include <Wire.h>

void setup() {

  Wire.begin(); // It sets up and initializes the hardware pins (SDA/SCL) (usually Analog Pins A4 (SDA) and A5 (SCL) on the Uno.) automatically ,
//so you don't have to manually assigning and controlling them yourself
  Serial.begin(9600);

}

void loop() {

  Wire.requestFrom(8,6); // It request 6 bytes from the arduino (slave device) with adress 8

  while(Wire.available())  // // While there's somthing in the Master's internal buffer
  {
    char c = Wire.read();// When one byte has been recieved, it is put into a character variable. The loop that follows will read the other five bytes (if the slave sent them).

    Serial.write(c);

    
  }
  Serial.println(); // Add a newline after receiving all data for clean output
  delay (500);



}
