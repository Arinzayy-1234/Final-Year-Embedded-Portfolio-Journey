
int ledPin = 9;

int rampTime = 2; //  controls the speed of the brightness change for the LED
void setup() {
  // put your setup code here, to run once:
  pinMode(ledPin,OUTPUT);
  Serial.begin(9600);
}

void loop() {
  // put your main code here, to run repeatedly:

  //increase LED brightness to the max
  for ( int i = 0 ; i <= 255 ; i ++)
  {
    analogWrite(ledPin, i);
    delay(rampTime);
    Serial.println(i);
    
  }
  //reduce LED brightness to the minimum
  for (int i = 255; i >= 0; i--)
  {
    analogWrite(ledPin,i);
    delay(rampTime);
    Serial.println(i);
    
  }
}
