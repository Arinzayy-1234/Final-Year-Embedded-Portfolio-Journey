
int ledPin = 12;
int buttonPin = 2;

int toggleState = 0;
int buttonState = 0;

void setup() {
  // put your setup code here, to run once:

  pinMode(ledPin, OUTPUT);
  pinMode(buttonPin, INPUT_PULLUP);

}

void loop() {
  // put your main code here, to run repeatedly:
  buttonState = digitalRead(buttonPin);
  while(buttonState == 1) // when the button is pressed
  {
    toggleState =! toggleState;
    digitalWrite(ledPin, toggleState);
    delay(50);
    buttonState = digitalRead(buttonPin);
  }

  toggleState =! toggleState;
  digitalWrite(ledPin, toggleState); 
  delay(200);

  // The button will blink at 200miliseconds when the button is not pressed and 50 miliseconds when the button is pressed
}

