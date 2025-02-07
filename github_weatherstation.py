Code:
First ESP32:
Webserver, I2C, LoRa transmitter:
#include <Wire.h> 
#include "rgb_lcd.h"
#include <OneWire.h>
#include <DallasTemperature.h>
#include <WiFi.h>
#include <SPI.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <LoRa.h>

// LCD Setup
rgb_lcd lcd;
const int colorR = 255;
const int colorG = 0;
const int colorB = 0;

// One-Wire and DS18B20 Setup
#define ONE_WIRE_BUS 4
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

// BME280 Setup
Adafruit_BME280 bme; // I2C

// Wi-Fi Credentials
const char* ssid = "Manya's S23";
const char* password = "63wx4pafuuf86tk";
WiFiServer server(80);

// LoRa Pins
#define ss 5
#define rst 0
#define dio0 2

// Global Variables
unsigned long delayTime;
int counter = 0;

void setup() {
  // Serial Monitor Setup
  Serial.begin(115200); //baud rate

  // LCD Setup
  lcd.begin(16, 2); //position
  lcd.setRGB(colorR, colorG, colorB);

  // DS18B20 Setup
  sensors.begin();

  // BME280 Setup
  if (!bme.begin()) {
    Serial.println("Could not find a valid BME280 sensor, check wiring!");
    while (1);
  }

  // Wi-Fi Setup
  Serial.print("Connecting to Wi-Fi");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) { //if the wifi is not connected
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWi-Fi connected!");
  Serial.println("IP Address: ");
  Serial.println(WiFi.localIP());
  server.begin();

  // LoRa Setup
  LoRa.setPins(ss, rst, dio0);
  while (!LoRa.begin(866E6)) { //setting the freqeuncy
    Serial.println(".");
    delay(500);
  }
  LoRa.setSyncWord(0x5F); //sync word
  Serial.println("LoRa initialized OK");
}

void loop() {
  // Read DS18B20 Temperature
  sensors.requestTemperatures();
  float oneWireTemp = sensors.getTempCByIndex(0);

  // Read BME280 Sensor Data
  float bmeTemp = bme.readTemperature();
  float pressure = bme.readPressure() / 100.0F;
  float humidity = bme.readHumidity();

  // Display on LCD
  lcd.setCursor(0, 0); //position
  lcd.print("1Wire:");
  lcd.print(oneWireTemp); //one wire temperature
  lcd.print("C");
  lcd.setCursor(0, 1); //position in next line
  lcd.print("BME:");
  lcd.print(bmeTemp); //BME280 temperature
  lcd.print("C");
  delay(2000);

  // Server Web Page
  WiFiClient client = server.available();
  if (client) {
    while (client.connected() && !client.available()) {
      delay(1);
    }
    client.readString();
    client.println("HTTP/1.1 200 OK");
    client.println("Content-type:text/html");
    client.println("Connection: close");
    client.println();

    //HTML for webserver

        //page title
        client.println("<!DOCTYPE html>");
        client.println("<html>");
        client.println("<head>");
        client.println("<meta charset=\"UTF-8\">");
        client.println("<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">");
        client.println("<style>body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }</style>");
        client.println("</head>");
        client.println("<body>");
        client.println("<h1>Weather Station</h1>");

        //displaying the temperature
        client.println("<p><strong>One-Wire Temperature:</strong> " + String(oneWireTemp) + " &#8451;</p>"); 
        client.println("<p><strong>BME280 Temperature:</strong> " + String(bmeTemp) + " &#8451;</p>");
        client.println("<p><strong>Pressure:</strong> " + String(pressure) + " hPa</p>");
        client.println("<p><strong>Humidity:</strong> " + String(humidity) + " %</p>");
        client.println("</body>");
        client.println("</html>");
        client.stop();
  }

  // Send Data via LoRa
  LoRa.beginPacket();
  LoRa.print("1Wire Temp: ");
  LoRa.print(oneWireTemp);
  LoRa.print("C, BME Temp: ");
  LoRa.print(bmeTemp);
  LoRa.print("C, Pressure: ");
  LoRa.print(pressure);
  LoRa.print(" hPa, Humidity: ");
  LoRa.print(humidity);
  LoRa.print(" %");
  LoRa.endPacket();
  counter++;

  delay(10000); // Delay between LoRa transmissions
}

Second ESP32:
Bluetooth and lora receiver:
#include <SPI.h>
#include <LoRa.h>
#include "BluetoothSerial.h"

BluetoothSerial SerialBT; 

int state;
int flag = 0;

//define the pins used by the transceiver module
#define ss 5
#define rst 0
#define dio0 2

void setup() {
  Serial.begin(115200); //baud rate
  while (!Serial);

//setup lora traceiver module
LoRa.setPins(ss,rst,dio0);

//replace the lora.begin argument with your location frequency: 866E6
while(!LoRa.begin(866E6)){
  Serial.println(".");
  delay(500);

  
}
 

LoRa.setSyncWord(0x5F); //the sync word assures you dont get lora messages from other transcievers
Serial.println("LoRa initializing OK");

SerialBT.begin("Manyas S23"); //using the device name to connect it with bluetooth
  Serial.println("the device is on, now you can pair with bluetooth");
}
void loop() {
  // try to parse packet
  int packetSize = LoRa.parsePacket(); 
  if (packetSize) {
    // received a packet
    Serial.print("Received packet '");

    // read packet
    while (LoRa.available()) {
      String LoRaData = LoRa.readString();
      Serial.print(LoRaData); //printing the recived data to the serial moniter
      SerialBT.println(LoRaData); //printing the recived data to the bluetooth terminal on your phone
    }

    // print RSSI of packet
    Serial.print("' with RSSI ");
    Serial.println(LoRa.packetRssi());


 }

}
