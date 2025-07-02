/*
  
  CyberSci Nationals 2025

  Dmitriy Beryoza (0xd13a@gmail.com)

  Jeopardy competition

  Voting Machine challenge

*/

#include <LiquidCrystal.h>
#include <SoftwareSerial.h>
#include <AESLib.h>

// Define constant strings in program memory to save RAM
#define FLASH_STR(name, val)  const char name[] PROGMEM = val

// Define pins
#define  D2  2
#define  D3  3
#define  D4  4
#define  D5  5 
#define  D6  6
#define  D7  7
#define  D8  8
#define  D9  9
#define D10 10

// AES encryption interface
AESLib aesLib;

// QR reader interface
SoftwareSerial qrReader(D10,D9); // RX, TX

// LCD screen interface
#define LCD_WIDTH  16
#define LCD_HEIGHT  2
LiquidCrystal lcd(D8, D7, D6, D5, D4, D3);

// Button IDs
#define KEY_A      'A'
#define KEY_B      'B'
#define KEY_C      'C'
#define KEY_D      'D'
#define KEY_E      'E'
#define KEY_VOTE   'V'
#define KEY_CANCEL 'X'

// Button info structure
struct Button {
  char id;       // Button ID
  uint8_t pin;   // Hardware pin
  uint8_t state; // Current state
};

// Buttons in the device
Button buttons[] = { 
  { KEY_A,      A5, HIGH },
  { KEY_B,      A4, HIGH },
  { KEY_C,      A3, HIGH },
  { KEY_D,      A2, HIGH },
  { KEY_E,      A1, HIGH },
  { KEY_VOTE,   A0, HIGH },
  { KEY_CANCEL, D2, HIGH }
};

// Number of buttons
#define NUM_BUTTONS sizeof(buttons) / sizeof(buttons[0])

// Candidate structure
struct Candidate {
  char id;    // Candidate ID
  const char* name; // Candidate name
};

// Defined candidates
static const Candidate candidates[] = {
  { KEY_A, "Esteban de Souza" },
  { KEY_B, "Arius Perez" },
  { KEY_C, "Raphael Velasqez" },
  { KEY_D, "Ramon Esperanza" },
  { KEY_E, "Sofia da Silva" }
};

// Number of candidates
#define NUM_CANDIDATES sizeof(candidates) / sizeof(candidates[0])

// Number of buttons to use for hidden admin login sequence
#define ADMIN_KEY_NUM 10

// Voter structure
struct Voter {
  uint32_t id;  // Voter ID
  const char * name;   // Voter name
};

// Voter names (using program memory to save space)
FLASH_STR(VOTER00, "Dalila Gil");
FLASH_STR(VOTER01, "Carmina Tapia");
FLASH_STR(VOTER02, "Cecilio Montero");
FLASH_STR(VOTER03, "Gonzalo Estevez");
FLASH_STR(VOTER04, "Gertrudis Palau");
FLASH_STR(VOTER05, "Fabiana Benavent");
FLASH_STR(VOTER06, "Estela Cadenas");
FLASH_STR(VOTER07, "Jose Frutos");
FLASH_STR(VOTER08, "Zacaria Bermudez");
FLASH_STR(VOTER09, "Jose Gisbert");
FLASH_STR(VOTER10, "Pilar Solera");
FLASH_STR(VOTER11, "Lino Esparza");
FLASH_STR(VOTER12, "Raquel Urrutia");
FLASH_STR(VOTER13, "Luis Paniagua");
FLASH_STR(VOTER14, "Ainoa Navas");
FLASH_STR(VOTER15, "Rogelio Aguilo");
FLASH_STR(VOTER16, "Diego Valencia");
FLASH_STR(VOTER17, "Perla Valentin");
FLASH_STR(VOTER18, "Jafet Castrillo");
FLASH_STR(VOTER19, "Delia Guillen");
FLASH_STR(VOTER20, "Andres Teruel");
FLASH_STR(VOTER21, "Cruz Olivares");
FLASH_STR(VOTER22, "Xavier Palacios");
FLASH_STR(VOTER23, "Severo Barros");
FLASH_STR(VOTER24, "Calisto Clemente");
FLASH_STR(VOTER25, "Ainara Marco");
FLASH_STR(VOTER26, "Eliana Almansa");
FLASH_STR(VOTER27, "Luisa Montes");
FLASH_STR(VOTER28, "Azeneth Cisneros");
FLASH_STR(VOTER29, "Elario Ramirez");
FLASH_STR(VOTER30, "Calisto Jauregui");
FLASH_STR(VOTER31, "Clement Cervera");
FLASH_STR(VOTER32, "Eric Valbuena");
FLASH_STR(VOTER33, "Epifanio Maestre");
FLASH_STR(VOTER34, "Paco Porcel");
FLASH_STR(VOTER35, "Maricruz Luis");
FLASH_STR(VOTER36, "Bernardo Roman");
FLASH_STR(VOTER37, "Pilar Fortuny");
FLASH_STR(VOTER38, "Desiderio Boada");
FLASH_STR(VOTER39, "Trinidad Campo");
FLASH_STR(VOTER40, "Aranzazu Romero");
FLASH_STR(VOTER41, "Emilio Alcantara");
FLASH_STR(VOTER42, "Eligio Valentin");
FLASH_STR(VOTER43, "Mireia Manzares");
FLASH_STR(VOTER44, "Amor Barriga");
FLASH_STR(VOTER45, "Roberto Agusti");
FLASH_STR(VOTER46, "Cristo Sebastian");
FLASH_STR(VOTER47, "Nieves Ugarte");
FLASH_STR(VOTER48, "Jose Manjon");
FLASH_STR(VOTER49, "Ana Quintanilla");
FLASH_STR(VOTER50, "Bernard Criado");
FLASH_STR(VOTER51, "Poncio Simo");
FLASH_STR(VOTER52, "Mar Sancho");
FLASH_STR(VOTER53, "Maria Puga");
FLASH_STR(VOTER54, "Graciano Cano");
FLASH_STR(VOTER55, "Luna Vizcaino");
FLASH_STR(VOTER56, "Galo Vila");
FLASH_STR(VOTER57, "Pastor Sanmiguel");
FLASH_STR(VOTER58, "Zaida Berenguer");
FLASH_STR(VOTER59, "Alfonso Elorza");
FLASH_STR(VOTER60, "Violeta Longa");
FLASH_STR(VOTER61, "Nando Dominguez");
FLASH_STR(VOTER62, "Ariel Caparros");
FLASH_STR(VOTER63, "Teresita Rubio");
FLASH_STR(VOTER64, "Modesto Portillo");
FLASH_STR(VOTER65, "Rafa Ojeda");
FLASH_STR(VOTER66, "Eloy Catalan");
FLASH_STR(VOTER67, "Lilia Naranjo");
FLASH_STR(VOTER68, "Adelardo Villar");
FLASH_STR(VOTER69, "Chita Bermejo");
FLASH_STR(VOTER70, "Yesica Perez");
FLASH_STR(VOTER71, "Paz Cobo");
FLASH_STR(VOTER72, "Anacleto Quiroga");
FLASH_STR(VOTER73, "Jaime Pedrero");
FLASH_STR(VOTER74, "Salvador Luna");
FLASH_STR(VOTER75, "Maria Torrecilla");
FLASH_STR(VOTER76, "Roberto Acuna");
FLASH_STR(VOTER77, "Maria Armengol");
FLASH_STR(VOTER78, "Herbert Robledo");
FLASH_STR(VOTER79, "Jose Orozco");
FLASH_STR(VOTER80, "Godofredo Marin");
FLASH_STR(VOTER81, "Lourdes Mosquera");
FLASH_STR(VOTER82, "Rosalva Villa");
FLASH_STR(VOTER83, "Humberto Pedro");
FLASH_STR(VOTER84, "Lupe Urena");
FLASH_STR(VOTER85, "Rodrigo Vazquez");
FLASH_STR(VOTER86, "Diego Ropero");
FLASH_STR(VOTER87, "Emigdio Nunez");
FLASH_STR(VOTER88, "Lorena Olive");
FLASH_STR(VOTER89, "Leonor Llopis");
FLASH_STR(VOTER90, "Carla Madrigal");
FLASH_STR(VOTER91, "Rodolfo Anglada");
FLASH_STR(VOTER92, "Fidel Zamora");
FLASH_STR(VOTER93, "Azucena Mari");
FLASH_STR(VOTER94, "Onofre Prieto");
FLASH_STR(VOTER95, "Griselda Palma");
FLASH_STR(VOTER96, "Marc Gutierrez");
FLASH_STR(VOTER97, "Herbert Calderon");
FLASH_STR(VOTER98, "Chucho Rosales");
FLASH_STR(VOTER99, "Baltasar Rubio");

// List of voters with IDs
static const PROGMEM Voter voters[] = {
  {0x240DAEBB, VOTER00},
  {0x2275F831, VOTER01},
  {0x084E0D07, VOTER02},
  {0x2AE5214E, VOTER03},
  {0x31B55D45, VOTER04},
  {0x0F427015, VOTER05},
  {0x132D3626, VOTER06},
  {0x369E53C0, VOTER07},
  {0x3AAF4238, VOTER08},
  {0x1BC843A8, VOTER09},
  {0x3462F612, VOTER10},
  {0x05500B9E, VOTER11},
  {0x00352F96, VOTER12},
  {0x097A3645, VOTER13},
  {0x1BBE5FC3, VOTER14},
  {0x11A64CE2, VOTER15},
  {0x25DB05D9, VOTER16},
  {0x39FE4BDB, VOTER17},
  {0x296875F9, VOTER18},
  {0x25D7C181, VOTER19},
  {0x275A35DA, VOTER20},
  {0x0A40A9C5, VOTER21},
  {0x18EEDAC1, VOTER22}, // test user
  {0x3224C16B, VOTER23},
  {0x08F93DE3, VOTER24},
  {0x0A74B3C3, VOTER25},
  {0x31AA51A2, VOTER26},
  {0x16665A8E, VOTER27},
  {0x2D754DE7, VOTER28},
  {0x1D299FE5, VOTER29},
  {0x2A971326, VOTER30},
  {0x30B05CDB, VOTER31},
  {0x1685A432, VOTER32},
  {0x02FDD86B, VOTER33},
  {0x10436567, VOTER34},
  {0x1DF1F026, VOTER35},
  {0x0003D222, VOTER36},
  {0x2FE4A5FD, VOTER37},
  {0x04A1B619, VOTER38},
  {0x016A20E7, VOTER39},
  {0x3665AE40, VOTER40},
  {0x326321B4, VOTER41},
  {0x37A00F77, VOTER42},
  {0x32BFC903, VOTER43},
  {0x1832C45A, VOTER44},
  {0x166D2F30, VOTER45},
  {0x0DB9D3B9, VOTER46},
  {0x1052A8EE, VOTER47},
  {0x24C01CB8, VOTER48},
  {0x36322315, VOTER49},
  {0x378B1EDA, VOTER50},
  {0x1FF5E3A8, VOTER51},
  {0x37AFB4D5, VOTER52},
  {0x38B551C3, VOTER53},
  {0x30E330AD, VOTER54},
  {0x26A008FE, VOTER55}, // admin user
  {0x1D0B4681, VOTER56},
  {0x30C95631, VOTER57},
  {0x039A8F7D, VOTER58},
  {0x19FF2341, VOTER59},
  {0x305F4BD6, VOTER60},
  {0x38AB738E, VOTER61},
  {0x25130E28, VOTER62},
  {0x3355EE0C, VOTER63},
  {0x304736A1, VOTER64},
  {0x0F5B1D29, VOTER65},
  {0x1CF8C1FB, VOTER66},
  {0x0DC2264A, VOTER67},
  {0x2870924A, VOTER68},
  {0x1ED9DE6C, VOTER69},
  {0x1864DAC6, VOTER70},
  {0x2C3FE661, VOTER71},
  {0x1E84F486, VOTER72},
  {0x2D35F788, VOTER73},
  {0x230255FD, VOTER74},
  {0x2875A808, VOTER75},
  {0x1F11A5FC, VOTER76},
  {0x14112FAC, VOTER77},
  {0x18042B3B, VOTER78},
  {0x26843509, VOTER79},
  {0x1653A051, VOTER80},
  {0x28212427, VOTER81},
  {0x0003A16B, VOTER82},
  {0x2A750766, VOTER83},
  {0x3422AE77, VOTER84},
  {0x1057EBBC, VOTER85},
  {0x21638104, VOTER86},
  {0x230C94A5, VOTER87},
  {0x0E1723D4, VOTER88},
  {0x1AD55C4C, VOTER89},
  {0x2625B03B, VOTER90},
  {0x2AB559A5, VOTER91},
  {0x31EA6C0E, VOTER92},
  {0x1599864B, VOTER93},
  {0x2FBED9CA, VOTER94},
  {0x2B807D1D, VOTER95},
  {0x1B2D80F8, VOTER96},
  {0x1C7E3B16, VOTER97},
  {0x05827913, VOTER98},
  {0x2B82B772, VOTER99}
};

// Number of known voters
#define NUM_VOTERS sizeof(voters) / sizeof(voters[0])

// Vote structure
struct Vote {
  uint32_t id;    // Voter ID
  char candidate; // Candidate ID
};

// Maximum number of votes the machine can hold
#define MAX_VOTES 50

// Vote storage
Vote votes[MAX_VOTES];

// Encrypted vote storage
uint8_t encrypted_votes[sizeof(votes)+16];

// Current number of votes
uint8_t numVotes = 0;

// Length of buffer to hold button presses
#define KEY_BUFFER_LEN 20

// Button key presses
char keyBuffer[KEY_BUFFER_LEN];

// Number of buttons pressed
uint8_t keysInBuffer = 0;

// Was Vote button pressed
bool votePressed = false;   

// Was Cancel button pressed
bool cancelPressed = false;

// Is user logged in
bool loggedIn = false;

// Is current user an admin
bool adminUser = false;

// Index of the current voter
int8_t voterIdx = -1;

// Invalid voter ID
#define INVALID 0xFFFFFFFF

// Current voter ID
uint32_t voterID = INVALID;

// QR code buffer size
#define QR_BUF_SIZE 20

// QR code character buffer
char qrBuffer[QR_BUF_SIZE];

// Current number of characters in the buffer
uint8_t qrLen = 0;

// Device version
const char VERSION[] = "v12.075-20250420";

// Read QR code in the buffer
void readQRCode() {
  // Check if there is Incoming Data in the Serial Buffer.
  if (qrReader.available()) 
  {    
    qrLen = 0;

    while (qrReader.available()) 
    {
      char input = qrReader.read();

      // Only store a limited number of printable characters, drain everything else
      if  ((input >= ' ') && (input <= '~') && (qrLen < QR_BUF_SIZE)) {
        qrBuffer[qrLen] = input;
        qrLen++;
      }
      // A small delay
      delay(5);
    }

    // Output code
    Serial.print(F("Read QR code: "));
    for (uint8_t i = 0; i < qrLen; i++) {
      Serial.print(qrBuffer[i]);
    }
    Serial.println();
  }
}

// Convert hexadecimal code to a number
uint32_t convertQRCode() {
  // Take exactly 8 characters
  if (qrLen != 8) {
    qrLen = 0;
    return INVALID;
  }

  uint32_t val = 0;

  for (uint8_t i = 0; i < 8; i++) {
    char c = qrBuffer[i];
    uint8_t digit;
    
    if (c >= '0' && c <= '9') {
      digit = c - '0';
    } else if (c >= 'A' && c <= 'F') {
      digit = 10 + (c - 'A');
    } else if (c >= 'a' && c <= 'f') {
      digit = 10 + (c - 'a');
    } else {
      // Clear the buffer
      qrLen = 0;
      return INVALID;
    }
    
    val = (val << 4) | digit;
  }
  
  // Clear the buffer
  qrLen = 0;

  return val;
}

// Retrieve voter ID
uint32_t getVoterID(uint8_t idx) {
  return pgm_read_dword_near(&(voters[idx].id));
}

// Retrieve pointer to the voter name
const __FlashStringHelper * getVoterName(uint8_t idx) {
  return pgm_read_ptr_near(&(voters[idx].name));
}

// Process user login
void processLogin() {
  uint32_t code = convertQRCode();

  if (code == INVALID) {
    return;
  }

  uint32_t id;
  voterIdx = -1;
  // If the ID was a valid hex number, find the user associated with it
  for (uint8_t i = 0; i < NUM_VOTERS; i++) {

    id = getVoterID(i);
    if (id == code) {
      voterIdx = i;
      voterID = id;
      Serial.print(F("Found voter "));
      Serial.println((const __FlashStringHelper *)pgm_read_ptr_near(&(voters[voterIdx].name)));
    
      break;
    }
  }

  if (voterIdx == -1) {
    return;
  }

  // VULNERABILITY: checking for a voter ID to be 26A008FE ("Luna Vizcaino") - an admin. 
  // Use ID of the last user on the list as a seed
  uint32_t orig_val = getVoterID(NUM_VOTERS-1);
  uint32_t admin_id = (orig_val >> 24) ^ 0xd5;
  admin_id |= (((orig_val >> 16) & 0xff) ^ 0x8a) << 8;
  admin_id |= (((orig_val >> 8) & 0xff) ^ 0x17) << 16;
  admin_id |= ((orig_val & 0xff) ^ 0x54) << 24;

  if (id == admin_id) {
    adminUser = true;
  } else {
    adminUser = false;
  }

  clearKeyBuffer();

  loggedIn = true;
}

// Check if Vote button was pressed
bool isVotePressed() {
  if (votePressed) {
    votePressed = false;
    return true;
  }
  return false;
}

// Check if Cancel button was pressed
bool isCancelPressed() {
  if (cancelPressed) {
    cancelPressed = false;
    return true;
  }
  return false;
}

// Process button presses
void processButtons() {
  uint8_t state;
  for (uint8_t i = 0; i < NUM_BUTTONS; i++) {
    state = digitalRead(buttons[i].pin);

    // if button was pressed and was released
    if ((state == HIGH) && (buttons[i].state == LOW)) {
      if (buttons[i].id == KEY_VOTE) {
        votePressed = true;
        Serial.print(F("Vote"));
      } else if (buttons[i].id == KEY_CANCEL) {
        cancelPressed = true;
        Serial.print(F("Cancel"));
      } else {
        storeKey(buttons[i].id);
        Serial.print(buttons[i].id);
      }
      Serial.println(F(" pressed"));
    }

    buttons[i].state = state;
  }
}

// Store key in buffer
void storeKey(char key) {
  if (keysInBuffer < KEY_BUFFER_LEN) {
    keyBuffer[keysInBuffer] = key;
    keysInBuffer++;
  }
}

// CLear key buffer
void clearKeyBuffer() {
  keysInBuffer = 0;
}

// Check for secret key sequence that will switch to admin mode
bool checkAdmin() {
  if (keysInBuffer != ADMIN_KEY_NUM) {
    return false;
  }

  // VULNERABILITY: the following key sequence gives admin access - CEDEACCEDA
  if ((keyBuffer[4] == keyBuffer[9]) &&
      (keyBuffer[5] - 1 == keyBuffer[6] - 1) &&
      (keyBuffer[1] == keyBuffer[3]) &&
      (keyBuffer[0] + 2 == keyBuffer[5] + 2) &&
      (keyBuffer[3] * 5 == (keyBuffer[7] * 10) - 345) &&
      (keyBuffer[2] == keyBuffer[8]) &&
      (keyBuffer[0] + 1 == keyBuffer[1] - 1) &&
      (keyBuffer[2] + 1 == keyBuffer[4] + 4) &&
      (keyBuffer[3] - 3 == keyBuffer[4] + 1)) {
    return true;
  }

  return false;
}

// Complete LCD display
void finishDisplay(uint8_t len, bool delayAfter = false) {

  // Write spaces after
  if (len < LCD_WIDTH) {
    uint8_t remainder = LCD_WIDTH - len;
      while(remainder > 0) {
        lcd.print(' ');
        remainder--;
      }
  }

  // Delay if you want to delay displaying the next message
  if (delayAfter) {
      delay(3000);
  }
}

// Display string on the LCD display (RAM string)
void displayLine(uint8_t line, const char* text, bool delayAfter = false) {
  lcd.setCursor(0, line);

  lcd.print(text);

  finishDisplay(strlen(text), delayAfter);
}

// Display string on the LCD display (Flash string)
void displayLine(uint8_t line, const __FlashStringHelper* text, bool delayAfter = false) {
  lcd.setCursor(0, line);

  lcd.print(text);

  finishDisplay(strlen_P((const char *)text), delayAfter);
}


// Find candidate name
const char* getCandidateName(char candidate) {
  for (uint8_t i = 0; i < NUM_CANDIDATES; i++) {
    if (candidates[i].id == candidate) {
      return candidates[i].name;
    }  
  }
  return NULL;
}

// Add a vote to the list
void addVote(uint32_t voterId, char candidate) {
  if (numVotes >= MAX_VOTES) {
    return;
  }

  votes[numVotes].id = voterId;
  votes[numVotes].candidate = candidate;
  numVotes++;
}

// Fake the maximum number of votes
void fakeVotes(char candidate) {
  Serial.print(F("Setting all votes for candidate "));
  Serial.println(getCandidateName(candidate));

  numVotes = 0;
  uint32_t id;
  for (uint8_t i = 0; i < MAX_VOTES; i++) {
    id = getVoterID(i);
    addVote(id, candidate);
  }
}

// Simulate submitting results to the electoral commission server
void submitResults() {
  Serial.println(F("Encoding votes..."));

  // VULNERABILITY: encrypted with an embedded key
  if (numVotes > 0) {
    uint8_t aes_key[16];
    uint8_t iv[] = { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 };

    // Build an encryption key based on a constant string
    for (int part = 0; part < 4; part++) {
      uint32_t val = *(uint32_t*)(&(VERSION[part*4]));
      for (int i = 0; i < 0xdb; i++) {
          val = (val + 0xdbdbdbdb) & 0xffffffff;
          val = ((val>>1) | (val<<(31))) & 0xffffffff;
          val ^= 0xdbdbdbdb;
      }
      *((uint32_t*)&(aes_key[part*4])) = val;
    }

    aesLib.set_paddingmode((paddingMode)0);

    int len = aesLib.encrypt((uint8_t*)votes, numVotes*sizeof(votes[0]), (uint8_t*)encrypted_votes, aes_key, sizeof(aes_key), iv);

    // Output encrypted data
    for(int i = 0; i < len; i++) {
      if (i % 16 == 0) {
        Serial.println(); 
      }
      Serial.print(' '); 
      Serial.print(encrypted_votes[i], HEX); 
    }    

    numVotes = 0;
  }

  Serial.println(F("\nSent votes to electoral commission."));
}

void setup() {

  // set up the LCD's number of columns and rows:
  lcd.begin(LCD_WIDTH, LCD_HEIGHT);

  Serial.begin(9600);
  qrReader.begin(115200);

  // Initialize the pushbutton pin as an input
  for (uint8_t i = 0; i < NUM_BUTTONS; i++) {
    pinMode(buttons[i].pin, INPUT_PULLUP);
  }

  // Display initial device banner
  displayLine(0, F("SuperVotante (R)"));
  displayLine(1, VERSION, true);
}

void loop() {

  // Process butoon state
  processButtons();

  // Process QR code, if used
  readQRCode();

  // If not logged in, process the login
  if (!loggedIn) {
      displayLine(0, F(" Welcome voter!"));
      displayLine(1, F("<Scan voter card"));

      processLogin();
  }

  // If logged in...
  if (loggedIn) {

    // If admin...
    if (adminUser) {
      displayLine(0, F(" Welcome admin!"));
      displayLine(1, F("V-send;Keys-test"));

      // Exit
      if (isCancelPressed()) {
        clearKeyBuffer();
        loggedIn = false;
        displayLine(1, "Exiting...", true);        
      } else if (isVotePressed()) {

        // Submit votes to central server
        submitResults();
        
        displayLine(1, F("Sending votes..."), true);
      } else if (keysInBuffer > 0) {

        // Simulate votes
        fakeVotes(keyBuffer[0]);

        displayLine(1, F("Setting 50 votes"), true);
        clearKeyBuffer();
      }
    } else {
      // Regular user logged in

      // Display their name
      displayLine(0, getVoterName(voterIdx));
      displayLine(1, "");

      // Clear key buffer or exit
      if (isCancelPressed()) {
        if (keysInBuffer > 0) {
          clearKeyBuffer();
        } else {
          loggedIn = false;
          displayLine(1, "Exiting...", true);
        }
      } else if (isVotePressed()) {

        // Handle Vote button pressed
        if (keysInBuffer > 0) {

          // Check if secret sequence was pressed to switch to admin mode
          if (checkAdmin()) {
            clearKeyBuffer();
            // We will stay logged in but change to admin
            adminUser = true;
          } else {

            // Vote for the last selected candidate
            addVote(voterID, keyBuffer[keysInBuffer-1]);
            clearKeyBuffer();

            loggedIn = false;
            displayLine(1, F("*Vote recorded!*"), true);
          }
        }
      } else if (keysInBuffer > 0) {
        // Display selected candidate
        displayLine(1, getCandidateName(keyBuffer[keysInBuffer-1]));
      }
    }
  }

  delay(100);
}