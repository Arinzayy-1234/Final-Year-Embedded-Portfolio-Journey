void setup() {

  Serial.begin(9600);
  
}

int readSerial()
  {
    int i = Serial.parseInt(); // Takes the data in the serial buffer, assigns it to a variable and it is then converted to an integer

    if (i < 1 || (i % 1 != 0) ) //checks if the received value is a valid integer
    {
      
      Serial.println("This isn't a valid integer");
      return 0;
    }
    Serial.println(i);
    Serial.parseInt(); // This alone without being declared, is to clear the buffer to await the next input
    return i;
  }

  void findSide(int x, int y)
  {
  
    float hypotenuse = sqrt((float)x*x + (float)y*y);
  
    Serial.print("Hypotenuse = ");
  
    Serial.println(hypotenuse);
    
  }

void loop() {

  int a;
  int b;
  float result;
    

  Serial.print("Enter a side value: ");
  while(!Serial.available()); // This basically is the blocking part. It frezzes the code until, the user input's data in the user buffer

  a = readSerial();
  if ( a == 0) //  This if statement is kind of redundant cause we already in readSerial gave a condition of i < 1 . Am i correct ?
  {
    return;
  }
 

  Serial.print("Enter the second value: ");

  while (!Serial.available());

  b = readSerial();
  if (b == 0)
  {
    return;
  }
  
  findSide(a,b);
  Serial.println();
}
