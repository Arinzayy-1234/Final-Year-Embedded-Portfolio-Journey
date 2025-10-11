

int ledArray[] = {2,3,4,5,6,7,8,9};
int delayTime = 150;

void setup() {
  for(int i = 0; i <= 7; i++)
  {
    pinMode(ledArray[i], OUTPUT);
    
  }

}

void loop() {

  // LEDS WILL ALL ON IN PROGRESSION

  for(int i = 0; i < 8; i++)
  { 
    digitalWrite(ledArray[i], HIGH);
    delay(delayTime);
  }

  // LEDS WILL ALL OFF IN PROGRESSION STARTING FROM THE LAST ONE

  for(int i = 7; i >= 0; i--)
  {
    digitalWrite(ledArray[i], LOW);
    delay(delayTime);
  }
}
