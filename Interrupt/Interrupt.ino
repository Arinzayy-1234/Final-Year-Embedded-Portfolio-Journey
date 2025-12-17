

int ledPin = 13;
int buttonPin = 2;

int toggleState = 0;
int lastButtonState = 1;
long unsigned int lastPress = 0;
volatile int buttonFlag = 0;
int debounceTime = 20;


void setup() {
  // put your setup code here, to run once:

  pinMode(ledPin,OUTPUT);
  pinMode(buttonPin,INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(2), ISR_button, CHANGE);

"""
Monitor Pin 2, and whenever its state changes (from High to Low, or Low to High), immediately stop what you are doing in loop() and run the function 
named ISR_button().
"""
}

void loop() {
  // put your main code here, to run repeatedly:
  if ((millis() - lastPress > debounceTime) && buttonFlag)
  {
    lastPress = millis(); // upddated lastPress
    if (digitalRead(buttonPin) == 0 && lastButtonState == 1)
    {
      toggleState =! toggleState;                 //toggle the LED state
      digitalWrite(ledPin, toggleState);
      lastButtonState = 0;    //record the lastButtonState
    }
    else if(digitalRead(buttonPin) == 1 && lastButtonState == 0)    //button is released
    {
      lastButtonState = 1;    //record the lastButtonState
    }
    buttonFlag = 0;
  }
    
}

void ISR_button()
{
  buttonFlag = 1;
}
