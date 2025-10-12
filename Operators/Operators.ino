

void setup() {

  Serial.begin(9600);
  int x = 5;

  x += 1;
  Serial.println(x);
}

void loop() {


  int x = 10;
  int y = 20;

  if(!(x > y)) 
  {
    Serial.println("1");
    delay(1000);
  }

  else
  {
    Serial.println("0");
    delay(1000);
  }
}
