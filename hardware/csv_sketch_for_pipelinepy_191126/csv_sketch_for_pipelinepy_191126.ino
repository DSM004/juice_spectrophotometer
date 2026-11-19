/*
  spectro_csv.ino
  ---------------------------------------------------------------
  Juice spectrophotometer: CSV output for logger.py / pipeline.py
  Board : Arduino Nano 33 BLE Sense Rev2
  Sensor: AS7343 (I2C 0x39)

  Prints ONE header line, then one CSV line per reading, in exactly the
  column order that analysis/pipeline.py expects.

  LED control: pin D2 drives the white/violet LED through the transistor.
  Set LED_ON below, or pull the LED jumper off for a dark reading.

  Licence: MIT
*/

#include <Adafruit_AS7343.h>

Adafruit_AS7343 as7343;

const int  LED_PIN   = 2;
const bool LED_ON    = true;   // false for a dark run
const int  N_AVERAGE = 10;     // readings averaged per printed line
const int  SETTLE_MS = 300;    // pause after switching the LED on

// Gain and integration: keep these FIXED across a whole measurement series.
// Full scale = (ATIME+1) * (ASTEP+1), here 30 * 600 = 18000 counts.
const as7343_gain_t GAIN  = AS7343_GAIN_256X;
const uint8_t       ATIME = 99;
const uint16_t      ASTEP = 599;

void setup() {
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LED_ON ? HIGH : LOW);   // LED on regardless of USB

  Serial.begin(115200);
  unsigned long t0 = millis();
  while (!Serial && millis() - t0 < 3000) delay(10);   // give up after 3 s

  if (!as7343.begin()) {
    Serial.println("AS7343 not found");
    while (1) delay(10);
  }
  as7343.setGain(GAIN);
  as7343.setATIME(ATIME);
  as7343.setASTEP(ASTEP);

  delay(SETTLE_MS);

  Serial.println("F1,F2,FZ,F3,F4,F5,FY,FXL,F6,F7,F8,NIR,VIS,led,gain,atime,astep");
}

void loop() {
  uint16_t r[18];
  uint32_t sum[13] = {0};
  int good = 0;

  for (int i = 0; i < N_AVERAGE; i++) {
    if (!as7343.readAllChannels(r)) { delay(50); continue; }
    sum[0]  += r[AS7343_CHANNEL_F1];
    sum[1]  += r[AS7343_CHANNEL_F2];
    sum[2]  += r[AS7343_CHANNEL_FZ];
    sum[3]  += r[AS7343_CHANNEL_F3];
    sum[4]  += r[AS7343_CHANNEL_F4];
    sum[5]  += r[AS7343_CHANNEL_F5];
    sum[6]  += r[AS7343_CHANNEL_FY];
    sum[7]  += r[AS7343_CHANNEL_FXL];
    sum[8]  += r[AS7343_CHANNEL_F6];
    sum[9]  += r[AS7343_CHANNEL_F7];
    sum[10] += r[AS7343_CHANNEL_F8];
    sum[11] += r[AS7343_CHANNEL_NIR];
    sum[12] += r[AS7343_CHANNEL_VIS_TL_0];
    good++;
  }

  if (good == 0) { Serial.println("read failed"); delay(500); return; }

  for (int c = 0; c < 13; c++) {
    Serial.print((float)sum[c] / good, 1);
    Serial.print(",");
  }
  Serial.print(LED_ON ? 1 : 0); Serial.print(",");
  Serial.print(0.5 * (1 << GAIN), 1);  Serial.print(",");   // replaces Serial.print(16)
  Serial.print(ATIME);          Serial.print(",");
  Serial.println(ASTEP);

  delay(500);
}