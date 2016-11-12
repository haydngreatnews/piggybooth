/*
  BoothButton
  
  See basic schematic diagram for circuit build
 */

// digital pin 2 has a pushbutton attached to it. Give it a name:
int pushButton = 2;
// Pin 13 has an indicator LED (on board)
int ledIndicator = 13;

// Keep the state of the switch, so we can have single indication
int buttonState = 0;
int lastState = 0;

// the setup routine runs once when you press reset:
void setup() {
  // initialize serial communication at 9600 bits per second:
  Serial.begin(9600);
  // make the pushbutton's pin an input:
  pinMode(pushButton, INPUT);
  pinMode(ledIndicator, OUTPUT);
  Serial.println('r');
}

// the loop routine runs over and over again forever:
void loop() {
  // read the input pin:
  lastState = buttonState;
  buttonState = digitalRead(pushButton);
  digitalWrite(ledIndicator, buttonState);
  // Only print something if the button has transitioned
  if (buttonState == HIGH && lastState == LOW){
    Serial.println('d');
  }

  delay(10);        // delay in between reads for stability
}



