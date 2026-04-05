#include <LedControl.h>
#include <Wire.h>

// ── Hardware ────────────────────────────────────────────
LedControl lc = LedControl(11, 13, 10, 1);   // DIN, CLK, CS, devices

const int BUZZER   = 9;
const int MPU_ADDR = 0x68;

// ── Maze (8 bytes, bit7=col0, bit0=col7; 1=wall, 0=path) ─
const uint8_t MAZE[8] = {
  0b11111111,   // row 0 - top wall
  0b10000001,   // row 1
  0b10111011,   // row 2
  0b10100001,   // row 3
  0b10101111,   // row 4
  0b10001001,   // row 5
  0b11101001,   // row 6
  0b11111111    // row 7 - bottom wall
};

// ── Game state ───────────────────────────────────────────
int  px = 1, py = 1;          // player position (col, row)
int  gx = 6, gy = 6;          // goal position
int  steps = 0;
bool gameOver = false;

unsigned long lastMove = 0;
const unsigned long MOVE_DELAY = 280;
const unsigned long BLINK_RATE = 400;

// ── Helper: is (x,y) a wall? ────────────────────────────
bool isWall(int x, int y) {
  if (x < 0 || x > 7 || y < 0 || y > 7) return true;
  return (MAZE[y] >> (7 - x)) & 1;
}

// ── MPU-6050 init ────────────────────────────────────────
void mpuInit() {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B);   // PWR_MGMT_1
  Wire.write(0x00);   // wake up
  Wire.endTransmission();
}

// ── Read raw accel (x, y axes only) ─────────────────────
void readAccel(int16_t &ax, int16_t &ay) {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B);   // ACCEL_XOUT_H
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDR, 4, true);
  ax = (Wire.read() << 8) | Wire.read();
  ay = (Wire.read() << 8) | Wire.read();
}

// ── Draw frame ───────────────────────────────────────────
void drawFrame() {
  bool showGoal = (millis() / BLINK_RATE) % 2;
  for (int row = 0; row < 8; row++) {
    uint8_t rowData = MAZE[row];
    if (showGoal && row == gy)
      rowData |= (1 << (7 - gx));
    if (row == py)
      rowData |= (1 << (7 - px));
    lc.setRow(0, row, rowData);
  }
}

// ── Win celebration ──────────────────────────────────────
void celebrateWin() {
  // Ascending arpeggio C5-E5-G5-C6
  int melody[]  = {523, 659, 784, 1047};
  int durations[] = {120, 120, 120, 200};
  for (int i = 0; i < 4; i++) {
    tone(BUZZER, melody[i], durations[i]);
    delay(durations[i] + 30);
  }
  noTone(BUZZER);

  // Flash all LEDs 4 times
  for (int f = 0; f < 4; f++) {
    for (int r = 0; r < 8; r++) lc.setRow(0, r, 0xFF);
    delay(200);
    for (int r = 0; r < 8; r++) lc.setRow(0, r, 0x00);
    delay(200);
  }

  // Show step count in binary on bottom row
  lc.setRow(0, 7, (uint8_t)steps);
}

// ── Setup ────────────────────────────────────────────────
void setup() {
  Wire.begin();
  mpuInit();

  lc.shutdown(0, false);
  lc.setIntensity(0, 4);
  lc.clearDisplay(0);

  pinMode(BUZZER, OUTPUT);
}

// ── Main loop ────────────────────────────────────────────
void loop() {
  if (gameOver) {
    // Slow idle flash until reset
    for (int r = 0; r < 8; r++) lc.setRow(0, r, 0xFF);
    delay(800);
    for (int r = 0; r < 8; r++) lc.setRow(0, r, 0x00);
    delay(800);
    return;
  }

  drawFrame();

  if (millis() - lastMove < MOVE_DELAY) return;

  int16_t ax, ay;
  readAccel(ax, ay);

  const int TILT_THRESHOLD = 5000;   // ~18°, tune if needed
  int dx = 0, dy = 0;

  if (abs(ax) > abs(ay)) {
    if      (ax >  TILT_THRESHOLD) dx =  1;
    else if (ax < -TILT_THRESHOLD) dx = -1;
  } else {
    if      (ay >  TILT_THRESHOLD) dy =  1;
    else if (ay < -TILT_THRESHOLD) dy = -1;
  }

  if (dx == 0 && dy == 0) return;

  int nx = px + dx;
  int ny = py + dy;

  if (isWall(nx, ny)) {
    tone(BUZZER, 180, 40);   // low thud
  } else {
    px = nx;
    py = ny;
    steps++;
    tone(BUZZER, 880, 40);   // clean click
    lastMove = millis();

    if (px == gx && py == gy) {
      celebrateWin();
      gameOver = true;
    }
  }
  lastMove = millis();
}