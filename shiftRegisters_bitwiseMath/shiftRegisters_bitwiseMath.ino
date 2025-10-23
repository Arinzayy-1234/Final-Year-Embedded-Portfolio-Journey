
const int dataPin = 6;
const int clockPin = 7;
const int latchPin = 8; // Why use const ?

byte ledMap = 0b11111111; // 1. what is the '0b' for ? and in hexadecimal, what will the value be ? 
// it is a datatype unique to arduino and not C/C++. It basically used to store bits instead of integers. 2 It creates a single byte Variable, wheras
// an integer takes up 2 bytes. therefore it is handy for saving space. Explain this.

int delayTime = 3000;

void setup() {
  pinMode(dataPin, OUTPUT); // why is it output when it recieves the data from the arduino ?
  pinMode(clockPin, OUTPUT);
  pinMode(latchPin, OUTPUT);

  Serial.begin(9600);
  shiftWrite(0x00); //This is a function used to control the shift register, but really explain it. What does 0x00 mean ? // We are setting all LEDs to zero for now (0x00)
  Serial.println("Enter a number btw 0 and 255"); // why must the input be btw 0 and 255

}

void loop() {

  if(Serial.available())
  {
    int inputVal = Serial.parseInt();
    
    if (inputVal > 255) 
    {
      Serial.println("Uh oh , Enter a number within 0 and 255");
      return;
    }
    Serial.print("DECIMALS: ");
    Serial.println(inputVal);
    Serial.print("BINARY: ");
    Serial.println(inputVal, BIN); //we are printing the value of our number in Binary. why not use bin(inputVal), like Typecasting?
    Serial.println();

    // AND OPERATION
    Serial.print("AND RESULT: ");
    Serial.println(ledMap & inputVal, BIN); //the AND of 'ledMap & inputVal' is put in binary form
    shiftWrite(ledMap & inputVal);// The result of ledMap and inputVal is parsed into the shift register. One bit at a time.
    delay(delayTime);

    // OR OPERATION
    Serial.print("OR RESULT: ");
    Serial.println(ledMap | inputVal, BIN);
    shiftWrite(ledMap | inputVal);
    delay(delayTime);

    // XOR OPERATION
    Serial.print("XOR RESULT: ");
    Serial.println(ledMap ^ inputVal, BIN);
    shiftWrite(ledMap ^ inputVal);
    delay(delayTime);

    Serial.println("Enter a number btw 0 and 255");

  }

}

void shiftWrite(byte Value) // what does byte Value mean ?explain this entire function. I don't understand it.
{
  digitalWrite(latchPin, LOW); // We pull the latchpin low, to say 'Hey, we are sending some data be ready to update. It is basically like a gate, allow the
  // the data flowing in the data pin to enter the shift register'.
  shiftOut(dataPin, clockPin, MSBFIRST, Value); 
  digitalWrite(latchPin, HIGH); // this like the gate being shut after all the data has been shifted into the register and now all the leds can be updated at once.

  
}
