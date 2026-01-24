// ------------------------------------------------------------
// Awana Timing Gate – Final Combined Version
// ------------------------------------------------------------
// Behavior:
// - On power-up: system is NOT armed, no serial prints
// - When switchPin goes LOW (closed): print "Race Reset" once
// - Only after a reset can a race start
// - When switchPin goes HIGH (open): print "Race Started" once
// - Each lane timer runs independently until beam breaks
// ------------------------------------------------------------

// Pin definitions
const int switchPin = 2;                 // Normally closed switch
const int beamPins[4] = {3, 4, 5, 6};    // Beam sensor inputs
const int ledPins[4]  = {7, 8, 9, 10};   // LEDs showing beam status

unsigned long startTimes[4];
unsigned long elapsedTimes[4];
bool timerRunning[4];
int timerlatch[4];

int racestartlatch = 0;
int timerresetlatch = 0;

bool systemArmed = false;   // Must reset once before racing allowed

void setup() {
  Serial.begin(9600);

  pinMode(switchPin, INPUT); // Normally closed switch

  for (int i = 0; i < 4; i++) {
    pinMode(beamPins[i], INPUT_PULLUP);
    pinMode(ledPins[i], OUTPUT);
    timerRunning[i] = false;
    elapsedTimes[i] = 0;
    timerlatch[i] = 0;
  }
}

void loop() {
  bool switchOpen = (digitalRead(switchPin) == LOW);  
  // LOW = switch open (race position)
  // HIGH = switch closed (reset position)

  // ------------------------------------------------------------
  // RESET STATE (switch closed)
  // ------------------------------------------------------------
  if (!switchOpen) {

    // Print Race Reset exactly once per reset
    if (timerresetlatch == 0) {
      Serial.println("Race Reset");
      timerresetlatch = 1;
    }

    // Arm the system on first reset
    if (!systemArmed) {
      systemArmed = true;
    }

    // Reset race state
    racestartlatch = 0;

    for (int i = 0; i < 4; i++) {
      elapsedTimes[i] = 0;
      timerRunning[i] = false;
      timerlatch[i] = 0;
    }

    // Beam indicator LEDs
    for (int i = 0; i < 4; i++) {
      if (digitalRead(beamPins[i]) == LOW) {
        digitalWrite(ledPins[i], LOW);
      } else {
        digitalWrite(ledPins[i], HIGH);
      }
    }

    return; // Stay in reset until switch opens
  }

  // ------------------------------------------------------------
  // RACE STATE (switch open)
  // ------------------------------------------------------------

  // Do NOT allow race to start unless system has been reset once
  if (!systemArmed) {
    return;
  }

  // Allow next reset to print again
  timerresetlatch = 0;

  // Print Race Started exactly once
  if (racestartlatch == 0) {
    Serial.println("Race Started");
    racestartlatch = 1;
  }

  // Start timers for all lanes that haven't started yet
  for (int i = 0; i < 4; i++) {
    if (!timerRunning[i]) {
      startTimes[i] = millis();
      timerRunning[i] = true;
    }
  }

  // Check beams for finish times
  for (int i = 0; i < 4; i++) {
    if (timerRunning[i] &&
        digitalRead(beamPins[i]) == LOW &&
        timerlatch[i] == 0) {

      elapsedTimes[i] = millis() - startTimes[i];
      timerRunning[i] = false;

      Serial.print("Lane");
      Serial.print(i + 1);
      Serial.print(" Time: ");
      Serial.println(elapsedTimes[i]);

      timerlatch[i] = 1;
      digitalWrite(ledPins[i], LOW);
    }
  }
}