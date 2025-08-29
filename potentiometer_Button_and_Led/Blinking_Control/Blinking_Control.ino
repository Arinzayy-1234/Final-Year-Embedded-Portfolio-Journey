//put your setup code here, to run once:
int ledPin = 9;
int potPin = A0;
void setup(){
  pinMode(ledPin,OUTPUT);
  pinMode(potPin,INPUT);
}

// put your main code here, to run repeatedly:
void loop(){

  int potValue = analogRead(potPin);
  digitalWrite(ledPin,HIGH);
  delay(potValue);

  potValue = analogRead(potPin);
  digitalWrite(ledPin, LOW);
  delay(potValue);

}