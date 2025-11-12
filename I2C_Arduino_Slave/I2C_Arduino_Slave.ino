// Sender Reciever Arduino Demo

#include <Wire.h>

void setup() {
  
  Wire.begin(8); // Why the 8 ?

  Wire.onRequest(requestEvent);
  // *** RECOMMENDED ADDITION FOR DEBUGGING ***
  Serial.begin(9600); 
  Serial.println("Slave 8 is active.");

}

void loop() {

  delay(100); // Why the delay ?

}


void requestEvent()
{
  Wire.write("HelloY"); // This is 6 bytes of data. If you send more than this, you will garbed the text as they are printed on the serial monitor
  // Send exactly 6 characters (bytes) to match the Master's requestFrom(8, 6)
  
  Serial.println("Data requested and sent!"); // *** RECOMMENDED ADDITION FOR DEBUGGING so you can confirm that the requestEvent() is actually running***
  // You can also use: Wire.write("Hello "); 
}






