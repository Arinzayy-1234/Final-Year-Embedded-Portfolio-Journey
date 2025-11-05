// We are using the shift register but not with it's highlevel functions like shiftout() and the rest, we are using the SPI protocol on it. 
// but we didn't define the pins of the shift register like the clock pin, data pin, latch pin and the rest


#include <SPI.h>

int slaveSelect = 2;

int delayTime = 1000;

void setup() {

  pinMode(slaveSelect, OUTPUT);
   pinMode(10, OUTPUT); // Optional but recommended: Set Pin 10 as output for safety, though SPI.begin() usually handles this.
  SPI.begin(); 
  SPI.setBitOrder(LSBFIRST);
}

void loop() {
  for (int i = 0 ; i < 256 ; i ++) //For loop to set data = 0 then increase it by one for every iteration of the loop, when the counter reaches the condition (256) it will be reset
  {
    digitalWrite(slaveSelect, LOW); //Write our Slave select low to enable the SHift register to begin listening for data
    SPI.transfer(i);                 //Transfer the 8-bit value of data to shift register, remembering that the least significant bit goes first
    digitalWrite(slaveSelect, HIGH);  //Once the transfer is complete, set the latch back to high to stop the shift register listening for data
    delay(delayTime);                  //Delay
  }

}
