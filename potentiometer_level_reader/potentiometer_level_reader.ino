
int potPin = A0;

int lastPotValue = 0;

void setup() {

  // put your setup code here, to run once:
  Serial.begin(9600);

  pinMode(potPin, INPUT);
  
}

void loop() {
  // put your main code here, to run repeatedly:

  int potValue = analogRead(potPin)/255;

  if (potValue != lastPotValue)
  {
    switch(potValue)
    {
      case 0:
      Serial.println("Too low");
      break;

      case 1:
      Serial.println("A little bit low");
      break;

      case 2:
      Serial.println(" Moderate ");
      break;

      case 3:
      Serial.println(" up Moderate ");
      break;

      case 4:
      Serial.println(" High ");
      break;

      default:
      Serial.println("There is an error !!!!!!");
      break;
    }
  }
  lastPotValue = potValue;


}
