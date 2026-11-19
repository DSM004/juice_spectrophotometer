#include <Arduino_HS300x.h>

void setup() {
  Serial.begin(115200);
  while (!Serial);                      // wait for Serial Monitor to open
  if (!HS300x.begin()) {
    Serial.println("Temperature sensor not found");
    while (1);
  }
  Serial.println("time_ms,temp_C");     // CSV header
}

void loop() {
  Serial.print(millis());
  Serial.print(",");
  Serial.println(HS300x.readTemperature(), 2);
  delay(1000);
}