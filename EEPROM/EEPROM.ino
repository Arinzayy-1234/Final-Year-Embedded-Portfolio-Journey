
#include <EEPROM.h>

int ledPin = 12;
int buttonPin = 2;

int lastButtonState = 1;
long unsigned int lastPress = 0;
int debounceTime = 20;
int counter = 0;


void setup() {
  // put your setup code here, to run once:


  pinMode(ledPin, OUTPUT);
  pinMode(buttonPin, INPUT_PULLUP);

  Serial.begin(9600);

  counter = EEPROM.read(0); // EEPROM read takes one Argument , which is the address on the EEPROM chip that you want to read. in this case it is 0, which is the very first adress on the EEPROM chip
  // 👆 explain this simply
  EEPROM.write(0,0); // what does this even mean 😭😭. It takes to argumets, it needs an adress and  a value to write to that adress
  // What does this mean -> "Be careful, address are only a byte. They are only 8 bit so be careful not to exceed this as this might lead to problems." also Give an example to help with the explanation

  // what does this mean "This allows for consecutive reset to reset the counter ?"
// Explain this part of the video -> 4:37 to 5:29 of  (https://youtu.be/hH9WalIMaeM?si=twr1_3rCBFEFgUiW)
}

void loop() {
  int buttonState = digitalRead(buttonPin);

  if ((millis() - lastPress) > debounceTime)
  {
    lastPress = millis(); // update lastPress
    if (buttonState == 0 && lastButtonState == 1) // if button was released ( ==1 ) and then pressed ( == 0)
    {
      counter ++;
      EEPROM.write(0,counter); //write counter to adress 0
      digitalWrite(ledPin,HIGH);
      lastButtonState = 0; // Record the new last button state

      //Print results
      Serial.println("Counter: ");
      Serial.println(counter);
    }

    if (buttonState == 1 && lastButtonState == 0) // Is the button was previously pressed ( == 0) and now released (== 1 )
    {
      lastButtonState = 1;
      digitalWrite(ledPin, LOW);
    }
  }


}
