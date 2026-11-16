/*
  led_driver_test.ino
  ------------------------------------------------------------
  Project : Low-cost juice spectrophotometer (Principles of Sensing)
  Board   : Arduino Nano 33 BLE Sense Rev2
  Purpose : Prove the LED driver circuit works. Pin D2 switches a
            2N3904 NPN transistor, which switches the LED on/off.
            The on-board orange LED blinks at the same time, so
            you can tell "code running" apart from "circuit working".

  Circuit (low-side switch):
    + rail (3.3 V) -> 220 ohm -> LED anode (long leg)
    LED cathode (short leg) -> 2N3904 collector (C)
    2N3904 emitter (E) -> GND rail
    D2 -> 1 kohm -> 2N3904 base (B)

  Expected: the external LED and the on-board LED blink together,
            0.5 s on, 0.5 s off (1 Hz).
  Licence : MIT
*/

const int LED_DRIVER_PIN = 2;      // D2: goes to the transistor base through 1 kohm
const unsigned long ON_MS  = 500;  // time LED is on (milliseconds)
const unsigned long OFF_MS = 500;  // time LED is off (milliseconds)

void setup() {
  // Set both pins as outputs so the Nano can drive them HIGH (3.3 V) or LOW (0 V).
  pinMode(LED_DRIVER_PIN, OUTPUT);
  pinMode(LED_BUILTIN, OUTPUT);    // on-board orange LED: a quick "is the code running?" check

  // Serial lets us print messages to the Serial Monitor (Tools -> Serial Monitor, 115200 baud).
  Serial.begin(115200);
}

void loop() {
  // --- LED ON ---
  // D2 HIGH -> ~2.6 mA flows into the base -> transistor turns fully on
  // -> current flows through the LED (~5.5 mA with 220 ohm at 3.3 V).
  digitalWrite(LED_DRIVER_PIN, HIGH);
  digitalWrite(LED_BUILTIN, HIGH);
  Serial.println("LED ON");
  delay(ON_MS);

  // --- LED OFF ---
  // D2 LOW -> no base current -> transistor off -> no LED current.
  digitalWrite(LED_DRIVER_PIN, LOW);
  digitalWrite(LED_BUILTIN, LOW);
  Serial.println("LED OFF");
  delay(OFF_MS);
}
