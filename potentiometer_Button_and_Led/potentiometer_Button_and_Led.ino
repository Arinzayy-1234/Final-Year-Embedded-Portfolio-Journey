
int ledPwmPin = 9;
int potPin = A0;

void setup() {

  pinMode(ledPwmPin,OUTPUT);
  pinMode(potPin,INPUT); //It dooesn't need a pull up resistor cause it is always connected to something. The potentiometer is always providing a stable voltage to the analog pin, so the pin never "floats" and its state is always known.
  Serial.begin(9600);
}

void loop() { 
  int potValue = analogRead(potPin); 
  int pwmValue = potValue/4;
  analogWrite(ledPwmPin, pwmValue);
  Serial.print(potValue);
  Serial.print(" | ");
  Serial.println(pwmValue);
}


