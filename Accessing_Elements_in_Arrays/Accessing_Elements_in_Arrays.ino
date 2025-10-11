
char arrayOne[6] = {"HELLO"};

// All initialization and code that should run once must go here.
void setup() {

  Serial.begin(9600);
  
  for (char character : arrayOne)
{
  Serial.print("Char: ");
  Serial.println(character);

  Serial.print("ASCII:"); 
  Serial.println((int)character); 
}   


for (int i = 0 ; i < 6; i ++)
{
  Serial.print(arrayOne[i]);
}

}


void loop() {


}
